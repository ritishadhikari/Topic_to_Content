from pydantic import BaseModel

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