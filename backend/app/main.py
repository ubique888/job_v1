from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import profile, queue, search, seeds


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Job Search Autopilot",
    version="0.1.0",
    description="Find real jobs from public ATS boards. No auto-apply.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(seeds.router)
app.include_router(search.router)
app.include_router(queue.router)


@app.get("/health")
def health():
    return {"status": "ok"}
