import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import custom_tracks, profile, queue, search, seeds, summary
from .routers.subscriptions import alerts_router, router as subscriptions_router
from .subscription_checker import run_subscription_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start background subscription checker
    task = asyncio.create_task(run_subscription_loop())
    yield
    # Cancel on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Job Search Autopilot",
    version="0.2.0",
    description="Find real jobs from public ATS boards. Now with alerts.",
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
app.include_router(subscriptions_router)
app.include_router(alerts_router)
app.include_router(summary.router)
app.include_router(custom_tracks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
