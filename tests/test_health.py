import pytest

@pytest.mark.asyncio  # used for async pytest
async def test_api_health_check(async_client):
    """
    Tests if the API is responding and if the database state is attached
    """
    response=await async_client.get("/health")

    assert response.status_code==200

    data=response.json()

    assert data['api_status']=="ok"
    assert "database" in data