"""Murder Mystery FastAPI Application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import games, stories, websocket
from app.db.database import init_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    await init_db()
    yield


app = FastAPI(
    title="Murder Mystery API",
    description="AI-powered 剧本杀 game backend",
    version="0.1.0",
    lifespan=lifespan
)

# CORS for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games.router, prefix="/api/games", tags=["games"])
app.include_router(stories.router, prefix="/api/stories", tags=["stories"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/")
async def root():
    return {"message": "Murder Mystery API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
