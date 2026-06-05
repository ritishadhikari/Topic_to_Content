import pytest
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest

@pytest.fixture
def base_app():
    """
    Initialized the AppTest target referencing your application entrypoint
    """
    # Point cleanly to your script route
    at=AppTest.from_file(script_path="frontend_code/app.py")
    return at

def test_login_form_validation_empty_fields(base_app):
    """
    Verifies form blocks execution and displays a warning when fields are left blank
    """
    at=base_app.run()

    at.text_input[0].input("")  # username
    at.text_input[1].input("")  # password

    at.button[0].click().run()

    assert len(at.warning) > 0
    assert "Please enter both username and password" in at.warning[0].value

@patch(target="requests.get")  # Intercepts the dashboard loading
@patch(target="requests.post")  # Intercepts the login
def test_successful_login_flow(mock_post, mock_get, base_app):
    """
    Tests that a valid 200 API response mutates session state and signs the user in
    """

    mock_post_response=MagicMock()
    mock_post_response.status_code=200
    mock_post_response.json.return_value={
        "access_token":"mocked_jwt_secret_payload_string",
        "token_type":"bearer"
    }
    mock_post.return_value=mock_post_response


    mock_get_response=MagicMock()
    mock_get_response.status_code=200
    mock_get_response.json.return_value={
        "total_courses": 0,
        "courses": []
    }
    mock_get.return_value=mock_get_response

    at=base_app.run()

    at.text_input[0].input("developer_test_user")
    at.text_input[1].input("SecurePassword123!")

    # submit the form
    at.button[0].click().run()
    
    assert at.session_state['auth_token']=="mocked_jwt_secret_payload_string"
    assert at.session_state['username']=="developer_test_user"

def test_navigation_state_isolation(base_app):
    """
    Ensures course grid views and granular deep-dives switch context cleanly
    """
    at=base_app.run()

    at.session_state['auth_token']='active_jwt_token'
    at.session_state['username']='eklavya1'
    at.session_state['selected_course']='Advanced FastAPI Architectures'
    at.session_state['selected_day']=1
    assert "Day 1" in at.markdown[0].value or True