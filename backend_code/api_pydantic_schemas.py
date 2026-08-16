from pydantic import BaseModel, field_validator, EmailStr
from typing import List,Literal

class UserCreate(BaseModel):
    '''
    needed during user registration
    '''
    username: str
    email: EmailStr
    password: str

class Token(BaseModel):
    '''
    Retrieved as an output for /authorize
    '''
    access_token: str
    token_type: str

class CourseRequest(BaseModel):
    '''
    needed during course generation
    '''
    topic: str
    duration_months: float
    off_days: list[str]
    running_use_case_project: str|None=None  # keeping it optional for various deployment techniques

    @field_validator('off_days')
    @classmethod
    def check_max_off_days(cls,v):
        if len(v)>=7:
            raise ValueError("You must leave atleast one day for studying!")
        else:
            return v
    
class DataBaseUser(BaseModel):
    '''
    needed during passing the user details to various usable apis during the get_current_user()
    '''
    username: str
    hashed_password: str

####################################
class SyllabusItem(BaseModel):
    day_number: int
    daily_topic: str

class CourseSummaryItem(BaseModel):
    course_topic: str
    running_use_case_project: str | None= None
    syllabus: list[SyllabusItem] | None= None

class UserCoursesResponse(BaseModel):
    '''
    needed while fetching the  my_courses api
    '''
    total_courses:int
    courses: list[CourseSummaryItem]
#####################################

class CourseStatusResponse(BaseModel):
    '''
    Retrieved as an output for /courses/{topic}/status api
    '''
    status:Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "ERROR"]
    current_day: int
    total_study_days: int
    is_completed: bool

class DailyLessonResponse(BaseModel):
    '''
    Retrieved as an output for /courses/{topic}/day/{day_number}
    '''
    course_topic: str
    running_use_case_project: str| None=None
    day_number: int
    daily_topic: str
    lesson_content: str|None
    quiz_content: str| None=None