# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import base, data, nlp
import uvicorn
import os
from pathlib import Path
from helpers.config import get_settings


app = FastAPI()

# CORS: allow browser/frontend (Swagger, ReDoc, localhost). Cannot use allow_origins=["*"] with allow_credentials=True.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(base.base_router, prefix="/base")
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
