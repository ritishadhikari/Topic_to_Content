from pydantic import BaseModel
from typing import List,Literal

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CourseRequest(BaseModel):
    topic: str
    duration_months: float
    off_days: list[str]
    
class DataBaseUser(BaseModel):
    username: str
    hashed_password: str

class SyllabusItem(BaseModel):
    day_number: int
    daily_topic: str

class CourseSummaryItem(BaseModel):
    course_topic: str
    running_use_case_project: str | None= None
    syllabus: list[SyllabusItem] | None= None

class UserCoursesResponse(BaseModel):
    total_courses:int
    courses: list[CourseSummaryItem]

class CourseStatusResponse(BaseModel):
    status:Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "ERROR"]
    current_day: int
    total_study_days: int
    is_completed: bool

class DailyLessonResponse(BaseModel):
    course_topic: str
    running_use_case_project: str| None=None
    day_number: int
    daily_topic: str
    lesson_content: str|None
    quiz_content: str| None=None