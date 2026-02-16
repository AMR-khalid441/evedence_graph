from fastapi import FastAPI, APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import BaseController
from controllers import ProjectController
from controllers import DataController
from controllers import ProcessController, PmcProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes import (
    ProcessRequest,
    PmcProcessRequest,
    BatchPmcProcessRequest,
    IngestPmcRequest,
)
from stores.llm.llm_provider_factory import LLMProviderFactory
from stores.vectordb.vector_db_provider_factory import VectorDBProviderFactory
logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.get("/pmc")
async def list_pmc_doc_ids():
    doc_ids = PmcProcessController().list_doc_ids()
    return {"doc_ids": doc_ids}


@data_router.post("/upload/{project_id}")
async def upload_data(project_id: str, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
        
    
    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    return JSONResponse(
            content={
                "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                "file_id": file_id
            }
        )

@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: ProcessRequest):

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )

    serialized_chunks = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "type": "Document",
        }
        for doc in file_chunks
    ]
    return serialized_chunks


@data_router.post("/process_pmc_article")
async def process_pmc_article_endpoint(process_request: PmcProcessRequest):

    doc_id = process_request.doc_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size

    pmc_process_controller = PmcProcessController()

    file_chunks = pmc_process_controller.process_article(
        doc_id=doc_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILED.value
            }
        )


    serialized_chunks = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "type": "Document",
        }
        for doc in file_chunks
    ]

    return serialized_chunks


@data_router.post("/process_pmc_articles")
async def process_pmc_articles_endpoint(batch_request: BatchPmcProcessRequest):
    doc_ids = batch_request.doc_ids
    chunk_size = batch_request.chunk_size
    overlap_size = batch_request.overlap_size

    pmc_process_controller = PmcProcessController()
    results = []

    for doc_id in doc_ids:
        try:
            file_chunks = pmc_process_controller.process_article(
                doc_id=doc_id,
                chunk_size=chunk_size,
                overlap_size=overlap_size,
            )
            if file_chunks is None or len(file_chunks) == 0:
                results.append({"doc_id": doc_id, "error": "No chunks produced"})
                continue
            serialized = [
                {
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                    "type": "Document",
                }
                for doc in file_chunks
            ]
            results.append({"doc_id": doc_id, "chunks": serialized})
        except FileNotFoundError as e:
            results.append({"doc_id": doc_id, "error": str(e)})
        except Exception as e:
            logger.exception(f"Error processing doc_id={doc_id}")
            results.append({"doc_id": doc_id, "error": str(e)})

    return {"results": results}


@data_router.post("/ingest_pmc_article")
async def ingest_pmc_article_endpoint(
    ingest_request: IngestPmcRequest,
    app_settings: Settings = Depends(get_settings),
):
    doc_id = ingest_request.doc_id
    collection_name = ingest_request.collection_name
    chunk_size = ingest_request.chunk_size
    overlap_size = ingest_request.overlap_size

    try:
        pmc_controller = PmcProcessController()
        chunks = pmc_controller.process_article(
            doc_id=doc_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
        )
    except FileNotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": str(e)},
        )

    if not chunks or len(chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "No chunks produced"},
        )

    llm_factory = LLMProviderFactory(app_settings)
    llm = llm_factory.create(app_settings.LLM_PROVIDER)
    if llm is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"LLM provider not available: {app_settings.LLM_PROVIDER}"},
        )
    llm.set_embedding_model(app_settings.EMBEDDING_MODEL_ID, app_settings.EMBEDDING_SIZE)

    texts = []
    vectors = []
    metadata_list = []
    for i, doc in enumerate(chunks):
        vec = llm.embed_text(doc.page_content)
        if vec is None:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Embedding failed for chunk index {i}"},
            )
        texts.append(doc.page_content)
        vectors.append(vec)
        metadata_list.append(doc.metadata)

    vdb_factory = VectorDBProviderFactory(app_settings)
    try:
        vector_db = vdb_factory.create(app_settings.VECTOR_DB_PROVIDER)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": str(e)},
        )
    if vector_db is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Vector DB provider not available: {app_settings.VECTOR_DB_PROVIDER}"},
        )

    try:
        await vector_db.connect_async()
        exists = await vector_db.is_collection_existed_async(collection_name)
        if not exists:
            await vector_db.create_collection_async(
                collection_name=collection_name,
                embedding_size=app_settings.EMBEDDING_SIZE,
                do_reset=False,
            )
        ok = await vector_db.insert_many_async(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata_list,
        )
        if not ok:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Vector DB insert_many_async failed"},
            )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": str(e)},
        )
    except Exception as e:
        logger.exception("Ingest failed while writing to Qdrant Cloud")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Qdrant ingest failed: {e!s}"},
        )
    finally:
        try:
            await vector_db.disconnect_async()
        except Exception:
            pass

    return {
        "doc_id": doc_id,
        "collection_name": collection_name,
        "chunks_ingested": len(chunks),
    }
