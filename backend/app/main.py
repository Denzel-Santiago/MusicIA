from fastapi import FastAPI

app = FastAPI(
    title="MusicAI",
    description="Sistema inteligente de biblioteca musical",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "app": "MusicAI",
        "status": "online",
        "version": "0.1.0"
    }