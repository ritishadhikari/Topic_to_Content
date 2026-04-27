# Remember: Name of the file has to be conftest.py

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from api import app
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from backend_code.database import db_state
import os


load_dotenv()

@pytest_asyncio.fixture  # allows for async_client in the parenthesis, handles background work - starting the server, connecting to the database and cleaning up afterward
async def async_client():
    """
    Spins up an asynchronous test client and explicitly forces the
    MongoDB connection to open since the fake server skips startup events.

    It connects to a dedicated testing database to prevent data pollution
    """
    mongo_uri=os.environ.get("MONGO_URI")
    db_state.client=AsyncIOMotorClient(host=mongo_uri)
    db_state.db=db_state.client.ai_course_generator_test

    async with AsyncClient(
        transport=ASGITransport(app=app),  # this is the web server
        base_url="http://test"  # written in place of http://127.0.0.1:8000/ and is used to pass information through a medium of exchange (ASGITransport) from the web browser (client) to the web server (app) and back
        ) as client:
        yield client  # this is the web browser which passes in the requests to the web server

    db_state.client.close()