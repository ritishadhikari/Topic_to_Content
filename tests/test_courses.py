import pytest
import uuid
from backend_code.database import db_state
from datetime import datetime
from unittest.mock import patch, ANY
import msgpack

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
@patch("backend_code.routers.course_generate.run_pipeline")  # Intercepts the heavy work
async def test_authorized_course_generation(mock_run_pipeline, async_client):
    """
    Tests that a valid user can successfully trigger the background pipeline
    """

    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post(
        "/register",
        json={
            "username": username,
            "email":email,
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
    mock_run_pipeline.assert_called_once_with(
        topic="Advanced Fast API",
        username=username,
        duration_months=1.0,
        off_days=["Sunday"],
        start_date=ANY,
        running_use_case_project=None
    )
    # assert "Pipeline started for" in response.json()['msg']
    # assert response.json()['requested_by']==username


# Test GET Course - Not Found
@pytest.mark.asyncio
async def test_get_course_not_found(async_client):
    """
    Tests fetching a course that has not been generated yet
    """

    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post(
        "/register",
        json={
            "username": username,
            "email":email,
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
    email="test@example.com"

    await async_client.post(
        "/register",
        json={
            "username": username,
            "email":email,
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

# Test Get User Courses - Empty State
@pytest.mark.asyncio
async def test_get_user_courses_empty(async_client):
    """
    Tests that a new user with zero generated courses receives a graceful empty list rather than throwing an unexpected 404 error.
    """
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )
    login_res=await async_client.post("/authorize", data={"username":username, "password":password})
    token=login_res.json()['access_token']

    headers={"Authorization":f"Bearer {token}"}
    response=await async_client.get("/my-courses", headers=headers)

    assert response.status_code==200
    data=response.json()
    assert data['total_courses']==0
    assert data['courses']==[]



# Test GET User Courses - Success (Syllabus Pre-Load Integrity)
@pytest.mark.asyncio
async def test_get_user_courses_success(async_client):
    """
    Tests that the aggregation pipeline successfully groups courses, extracts the overarching running project, and populates the pre-loaded syllabus items in sequential order.
    """
   
        
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )
    login_res=await async_client.post("/authorize", data={"username":username, "password":password})
    token=login_res.json()['access_token']

    test_topic=f"Langgraph Framework {uuid.uuid4().hex[:4]}"
    project_desc="Building a Multi-Agent Support System"

    # Seed two separate days for the same course to verify aggregation and chronological sorting

    lesson_day_2={
        "course_topic": test_topic,
        "username": username,
        "running_use_case_project": project_desc,
        "day_number": 2,
        "daily_topic":"Human-in-the-loop validation",
        "lesson_content":"Content Day 2",
        "generated_at":datetime.now()
    }

    lesson_day_1={
        "course_topic": test_topic,
        "username": username,
        "running_use_case_project": project_desc,
        "day_number": 1,
        "daily_topic":"Stategraph and Checkpointers",
        "lesson_content":"Content Day 1",
        "generated_at":datetime.now()
    }

    # Insert out-of-order intentionally to test the pipeline's mandatory pre-sorting stage
    await db_state.db.daily_lessons.insert_many([lesson_day_2, lesson_day_1])

    headers={"Authorization":f"Bearer {token}"}
    response=await async_client.get("/my-courses", headers=headers)

    assert response.status_code==200
    data=response.json()

    assert data['total_courses']==1
    course_item=data["courses"][0]
    assert course_item['course_topic']==test_topic
    
    # Validate syllabus pre-load arrays are perfectly ordered
    assert len(course_item["syllabus"])==2
    assert course_item['running_use_case_project']==project_desc
    assert course_item["syllabus"][0]["day_number"]==1
    assert course_item['syllabus'][0]["daily_topic"]=="Stategraph and Checkpointers"
    assert course_item['syllabus'][1]['day_number']==2

@pytest.mark.asyncio
async def test_get_lesson_deep_dive_not_found(async_client):
    """
    Tests that requesting a specific day that does not exist returns a 404 error.
    """
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )
    login_res=await async_client.post("/authorize", data={"username": username, "password": password})
    token=login_res.json()['access_token']
    headers={'Authorization':f"Bearer {token}"}

    response=await async_client.get("/courses/Ghost_Course/day/99", headers=headers)
    assert response.status_code==404
    assert "not available yet" in response.json()['detail']

@pytest.mark.asyncio
async def test_get_lesson_deep_dive_success(async_client):
    """
    Tests successfully fetching a specific day's deep dive markdown and quiz
    """
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )
    login_res=await async_client.post("/authorize", data={"username": username, "password": password})
    token=login_res.json()['access_token']
    headers={'Authorization':f"Bearer {token}"}

    test_topic=f"Streamlit Dashboard {uuid.uuid4().hex[:4]}"

    # Inject a specific day's module
    mock_lesson={
        "course_topic":test_topic,
        "username":username,
        "running_use_case_project":"Data Viz App",
        "day_number":3,
        "daily_topic":"Session State Management",
        "lesson_content":"Detailed Markdown about st.session_state",
        "quiz_content":"Quiz: What does st.session_state do",
        "generated_at":datetime.now()
    }

    await db_state.db.daily_lessons.insert_one(mock_lesson)

    url_topic=test_topic.replace(" ","_")
    response=await async_client.get(f"/courses/{url_topic}/day/3", headers=headers)

    assert response.status_code==200
    data=response.json()

    assert data['course_topic']==test_topic
    assert data['day_number']==3
    assert data['daily_topic']=="Session State Management"
    assert data['lesson_content']=="Detailed Markdown about st.session_state"

@pytest.mark.asyncio
async def test_get_generation_status_not_started(async_client):
    """
    Tests the polling endpoint when a course has neither checkpoints nor DB records.
    """
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )

    login_res=await async_client.post("/authorize", data={"username":username, "password": password})

    token=login_res.json()['access_token']
    headers={"Authorization":f"Bearer {token}"}

    response=await async_client.get("/courses/Brand_New_Course/status", headers=headers)

    assert response.status_code==200
    
    data=response.json()
    assert data['status']=="NOT_STARTED"
    assert data['current_day']==0
    assert data['is_completed'] is False

@pytest.mark.asyncio
async def test_get_generation_status_in_progress(async_client):
    """
    Tests the polling endpoint by safely mocking LangGraph's binary Pickling state to simulate a workflow currently stuck on Day 2.
    """
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )


    login_res=await async_client.post("/authorize", data={"username":username, "password": password})

    token=login_res.json()['access_token']
    headers={"Authorization":f"Bearer {token}"}

    test_topic_url="Docker_for_Beginners"
    thread_id=f"course_generation_{username}_{test_topic_url}"
    
    # Creating a fake python dictionary mimicking Langgraph's internal structure

    fake_state_dict={
        "channel_values":{
            "day_number": 2,
            "total_study_days": 5
        },
        "pending_sends":['schedule_architect_task_id']  # Simulating active graph routing
    }

    raw_binary_payload=msgpack.packb(o=fake_state_dict)

    await db_state.db.checkpoints.insert_one({
        "thread_id": thread_id,
        "checkpoint_id":"1e9f4b8s-0000-1111-2222-123456789101",
        "checkpoint": raw_binary_payload,
        "type":"msgpack"
    })

    response=await async_client.get(f"/courses/{test_topic_url}/status", headers=headers)

    assert response.status_code==200
    data=response.json()

    assert data['status']=="IN_PROGRESS"
    assert data["current_day"]==2
    assert data['total_study_days']==5
    assert data['is_completed'] is False


