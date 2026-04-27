import pytest
import uuid


# Test for Correct Registration
@pytest.mark.asyncio
async def test_successful_registration(async_client):
    test_username=f"test_user_{uuid.uuid4().hex[:8]}"
    test_password="SuperSecretPassword123!"

    response=await async_client.post(
        "/register",
        json={
            "username":test_username, 
            "password":test_password
            }
        )
    
    assert response.status_code==201
    assert response.json()['msg']=="User created Successfully"


# Test for Failed Registration
@pytest.mark.asyncio
async def test_duplicate_registration_fails(async_client):
    test_username=f"test_user_{uuid.uuid4().hex[:8]}"
    test_password="SuperSecretPassword123!"

    # Register for the first time
    await async_client.post(
        "/register",
        json={"username":test_username,
              "password": test_password}
    )

    # Now intentionally make a duplicate registration
    dupicate_response=await async_client.post(
        "/register",
        json={"username":test_username,
              "password": test_password}
    )

    assert dupicate_response.status_code==400
    assert dupicate_response.json()['detail']=="Username is already Registered"