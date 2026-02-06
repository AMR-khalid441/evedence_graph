# main.py
from fastapi import FastAPI
from routes import base , data
import uvicorn
import os
from pathlib import Path
from helpers.config import get_settings



app = FastAPI()

# Mount router at /base
app.include_router(base.base_router, prefix="/base")
app.include_router(data.data_router)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
