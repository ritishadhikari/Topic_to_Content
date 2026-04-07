from typing import List, Annotated, Dict
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
import logging
from helper_functions import (add_schedules, get_exact_end_date)
from prompts import expert_curriculam_prompt
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic_schemas import CurriculumPlan

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger=logging.getLogger(name="TopicToContentGraph")


class GraphState(BaseModel):
    topic: str
    duration_months: int
    off_days: List[str]
    start_date: date
    system_date: date= Field(default_factory=date.today, frozen=True)
    full_schedule: Annotated[List[Dict], add_schedules] = Field (default_factory=list)

    current_target_date: date|None=None
    day_number: int=0
    latest_content: str|None=None
    has_code: bool=False
    is_valid: bool=False
    error_feedback: str|None=None
    is_completed: bool=False
    refresher_questions: Dict|None=None

async def input_processor(state:GraphState):
    """
    The entry point of the graph
    Sanitizes user inputs and starts the state tracking
    """

    logger.info(msg="--- [START] INITIALIZING CURRICULUM GRAPH ---")
    
    logger.info(msg=f"Topic:{state.topic}")
    
    clean_off_days=[s.strip().capitalize() for s in state.off_days]
    if clean_off_days: logger.info(msg=f"Configured Off Days: {' '.join(clean_off_days)}")

    return {
        "off_days" : clean_off_days,
        "day_number": 0,
        "is_completed": False,
        "full_schedule": []
    }

async def schedule_architect(state: GraphState):
    """
    Calculates the exact calendar, counts the working study days, and forces the LLM to generate exactly that many sub-topics using Pydantic
    """
    
    logger.info(msg="--- [PLANNING] ARCHTECTING MASTER SCHEDULE")
    
    current_day=state.start_date
    end_date=await get_exact_end_date(start_date=current_day,months_to_add=state.duration_months)

    logger.info(msg=f"Timeline: {current_day} to {end_date}")

    skeleton_schedule, study_dates, day_counter=[],[],1

    while current_day<=end_date:
        day_name=current_day.strftime(format="%A")
        
        if day_name in state.off_days:
            skeleton_schedule.append(
                {
                    "date": current_day,
                    "day_name": day_name,
                    "day_number": None,
                    "type": "OFF_DAY", 
                    "topic_metadata": None
                }
            )
        else:
            study_dates.append(current_day)
            skeleton_schedule.append(
                {
                    "date": current_day,
                    "day_name": day_name,
                    "day_number": day_counter,
                    "type": "STUDY_DAY", 
                    "topic_metadata": None
                }
            )
            day_counter+=1
        current_day+=timedelta(days=1)
    total_study_days=len(study_dates)
    
    logger.info(f"Calculated Timeline: {total_study_days} total exact study days found")

    llm=ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm=llm.with_structured_output(schema=CurriculumPlan)

    prompt=expert_curriculam_prompt(topic=state.topic,total_study_days=total_study_days)

    logger.info(msg=f"Requesting exactly {total_study_days} topics from LLM...")
    
    plan=await structured_llm.ainvoke(input=prompt)
    
    logger.info(f"LLM Successfully generated {len(plan.daily_topics)} topics")

    # merge LLM topics into the skeleton calendar
    id=0
    for schedule in skeleton_schedule:
        if schedule['type']=="STUDY_DAY":
            schedule['topic_metadata']=plan.daily_topics[id].topic_title
            id+=1

    first_study_date=study_dates[0] if study_dates else state.start_date

    logger.info(f"Master Plan complete. Setting initial target date to {first_study_date}")

    return {
        "full_schedule":skeleton_schedule,
        "current_target_date":first_study_date,
        "day_number":1
    }