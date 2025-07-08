from fastapi import FastAPI
from .api.routes import router
from .db.database import init_db
from .utils.logging import setup_logging

app = FastAPI(title="AI-Powered IDS Backend")

@app.on_event("startup")
async def startup_event():
    setup_logging()
    init_db()

app.include_router(router, prefix="/api")
