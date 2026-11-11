from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database.init_db import create_db_and_tables, seed_admin
from app.routers import auth, trains, bookings, users
from app.routers.admin import stations as admin_stations
from app.routers.admin import trains as admin_trains

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚂 {settings.app_name} v{settings.app_version} starting up...")
    create_db_and_tables()
    seed_admin()
    yield
    print(f"🛑 {settings.app_name} shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "RailConnect — Simulated railway reservation backend. "
        "Educational project only. No real railway or payment systems."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(trains.router)
app.include_router(bookings.router)
app.include_router(users.router)
app.include_router(admin_stations.router)
app.include_router(admin_trains.router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"Welcome to {settings.app_name}!",
            "version": settings.app_version, "docs": "/docs", "health": "/api/v1/health"}


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "app": settings.app_name, "version": settings.app_version}
