import os
from datetime import date, datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import bcrypt
from jose import JWTError, jwt
import motor.motor_asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging
from backend_code.pydantic_schema import UserCreate, Token, CourseRequest

from content_generator_code.pipeline_runner import run_pipeline

load_dotenv()



# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger=logging.getLogger(name="CourseAPI")



# SECURITY CONFIGURATION
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY","fallback-secret-change-me")
ALGORITHM=os.getenv("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES",120))

oauth2_schema=OAuth2PasswordBearer(tokenUrl="authorize")


# DATABASE CONNECTION
db=None
client=None  # Track the client so we can close it gracefully on shutdown
@asynccontextmanager
async def lifespan(app:FastAPI):
    global db,client
    mongo_uri=os.environ.get("MONGO_URI")
    if not mongo_uri:   logger.warning("MONGO_URI not found in environment variables")
    else:
        try:
            client=motor.motor_asyncio.AsyncIOMotorClient(host=mongo_uri)
            db=client.ai_course_generator
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}",exc_info=True)
    yield

    # shutdown logic
    if client:
        client.close()
        logger.info(msg="MongoDB connection closed cleanly")

app=FastAPI(title="AI Course Generator API",lifespan=lifespan)

# AUTHENTICATION UTILITIES

def verify_password(plain_password, hashed_password):
    """
    Required during Authorize
    """
    password_bytes=plain_password.encode('utf-8')[:72]
    hashed_password=hashed_password.encode('utf-8')
    return bcrypt.checkpw(password=password_bytes,hashed_password=hashed_password)
    

def get_password_hash(plain_password):
    """
    Required during Register User
    """
    password_bytes=plain_password.encode('utf-8')[:72]
    salt=bcrypt.gensalt()
    hashed_password=bcrypt.hashpw(password=password_bytes,salt=salt)
    return hashed_password.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta|None=None):
    """
    Required during Authorize
    """
    to_encode=data.copy()
    expire=datetime.utcnow()+(expires_delta if expires_delta is not None else timedelta(minutes=15))
    to_encode.update({'exp':expire})
    return jwt.encode(claims=to_encode,key=JWT_SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token: str=Depends(dependency=oauth2_schema)):
    """
    Dependency to validate the JWT token on protected routes
    """
    try:
        payload=jwt.decode(token=token,key=JWT_SECRET_KEY,algorithms=[ALGORITHM])
        username: str=payload.get('sub')
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username Not Found in the Token",
                headers={"WWW-Authenticate":'Bearer'}
                )
    except JWTError:  # what if the validity timeout has happened
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate":'Bearer'}
                )
    
    user=await db.users.find_one(filter={'username': username})
    if user is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username could not be located in the database",
                headers={"WWW-Authenticate":'Bearer'}
                )
    else: return user

@app.post(path="/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """
    Registers a new user and hashes their password
    """
    logger.info(msg="Attempting to register user: {user.username}")
    existing_user=await db.users.find_one({'username':user.username})
    if existing_user:
        logger.warning(msg=f"Registration failed: Username : {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username is already Registered")
    else:
        hashed_password=get_password_hash(plain_password=user.password)
        user_dict={
            'username':user.username,
            'hashed_password': hashed_password}
        await db.users.insert_one(document=user_dict)
        logger.info(msg=f"User {user.username} registered successfully.")
        return {"msg":"User created successfully"}
    
@app.post(path="/authorize",response_model=Token)
async def login_for_access_token(form_data:OAuth2PasswordRequestForm=Depends()):
    """
    The login endpoint. Returns a JWT token if credentials are valid
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    user=await db.users.find_one(filter={'username':form_data.username})
    if user is None or not verify_password(plain_password=form_data.password,
                                           hashed_password=user['hashed_password']):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    else:
        access_token_expires=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token=create_access_token(
            data={"sub":user['username']},
            expires_delta=access_token_expires
        )
        logger.info(f"Successful login for user: {form_data.username}")
        return {"access_token":access_token, "token_type":"bearer"}
    
# PROTECTED ROUTES (LangGraph Integration)

@app.post(path="/generate-course", status_code=status.HTTP_202_ACCEPTED)
async def generate_course(
    request: CourseRequest,
    background_tasks: BackgroundTasks,
    current_user: dict=Depends(dependency=get_current_user)
):
    """
    PROTECTED: Triggers the LangGraph pipeline as a background task
    """
    logger.info(msg=f"Course generation requested by {current_user['username']} for topic: {request.topic}")
    background_tasks.add_task(
        run_pipeline,
        topic=request.topic,
        duration_months=request.duration_months,
        off_days=request.off_days,
        start_date=date.today()
    )
    return {
        "msg": f"Pipeline started for {request.topic}. Check MongoDB for updates",
        "requested_by": current_user['username']
    }

@app.get(path="/courses/{topic}")
async def get_course_by_topic(topic: str, 
                              current_user: dict=Depends(dependency=get_current_user)
                              ):
    """
    PROTECTED: Only authenticated users can fetch generated courses from MongoDB.
    """
    clean_topic=topic.replace("_"," ")
    cursor=db.daily_lessons.\
        find({"course_topic":clean_topic}).\
        sort(key_or_list="day_number",direction=1)
    lessons=await cursor.to_list(length=180)

    if not lessons:
        logger.warning(f"No Lessons found for topic: {clean_topic}")
        raise HTTPException(status_code=404,
                            detail="Course not found or has not started generating yet")
    
    for lesson in lessons: lesson["_id"]=str(lesson["_id"])

    return {
        "course_topic": clean_topic,
        "total_lessons": len(lessons),
        "lessons": lessons
    }

    