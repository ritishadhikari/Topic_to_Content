import streamlit as st
import requests
import os

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Khudse | AI Learning Platform",
    page_icon="🎓",
    layout="centered"
)

# ENVIRONMENT SETUP
API_URL=os.environ.get("API_URL","http://localhost:8991")

# SESSION STATE INITIALIZATION

if "auth_token" not in st.session_state : st.session_state.auth_token=None

if "username" not in st.session_state:  st.session_state.username=None

# Helper function to handle logout
def logout():
    st.session_state.auth_token=None
    st.session_state.username=None
    # st.rerun()  # callbacks are anyway rerun

# LOGIN & REGISTRY

if st.session_state.auth_token is None:
    st.markdown(body="""
                <h1 style='text-align:center;'>Khudse</h1>
            """,
        unsafe_allow_html=True
    )

    st.markdown(body="""
                    <p style='text-align:center; color: #94a3b8;'>Your persoanlized Tech Courses powered by AI</p>
                """,
                unsafe_allow_html=True
                )
    
    st.write("----")

    tab_login,tab_register=st.tabs(tabs=['Log In', "Create Account"])

    # LOGIN TAB
    with tab_login:
        with st.form(key="login_form"):
            st.subheader(body="Welcome Back")
            login_user=st.text_input(label="Username")
            login_pass=st.text_input(label="Password", type="password")
            submitted=st.form_submit_button(label="Sign In",width="stretch")

            if submitted:
                if not login_user or not login_pass:
                    st.warning(body="Please enter both username and password")
                else:
                    with st.spinner(text="Authenticating..."):
                        try:
                            response=requests.post(
                                url=f"{API_URL}/authorize",
                                data={'username':login_user, 'password': login_pass}
                            )
                            if response.status_code==200:
                                data=response.json()
                                st.session_state.auth_token=data.get('access_token')
                                st.session_state.username=login_user
                                st.success(body="Login Successful!")
                                st.rerun()
                            else:
                                st.error(body="Invalid Username or Password")
                        except requests.exceptions.ConnectionError:
                            st.error(body="Cannot connect to the backend server. Is it running?")
    
    with tab_register:
        with st.form(key="register_form"):
            st.subheader("Join Khudse")
            reg_user=st.text_input(label="Choose a Username")
            reg_email=st.text_input(label="Email Address")
            reg_password=st.text_input(label="Chose your Password", type="password")
            reg_submitted=st.form_submit_button(label="Sign Up", width="stretch")

            if reg_submitted:
                if not reg_user or not reg_email:
                    st.warning(body="Please fill in all the fields.")
                else:
                    with st.spinner(text="Creating your workspace..."):
                        try:
                            response=requests.post(
                                url=f"{API_URL}/register",
                                json={"username":reg_user,"email":reg_email,"password":reg_password}
                            )
                            
                            if response.status_code in (200,201):
                                st.success(body="Account created successfully! You may now log in.")
                            elif response.status_code==400:
                                st.error(body=response.get("detail","Username already exists!"))
                            else:
                                st.error(body="An error occurred during registration.")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to the backend server. Is it running?")
    st.stop()  # if token is not valid, then even after the rerun, should not redirect to the content generation 'else' page
else:  # Token is valid
    with st.sidebar:
        st.write(f"Hi {st.session_state.username}")
        st.button(label="Log Out", on_click=logout, width="stretch")
    

    st.title(body="Khudse")
    st.write("-------")
    tab_dashboard, tab_generate=st.tabs(tabs=["📚 My Courses", "✨ Generate New Course"])