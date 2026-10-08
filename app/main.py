# app/main.py
from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Industry Research Agent")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}