@pytest.mark.asyncio
async def test_get_generation_status_completed(async_client):
    """
    Tests the polling endpoint when a course has successfully finished generation
    Simulates an empty pending_sends queue and a matching database document count
    """
    username=f"user_{uuid.uuid4().hex[:8]}"
    password="SecurePassword123!"
    email="test@example.com"

    await async_client.post("/register", 
                            json={
                                "username": username, 
                                "email":email,
                                "password":password}
                                )


    login_res=await async_client.post("/authorize", data={"username":username, "password": password})

    token=login_res.json()['access_token']
    headers={"Authorization":f"Bearer {token}"}

    test_topic=f"React Fundamentals {uuid.uuid4().hex[:4]}"
    test_topic_url=test_topic.replace(" ", "_")
    thread_id=f"course_generation_{username}_{test_topic_url}"

    # Mock a COMPLETED Langgraph Checkpoint
    # Notice that "pending_sends" is an empty list, which signals the graph has stopped routing

    fake_state_dict={
        "channel_values":{
            "day_number":2,
            "total_study_days":2
        }, 
        "pending_sends":[]
    }

    raw_binary_payload=msgpack.packb(o=fake_state_dict)

    await db_state.db.checkpoints.insert_one({
        "thread_id": thread_id,
        "checkpoint_id": "final-checkpoint-uuid-000",
        "checkpoint": raw_binary_payload,
        "type": "msgpack"
    })

    # Inject the actual written lessons into the database to match total_study_days
    await db_state.db.daily_lessons.insert_many([
        {"course_topic": test_topic,"username": username, "day_number": 1},
        {"course_topic": test_topic,"username": username, "day_number": 2},
    ])

    response=await async_client.get(f"/courses/{test_topic_url}/status", headers=headers)


    assert response.status_code==200
    data=response.json()

    assert data['status']=="COMPLETED"
    assert data['current_day']==2
    assert data['total_study_days']==2
    assert data['is_completed'] is True