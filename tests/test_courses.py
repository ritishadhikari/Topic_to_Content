import pytest
import uuid
from backend_code.database import db_state
from datetime import datetime

# Test Unauthorized Access
@pytest.mark.asyncio
async def test_unauthorized_course_generation(async_client):
    """
    Tests that a user without a valid JWT token cannot trigger the pipeline
    """
    payload={
        "topic": "Advanced Fast API",
        "duration_months": 1.5,
        "off_days":["Sunday"]
    }

    # Sending Requests without the authorization header
    response=await async_client.post("/generate-course", json=payload)

    assert response.status_code==401
    assert response.json()['detail']=="Not authenticated"  # Gets failed in the oauth2_schema level itself - the first line of defence


# Test Authorized Access
@pytest.mark.asyncio
async def test_authorized_course_generation(async_client):
    """
    Tests that a valid user can successfully trigger the background pipeline
    """

    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"

    await async_client.post(
        "/register",
        json={
            "username": username,
            "password":password
        })
    login_res=await async_client.post(
        "/authorize",
        data={
            "username":username,
            "password":password
        })
    
    token=login_res.json()["access_token"]

    headers={"Authorization":f"Bearer {token}"}
    payload={
        "topic": "Advanced Fast API",
        "duration_months": 1,
        "off_days":["Sunday"]
    }

    response=await async_client.post("/generate-course", json=payload, headers=headers)

    assert response.status_code==202
    assert "Pipeline started for" in response.json()['msg']
    assert response.json()['requested_by']==username


# Test GET Course - Not Found
@pytest.mark.asyncio
async def test_get_course_not_found(async_client):
    """
    Tests fetching a course that has not been generated yet
    """

    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"

    await async_client.post(
        "/register",
        json={
            "username": username,
            "password":password
        })
    login_res=await async_client.post(
        "/authorize",
        data={
            "username":username,
            "password":password
        })
    
    token=login_res.json()["access_token"]
    headers={'Authorization':f"Bearer {token}"}

    response=await async_client.get("/courses/Ghost_course", headers=headers)

    assert response.status_code==404
    assert response.json()["detail"]=="Course not found or has not started yet"


# Test Get Course - SUCCESS
@pytest.mark.asyncio
async def test_get_course_success(async_client):
    """
    Tests successfully fetching a generated course from MongoDB
    """

    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"

    await async_client.post(
        "/register",
        json={
            "username": username,
            "password":password
        })
    login_res=await async_client.post(
        "/authorize",
        data={
            "username":username,
            "password":password
        })
    
    token=login_res.json()['access_token']

    # Injecting a mock lesson directly into the test database
    test_topic=f"Testing Application {uuid.uuid4().hex[:4]}"
    mock_lesson={
        "course_topic": test_topic,
        "username": username,
        "day_number": 1,
        "daily_topic": "Intro to Containers",
        "lesson_content":"This is a test lesson",
        "quiz_content": "This is a test quiz",
        "generated_at":datetime.now()
    }

    await db_state.db.daily_lessons.replace_one(
        filter={"course_topic": test_topic,"username":username},
        replacement=mock_lesson,
        upsert=True
    )

    url_topic=test_topic.replace(" ","_")
    headers={"Authorization":f"Bearer {token}"}

    response=await async_client.get(f"/courses/{url_topic}", headers=headers)

    assert response.status_code==200
    data=response.json()
    assert data['course_topic']==test_topic
    assert data['total_lessons']==1
    assert len(data['lessons'])==1