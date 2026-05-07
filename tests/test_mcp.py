import pytest
import uuid
from unittest.mock import patch
from datetime import datetime

from mcp_code.mcp_server import generate_new_course, get_course_summary, MCP_IDENTITY
from backend_code.database import db_state

# Generate New Course Tool
@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.create_task")
async def test_mcp_generate_new_course(mock_create_task, async_client):
    """
    Tests the MCP tool for generating a course
    Mocks the asyncio.create_task to prevent Langgraph from actually running
    """
    response=await generate_new_course(
        topic="MCP Testing Protocol",
        duration_months=1.0,
        off_days=["Monday"]
    )

    # Verifying that the background task was successfully triggered
    mock_create_task.assert_called_once()

    # Verify that the LLM gets the correct success string back
    assert "Successfully started generating the course for MCP Testing Protocol" in response
    assert "check back shortly" in response

# Get Course Summary tool - Not found
@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.AsyncIOMotorClient")
async def test_mcp_get_course_summary_not_found(mock_mongo_client, async_client):
    """
    Tests the summary tool when a course does not exists
    """
    mock_instance=mock_mongo_client.return_value  # creating a mock client
    mock_instance.ai_course_generator=db_state.db  # after creating the fake mock client, we are assigning the db to the mock client which is the db of the actual test client; the database is actually real and points to the test database
    
    response=await get_course_summary(topic="NonExistant Course 404")
    assert "No Course found for the topic NonExistant Course 404" in response
    assert "ask the user if they would want to generate it" in response

# Get Course Tool Success
@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.AsyncIOMotorClient")
async def test_mcp_get_course_summary_success(mock_mongo_client, async_client):
    """
    Tests the summary tool retrieving an actual course from MongoDB.
    """
    
    mock_instance=mock_mongo_client.return_value  # fake mock client
    mock_instance.ai_course_generator=db_state.db  # real test database

    test_topic=f"MCP Integration {uuid.uuid4().hex[:4]}"

    # We must attach the exact identity the MCP server is currently loaded with
    mock_lesson={
        "course_topic":test_topic,
        "username":MCP_IDENTITY,
        "day_number":1,
        "daily_topic": "Introduction to FastMCP",
        "lesson_content":"This is an MCP test lesson",
        "quiz_content":"This is an MCP Test Quiz",
        "generated_at": datetime.now()
    }

    await db_state.db.daily_lessons.insert_one(doc=mock_lesson)

    url_topic=test_topic.replace(" ", "_")
    response=await get_course_summary(topic=url_topic)

    assert f"Course: {test_topic}" in response
    assert "Total Lessons Found: 1" in response
    assert "Day 1: Introduction to FastMCP" in response
