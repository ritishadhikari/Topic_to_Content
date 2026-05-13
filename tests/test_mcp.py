import pytest
import uuid
from unittest.mock import patch
from datetime import datetime
import asyncio

from mcp_code.mcp_server import (generate_new_course, get_course_summary, list_user_courses,get_lesson_deep_dive ,MCP_IDENTITY)
from backend_code.database import db_state

# Generate New Course Tool
@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.background_pipeline_worker")
async def test_mcp_generate_new_course(mock_pipeline_worker, async_client):
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
    mock_pipeline_worker.assert_called_once_with(
        topic="MCP Testing Protocol",
        username=MCP_IDENTITY,
        duration_months=1.0,
        off_days=["Monday"]
    )

    # Verify that the LLM gets the correct success string back
    assert "Successfully started" in response
    
    # Allows asyncio.create_task to quiety execute and delete our fake MOCK Payload
    # before Pytest shuts the whole system down
    await asyncio.sleep(0)



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
    assert "No course found for the topic NonExistant Course 404" in response
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

    await db_state.db.daily_lessons.insert_one(document=mock_lesson)

    url_topic=test_topic.replace(" ", "_")
    response=await get_course_summary(topic=url_topic)

    assert f"Course: {test_topic}" in response
    assert "Total Lessons Found: 1" in response
    assert "Day 1: Introduction to FastMCP" in response


# List User Courses Tool Tests
@pytest.mark.asyncio
@patch (target="mcp_code.mcp_server.AsyncIOMotorClient")
async def test_mcp_list_user_courses_empty(mock_mongo_client, async_client):
    """
    Tests the dashboard listing tool when a user has zero active courses. Verifies graceful text response instructing the LLM to help plan one
    """
    mock_instance=mock_mongo_client.return_value
    mock_instance.ai_course_generator=db_state.db

    response=await list_user_courses()

    assert "The user has not generated any courses yet" in response

    assert "Offer to help them plan their first course" in response


@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.AsyncIOMotorClient")
async def test_mcp_list_user_courses_success(mock_mongo_client, async_client):
    """
    Tests successfully listing distinct grouped courses and overarching projects
    """
    mock_instance=mock_mongo_client.return_value
    mock_instance.ai_course_generator=db_state.db

    test_topic=f"Dashboard Analytics {uuid.uuid4().hex[:4]}"
    project_string="Real-time Metrics Dashboard"

    # Seed Multiple daily documents for the same course to verify aggregation grouping
    mock_lessons=[
        {
            "course_topic": test_topic,
            "username": MCP_IDENTITY,
            "running_use_case_project": project_string,
            "day_number": 1,
            "daily_topic": "Intro",
            "lesson_content":"Content 1",
            "generated_at": datetime.now()

        },
        {
            "course_topic": test_topic,
            "username": MCP_IDENTITY,
            "running_use_case_project": project_string,
            "day_number": 2,
            "daily_topic": "Advanced",
            "lesson_content":"Content 2",
            "generated_at": datetime.now()

        },
    ]

    await db_state.db.daily_lessons.insert_many(mock_lessons)
    response=await list_user_courses()

    assert "** Active User Curriculum Dashboard: **" in response
    assert f"- **Course Topic**: {test_topic}" in response
    assert "- **Duration**: 2 study days" in response
    assert f"- **Overarching Project** {project_string}" in response

# Get Lesson Deep Dive Tool Tests

@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.AsyncIOMotorClient")
async def test_mcp_get_lesson_deep_dive_not_found(mock_mongo_client, async_client):
    """
    Tests deep-dive extraction tool when given invalid parameters
    """
    mock_instance=mock_mongo_client.return_value
    mock_instance.ai_course_generator=db_state.db

    response=await get_lesson_deep_dive(topic="Missing Topic", day_number=99)

    assert "No Content found for Missing Topic" in response
    assert "Verify the topic name and day number" in response


@pytest.mark.asyncio
@patch(target="mcp_code.mcp_server.AsyncIOMotorClient")
async def test_mcp_get_lesson_deep_dive_success(mock_mongo_client, async_client):
    """
    Tests deep-dive tool retrieving unabridged module text and quizzes 
    """
    mock_instance=mock_mongo_client.return_value
    mock_instance.ai_course_generator=db_state.db

    test_topic=f"Tutor Systems {uuid.uuid4().hex[:4]}"
    lesson_body="Comprehensive architectural overview text..."
    quiz_body="Q1: What is FastMCP\n A1: A Python SDK."

    mock_lesson={
        "course_topic": test_topic,
        "username": MCP_IDENTITY,
        "running_use_case_project": "AI Assistant Backend",
        "day_number": 3,
        "daily_topic": "Contextual Tool Integration",
        "lesson_content": lesson_body,
        "quiz_content": quiz_body,
        "generated_at": datetime.now()
    }

    await db_state.db.daily_lessons.insert_one(mock_lesson)

    # Use underscores to verify server-side normalization logic (.replace("_"," "))
    url_topic=test_topic.replace(" ","_")
    response=await get_lesson_deep_dive(topic=url_topic, day_number=3)

    assert "**Module Content: Day 3 - Contextual Tool Integration**" in response
    assert "**Core Course Project Context**: AI Assistant Backend" in response
    assert lesson_body in response
    assert quiz_body in response
