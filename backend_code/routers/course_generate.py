import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from backend_code.pydantic_schema import CourseRequest, DataBaseUser
from backend_code.database import db_state
from backend_code.security import get_current_user
from backend_code.content_generator_code.pipeline_runner import run_pipeline

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y:%m:%d %H:%M:%S",
    level=logging.INFO
)

logger=logging.getLogger(name="CourseRouter")
router=APIRouter(tags=["Courses"])

@router.post(path="/generate-course", status_code=status.HTTP_202_ACCEPTED)
async def generate_course(
    request: CourseRequest,
    background_tasks:BackgroundTasks,
    current_user: DataBaseUser=Depends(dependency=get_current_user)
):
    logger.info(msg=f"Course generation requested by {current_user.username} for topic: {request.topic}")
    background_tasks.add_task(
        func=run_pipeline,
        topic=request.topic,
        username=current_user.username,
        duration_months=request.duration_months,
        off_days=request.off_days,
        start_date=date.today()
        )
    return {
        "msg":f"Pipeline started for {request.topic}. Check MongoDB for updates",
        "requested_by": current_user.username
    }

@router.get(path="/courses/{topic}", status_code=status.HTTP_200_OK)
async def get_course_by_topic(topic: str, current_user:DataBaseUser=Depends(dependency=get_current_user)):
    clean_topic=topic.replace("_"," ")
    cursor=db_state.db.daily_lessons.\
        find({'course_topic': clean_topic,'username':current_user.username}).\
            sort(key_or_list="day_number", direction=1)
    lessons=await cursor.to_list(length=180)

    if not lessons:
        logger.warning(f"No Lessons found for the topic: {clean_topic}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found or has not started yet"
        )
    else:   
        for lesson in lessons:  lesson["_id"]=str(lesson["_id"])
    
    return {
        "course_topic": clean_topic,
        "total_lessons": len(lessons),
        "lessons": lessons
    }