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

# Test for correct Authorization
@pytest.mark.asyncio
async def test_successful_authorization(async_client):
    test_username=f"test_user_{uuid.uuid4().hex[:8]}"
    test_password="SuperSecretPassword123!"
    
    # Register the user so that we have valid credentials to test 
    await async_client.post(
        "/register",
        json={
                "username":test_username,
                "password":test_password
        }
    )

    login_response=await async_client.post(
        "/authorize",
        data={
                "username":test_username,
                "password":test_password
            }
        )
    
    assert login_response.status_code==200

    token_data=login_response.json()
    assert 'access_token' in token_data
    assert token_data['token_type']=="bearer"


# Test for incorrect Authorization
@pytest.mark.asyncio
async def test_incorrect_authorization(async_client):
    # Generating credentials that have never been registered
    fake_username=f"ghost_{uuid.uuid4().hex[:8]}"
    wrong_password="WrongPassword123!"

    # Act: Attempt to login
    bad_login_response=await async_client.post(
        "/authorize",
        data={
            "username":fake_username,
            "password":wrong_password
        }
    )

    assert bad_login_response.status_code==401
    assert bad_login_response.json()['detail']=="Incorrect username or password"
