import streamlit as st
import requests
import os
import time
import logging

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Khudse | AI Learning Platform",
    page_icon="🎓",
    layout="centered"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(name="KhudseFrontend")

# ENVIRONMENT SETUP
API_URL=os.environ.get("API_URL","http://localhost:8991")

# SESSION STATE INITIALIZATION

if "auth_token" not in st.session_state : st.session_state.auth_token=None

if "username" not in st.session_state:  st.session_state.username=None

if "active_generations" not in st.session_state:    st.session_state.active_generations=[]  # memory for background tasks

if "selected_course" not in st.session_state:   st.session_state.selected_course=None

if "selected_day" not in st.session_state: st.session_state.selected_day=1


# Helper function to handle logout
def logout():
    st.session_state.auth_token=None
    st.session_state.username=None
    # st.rerun()  # callbacks are anyway rerun

def open_course(topic):
    st.session_state.selected_course=topic
    st.session_state.selected_day=1

def close_course():
    st.session_state.selected_course=None

def go_previous_day():
    st.session_state.selected_day-=1

def go_next_day():
    st.session_state.selected_day+=1



# LOGIN & REGISTRY

if st.session_state.auth_token is None:
    st.markdown(body="""
                <h1 style='text-align:center;'>Khudse</h1>
            """,
        unsafe_allow_html=True
    )

    st.markdown(body="""
                    <p style='text-align:center; color: #94a3b8;'>Your personalized Tech Courses powered by AI</p>
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
                                logger.info(msg=f"User `{login_user}` authenticated successfully via UI form.")
                                st.success(body="Login Successful!")
                                st.rerun()
                            else:
                                st.error(body="Invalid Username or Password")
                                logger.warning(msg=f"Failed authentication attempt for username: `{login_user} - Status Code: {response.status_code}`")
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
                                logger.info(msg=f"Account for User `{reg_user}` created successfully")
                            elif response.status_code==400:
                                st.error(body=response.get("detail","Username already exists!"))
                                logger.warning(msg=f"Username already exists for the user - {reg_user}")
                            else:
                                st.error(body=f"An error occurred during registration.{response.status_code}")
                                logger.warning(msg=f"An error occurred during registration. - {response.status_code}")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to the backend server. Is it running?")
    st.stop()  # if token is not valid, then even after the rerun, should not redirect to the content generation 'else' page
else:  # Token is valid
    with st.sidebar:
        st.write(f"Hi {st.session_state.username}")
        st.button(label="Log Out", on_click=logout, width="stretch")

        if st.session_state.active_generations:
            st.write("---")
            st.write("### ⚙️ Active Generations")

            completed_tasks=[]
            headers={"Authorization":f"Bearer {st.session_state.auth_token}"}

            # Poll the backend for each course currently in memory
            for topic in st.session_state.active_generations:
                try:
                    poll_res=requests.get(f"{API_URL}/courses/{topic}/status", headers=headers)
                    if poll_res.status_code==200:
                        data=poll_res.json()
                        status=data.get("status")

                        if status=="IN_PROGRESS":
                            st.info(f"**{topic}**\n\nDrafting Day {data.get('current_day',0)}")
                        elif status=="COMPLETED":
                            st.success(f"✅**{topic}** complete!")
                            completed_tasks.append(topic)
                        elif status=="ERROR":
                            st.error(body=f"❌**{topic}** failed.")
                            completed_tasks.append(topic)
                except:
                    logger.error(f"Tracking thread lost or connection dropped for topic: {topic}")
                    st.warning(body=f"⚠️ Tracking lost for {topic}")

            for ct in completed_tasks:
                st.session_state.active_generations.remove(ct)

        if st.session_state.active_generations:
            st.button(label="🔄 Refresh Progress", width="stretch")

    # In the main window
    st.title(body="Khudse")
    st.write("-------")
    tab_dashboard, tab_generate=st.tabs(tabs=["📚 My Courses", "✨ Generate New Course"])

    with tab_dashboard:
        if st.session_state.selected_course is None:
            st.subheader(body="Your learning Paths")

            headers={'Authorization':f"Bearer {st.session_state.auth_token}"}
            
            with st.spinner(text="Fetching your customized courses..."):
                try:
                    response=requests.get(f"{API_URL}/my-courses", headers=headers)
                    if response.status_code==200:
                        data=response.json()
                        total_courses=data.get("total_courses",0)
                        courses=data.get('courses',[])

                        if total_courses==0:
                            st.info(body="You haven't generated any courses yet. Head over to the `Generate New Course` tab to get it started")
                        else:
                            for course in courses:
                                topic=course.get('course_topic',"Unknown Topic")
                                project=course.get('running_use_case_project', 'No Project assigned')

                                with st.expander(f"🎓 {topic}"):
                                    st.markdown(f"**Capstone Project:** {project}")
                                    st.write("----")

                                    # display the syllabus
                                    syllabus=course.get("syllabus",[])
                                    for day in syllabus:
                                        day_num=day.get("day_number")
                                        day_topic=day.get("daily_topic")
                                        st.write(f"**Day {day_num}:** {day_topic}")
                                    st.write("")
                                    
                                    st.button(label=f"Resume {topic}",key=f"resume_{topic}",type='primary',on_click=open_course, args=(topic,),width="stretch")
                    elif response.status_code==401:
                        st.warning(body="Your session has expired. Please login again.")      
                        logout() 
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(body=f"Failed to fetch courses. Server responded with {response.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the backend server. Is it running?")
        else:
            active_topic=st.session_state.selected_course
            current_day=st.session_state.selected_day

            col_title, col_back=st.columns(spec=[8,2])
            with col_title: st.subheader(body=f"📖{active_topic}")
            with col_back:  st.button(label="← Back to Grid", width="stretch", on_click=close_course)
            
            st.write("---")

            col_prev, col_day, col_next=st.columns(spec=[2,4,2])
            with col_prev:
                st.button(label="⬅️ Previous Day", disabled=(current_day==1), width="stretch", on_click=go_previous_day)

            with col_day:
                st.markdown(body=f"<h4 style='text-align: center'>Day {current_day} </h4>", unsafe_allow_html=True)
            
            with col_next:
                st.button(label="Next Day ➡️", width="stretch", on_click=go_next_day)

            st.write("---")
            
            # Fetch Mark-down content on-demand
            with st.spinner(text=f"Loading Day {current_day} materials..."):
                try:
                    headers={"Authorization":f"Bearer {st.session_state.auth_token}"}
                    res=requests.get(url=f"{API_URL}/courses/{active_topic}/day/{current_day}", headers=headers)

                    if res.status_code==200: 
                        lesson_data=res.json()
                        
                        st.markdown(body=f"### {lesson_data.get('daily_topic')}")
                        st.info(body=f"**Capstone Context**: {lesson_data.get('running_use_case_project')}")

                        tab_lesson, tab_quiz=st.tabs(tabs=["📚 Interactive Lesson", "📝 Daily Quiz"])

                        with tab_lesson: st.markdown(body=lesson_data.get('lesson_content'))

                        with tab_quiz:  st.markdown(body=lesson_data.get('quiz_content'))

                    elif res.status_code==404:
                        st.warning(body="You have reached the end of this course, or this does not exists yet!")
                    elif res.status_code==401:
                        st.warning(body="Session expired.")
                        logout()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(body=f"Error fetching lesson: {res.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error(body="Cannot connect to the server.")
            
    with tab_generate:
        st.subheader(body="Create a Custom Curriculum")
        with st.form(key="generate_new_form"):
            course_topic=st.text_input(label="What would you want to learn", placeholder="e.g. GCP Vertex AI")

            col_a, col_b=st.columns(spec=2)
            with col_a:
                duration_months=st.slider(label="Duration (Months)", max_value=6, min_value=1, value=1)
            with col_b:
                off_days=st.multiselect(
                    label="Select your days off (No studying!)",
                    options=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
                    default=["Sunday"]
                )
            submitted=st.form_submit_button(label="Select to generate your course", width="stretch")
        
        if submitted:
            if not course_topic:
                st.warning(body="Please enter a topic to generate a course.")
            elif course_topic in st.session_state.active_generations:
                st.warning(body="You are already generating this course!")
            else:
                headers={"Authorization":f"Bearer {st.session_state.auth_token}"}
                payloads={
                    "topic":course_topic,
                    "duration_months":duration_months,
                    "off_days": off_days
                }
            
                with st.spinner(text=f"Generating course for {course_topic} through AI"):
                    try:
                        logger.info(msg=f"Dispatching generation request for topic: `{course_topic}` by `{st.session_state.username}`")
                        trigger_response=requests.post(url=f"{API_URL}/generate-course", json=payloads,headers=headers)

                        if trigger_response.status_code==202:
                            st.session_state.active_generations.append(course_topic)
                            st.success(body=f"Course Generated set in Progress. Track your course : {course_topic} in the sidebar. You may continue to explore other features in this website")

                            time.sleep(1)
                            st.rerun()
                        elif trigger_response.status_code==401:
                            st.warning(body="Session expired. Please log in.")
                            logout()
                            time.sleep()
                            st.rerun()
                        else:
                            st.error(body=f"Failed to start. Server returned {trigger_response.status_code} error")

                    except requests.exceptions.ConnectionError:
                        st.error(body="Cannot connect to the server.")