from fastapi import FastAPI

from app.database.connection import Base, engine
from app.models.song import Song
from app.routes.songs import router as songs_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MusicAI",
    description="Sistema inteligente de biblioteca musical",
    version="0.1.0"
)


app.include_router(songs_router)


@app.get("/")
def root():
    return {
        "app": "MusicAI",
        "status": "online",
        "version": "0.1.0"
    }