import logging 
from fastapi import FastAPI

from backend_code.database import lifespan
from backend_code.routers import authentication, course_generate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y:%m:%d %H:%M:%S"
    )

app=FastAPI(title="AI Course Generator API", lifespan=lifespan)

app.include_router(router=authentication.router)
app.include_router(router=course_generate.router)