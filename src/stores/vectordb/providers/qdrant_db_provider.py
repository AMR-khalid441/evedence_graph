import logging
import uuid
from typing import List

from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from ..vector_db_interface import VectorDBInterface
from ..vector_db_enums import DistanceMethodEnums


class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path: str, distance_method: str, url: str = None, api_key: str = None):

        self.client = None
        self.async_client = None  # New async client
        self.db_path = db_path
        self.url = url
        self.api_key = api_key
        self.distance_method = None

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = Distance.DOT

        self.logger = logging.getLogger(__name__)

    def connect(self):
        if not self.url or not self.api_key:
            raise ValueError(
                "Qdrant Cloud is required: set QDRANT_CLUSTER_URL and QDRANT_KEY in your environment."
            )
        self.client = QdrantClient(url=self.url, api_key=self.api_key)

    def disconnect(self):
        self.client = None

    async def connect_async(self):
        """Async connection - Qdrant Cloud required. Uses 120s timeout for cloud upserts."""
        if not self.url or not self.api_key:
            raise ValueError(
                "Qdrant Cloud is required: set QDRANT_CLUSTER_URL and QDRANT_KEY in your environment."
            )
        self.async_client = AsyncQdrantClient(
            url=self.url, api_key=self.api_key, timeout=120.0
        )

    async def disconnect_async(self):
        """Async disconnection."""
        if self.async_client:
            await self.async_client.close()
            self.async_client = None

    async def is_collection_existed_async(self, collection_name: str) -> bool:
        """Async collection existence check."""
        if not self.async_client:
            await self.connect_async()
        return await self.async_client.collection_exists(collection_name=collection_name)

    async def create_collection_async(self, collection_name: str, 
                                     embedding_size: int,
                                     do_reset: bool = False):
        """Async collection creation."""
        if not self.async_client:
            await self.connect_async()
        
        if do_reset:
            exists = await self.is_collection_existed_async(collection_name)
            if exists:
                await self.async_client.delete_collection(collection_name=collection_name)
        
        exists = await self.is_collection_existed_async(collection_name)
        if not exists:
            await self.async_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )
            return True
        
        return False

    def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    def list_all_collections(self) -> List:
        return self.client.get_collections()
    
    def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        
    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = self.delete_collection(collection_name=collection_name)
        
        if not self.is_collection_existed(collection_name):
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )

            return True
        
        return False
    
    def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None,
                         record_id: str = None):

        if not self.is_collection_existed(collection_name):
            self.logger.error(f"Can not insert new record to non-existed collection: {collection_name}")
            return False

        point_id = record_id if record_id is not None else str(uuid.uuid4())
        payload = {"text": text, "metadata": metadata}

        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )
        except Exception as e:
            self.logger.error(f"Error while inserting record: {e}")
            return False

        return True
    
    def insert_many(self, collection_name: str, texts: list,
                          vectors: list, metadata: list = None,
                          record_ids: list = None, batch_size: int = 50):

        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = [None] * len(texts)

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_ids = record_ids[i:batch_end]

            points = [
                PointStruct(
                    id=batch_ids[x] if batch_ids[x] is not None else str(uuid.uuid4()),
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x],
                        "metadata": batch_metadata[x],
                    },
                )
                for x in range(len(batch_texts))
            ]

            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=points,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True

    async def insert_many_async(self, collection_name: str, texts: list,
                                vectors: list, metadata: list = None,
                                record_ids: list = None, batch_size: int = 20):
        """Async batch insert using upsert from official Qdrant docs - prevents duplicates.
        Raises on failure so the API can return 5xx instead of 200.
        """
        if not self.async_client:
            await self.connect_async()
        
        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = [None] * len(texts)
        
        # Batch upsert so cloud limits / timeouts are less likely
        for i in range(0, len(texts), batch_size):
            batch_end = min(i + batch_size, len(texts))
            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_ids = record_ids[i:batch_end]
            points = [
                PointStruct(
                    id=(batch_ids[j] if batch_ids[j] is not None else str(uuid.uuid4())),
                    vector=batch_vectors[j],
                    payload={"text": batch_texts[j], "metadata": batch_metadata[j]},
                )
                for j in range(len(batch_texts))
            ]
            # Do not swallow exceptions - let them propagate so API returns 5xx
            await self.async_client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )
        return True
        
    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        """
        Search for nearest vectors using query_points (official Qdrant API).
        Returns list of ScoredPoint objects with id, score, and payload.
        """
        resp = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return resp.points
