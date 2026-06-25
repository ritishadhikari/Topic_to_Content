import logging 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend_code.database import  db_state, lifespan
from backend_code.routers import authentication, course_generate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y:%m:%d %H:%M:%S"
    )

app=FastAPI(title="Khudse API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=["*"]
)

@app.get(path="/health",tags=["System Checks"])
async def health_check():
    """
    Verifies API status and Mongo DB conection
    """
    db_status="disconnected"
    if db_state.client is not None:
        try:
            # Send a Lightweight Ping to Mongodb
            await db_state.db.command("ping")
            db_status="connected"
        except Exception:   db_status="error"
    return {
        "api_status":"ok",
        "database": db_status
    }


app.include_router(router=authentication.router)
app.include_router(router=course_generate.router)

Instrumentator().instrument(app=app).expose(app=app)