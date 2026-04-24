import os
import logging
from motor import motor_asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(name="Database")

class DatabaseState:
    client=None
    db=None

db_state=DatabaseState()

@asynccontextmanager
async def lifespan(app:FastAPI):
    mongo_uri=os.environ.get("MONGO_URI")
    if mongo_uri is None:
        logger.warning("Mongo_URI not found in environment variables")
    else:
        try:
            db_state.client=motor_asyncio.AsyncIOMotorClient(host=mongo_uri)
            db_state.db=db_state.client.ai_course_generator
            logger.info("MongoDB connection opened cleanly")
        except Exception as e:
            logger.error(msg=f"Failed to connect to MongoDB: {e}", exc_info=True)
    
    yield  # Server is running
    
    if db_state.client:
        db_state.client.close()
        logger.info("MongoDB connection closed cleanly")


