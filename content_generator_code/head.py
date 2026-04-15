from typing import List, Annotated, Dict
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
import logging, json
from helper_functions import (add_schedules, get_exact_end_date)
from prompts import (expert_curriculam_prompt, researcher_prompt, daily_content_prompt, 
                     code_presence_checker_prompt, syntax_checker_prompt, pedagogical_validator_prompt,
                     refiner_prompt)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic_schemas import (CurriculumPlan, CodePresence, SyntaxReview, PedagogicalReview)
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import BraveSearchWrapper, GoogleSerperAPIWrapper



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
    
    research_notes: str| None = None
    total_study_days:int=0
    current_topic:str|None=None
    daily_web_context:str|None=None
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

async def curriculum_researcher(state: GraphState):
    """ 
    Uses Tavily to search the live web for the most up-to-date course structures, syllabi, and advanced topics before synthesizing the master outline.
    """
    logger.info(msg="---[RESEARCHING] GATHERING LIVE SYLLABUS DATA")

    # search_tool=TavilySearchResults(max_results=4, search_depth="advanced")
    current_year=state.system_date.year
    search_query=f"Latest Comprehensive syllabus course outline topics for {state.topic} {current_year}"
    logger.info(msg=f"Executing Web Search: {search_query}")

    try:
        logger.info(msg="Attempting Search with Brave API")
        search_tool=BraveSearchWrapper()
        search_results=json.loads(search_tool.run(search_query))
        web_context="\n\n".join([f"Source: {result.get('link','Unknown')}\nContent: {result.get('snippet','')}" for result in search_results[:4]])
        logger.info(msg="Brave Web Search Successful")
    except Exception as brave_err:
        logger.warning(msg=f"Brave search failed due to Quota limit error. Error: {brave_err} ")
        try:  # fallback to Serper API
            logger.info(msg="Falling Back to Serper API")
            search_tool=GoogleSerperAPIWrapper(k=4)
            search_results=search_tool.results(search_query).get("organic",[])
            web_context="\n\n".join([f"Source: {result.get('link','Unknown')}\nContent: {result.get('snippet','')}" for result in search_results])
        except Exception as serper_err:
            logger.warning(msg=f"Serper Search also failed. Error: {serper_err}")
            web_context="No live web data available. Relying on internal knowledge"


    llm=ChatOpenAI(model='gpt-4o', temperature=0.2)
    prompt=researcher_prompt(topic=state.topic, duration_months=state.duration_months, web_context=web_context)

    response=await llm.ainvoke(prompt)
    logger.info(msg="Research Complete. Up-to-date syllabus outline generated")

    return {
        "research_notes": response.content
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

    prompt=expert_curriculam_prompt(topic=state.topic,total_study_days=total_study_days, research_notes=state.research_notes)

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
        "day_number":1, 
        "total_study_days": total_study_days
    }

async def daily_content_researcher(state:GraphState):
    """
    Identify today's specific topic if it isn't set yet
    """
    todays_topic=state.current_topic
    if todays_topic is None:
        for day in state.full_schedule:
            if day.get('day_number')==state.day_number:
                todays_topic=day.get('topic_metadata')
                break
    
    logger.info(msg=f"--- [DAILY RESEARCH] FETCHING CONTEXT FOR DAY {state.day_number}: {todays_topic}")

    search_query=f"{todays_topic} in {state.topic} tutorial examples latest"

    try:
        logger.info(msg="Attempting Search with Brave API for Content Generation")
        search_tool=BraveSearchWrapper()
        search_results=json.loads(search_tool.run(search_query))
        web_context="\n\n".join([f"Source: {result.get('link','Unknown')}\nContent: {result.get('snippet','')}" for result in search_results[:4]])
        logger.info(msg="Brave Web Search Successful")
    except Exception as brave_err:
        logger.warning(msg=f"Brave search failed due to Quota limit error. Error: {brave_err} ")
        try:  # fallback to Serper API
            logger.info(msg="Falling Back to Serper API")
            search_tool=GoogleSerperAPIWrapper(k=4)
            search_results=search_tool.results(search_query).get("organic",[])
            web_context="\n\n".join([f"Source: {result.get('link','Unknown')}\nContent: {result.get('snippet','')}" for result in search_results])
        except Exception as serper_err:
            logger.warning(msg=f"Serper Search also failed. Error: {serper_err}")
            web_context="No live web data available. Relying on internal knowledge"
        
    return {
        "current_topic": todays_topic,
        "daily_web_context": web_context
    }
    
async def daily_content_generator(state: GraphState):
    """
    Takes the gathered web context and writes the actual educational lesson.
    """
    logger.info(msg=f"--- [DAILY GENERATOR] WRITING LESSON FOR DAY {state.day_number} ---")
    
    llm=ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    daily_prompt=daily_content_prompt(
        course_topic=state.topic,
        daily_topic=state.current_topic,
        web_context=state.daily_web_context
        )
    
    response=await llm.ainvoke(input=daily_prompt)
    logger.info(msg=f"Lesson for Day {state.day_number} successfully generated!")

    return {
        "latest_content":response.content

    }


async def code_presence_checker(state: GraphState):
    """
    Analyzes the daily content to determine if it contains any code blocks.
    Updates the state.has_code boolean for the router
    """
    logger.info(msg=f"---[QA] CHECKING FOR CODE IN DAY {state.day_number} CONTENT")

    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm=llm.with_structured_output(schema=CodePresence)
    code_presence_prompt=code_presence_checker_prompt(content=state.latest_content)
    result= await structured_llm.ainvoke(input=code_presence_prompt)
    logger.info(msg=f"Code found in lesson: {result.has_code}")

    return {
        "has_code": result.has_code
    }

async def code_syntax_checker(state: GraphState):
    """
    If code is present, this node reviews it for syntax errors, best practices and relevancy.
    If it finds errors or irrelavant code, it fixes them and updates the lesson content.
    """
    logger.info(msg="---[QA] VALIDATING CODE SYNTAX & RELEVANCY")

    llm=ChatOpenAI(model='gpt-4o', temperature=0)
    structured_llm=llm.with_structured_output(schema=SyntaxReview)
    syntax_prompt=syntax_checker_prompt(
        latest_content=state.latest_content,
        course_topic=state.topic,
        daily_topic=state.current_topic
        )
    review=await structured_llm.ainvoke(input=syntax_prompt)
    if review.is_valid:
        logger.info(msg="Code Syntax is perfectly valid and relevant. No changes needed")
        return {}
    else:
        logger.warning(msg="Syntax or relevancy errors detected! Applying corrections to the lesson")
        return {
            "latest_content": review.corrected_content
        }
    
async def route_after_code_check(state:GraphState):
    """
    Reads the state.has_code boolean and returns the name of the next node
    """
    if state.has_code:  return "code_syntax_checker"
    else: return "pedagogical_validator"


async def pedagogical_validator(state: GraphState):
    """
    Acts as Editor-in-Cheif. Ensures the text is easy to grasp, uses analogies and maintains a high pedagocical standard befire saving.
    """
    logger.info(msg="--- [QA] PEDAGOGICAL VALIDATION (EDITIOR-IN-CHIEF) ---")
    llm=ChatOpenAI(model='gpt-4o', temperature=0.4)
    structured_llm=llm.with_structured_output(schema=PedagogicalReview)

    pedagogical_prompt=pedagogical_validator_prompt(
        course_topic=state.topic,
        daily_topic=state.current_topic,
        lesson_content=state.latest_content,
        web_context=state.daily_web_context
    )

    review=await structured_llm.ainvoke(input=pedagogical_prompt)

    if review.is_pedagogically_sound:
        logger.info(msg="Pedagocical check passed: Content is engaging and easy to grasp.")
        return {
            'is_valid': True,
            'error_feedback': None
        }
    else:
        logger.info(msg=f'Pedagocical improvements applied. Editor Feedback: {review.feedback}')
        return {
            'is_valid': False,
            'error_feedback': review.feedback
        }


async def refiner(state: GraphState):
    """
    Takes the feedback from the Editor-in-Chief and rewrites the content.
    """
    logger.info(msg="---[QA] REFINER: REWRITING CONTENT BASED ON FEEDBACK ---")
    
    llm=ChatOpenAI(model="gpt-4o", temperature=0.4)

    ref_prompt=refiner_prompt(course_topic=state.topic,
                              daily_topic=state.current_topic,
                              lesson_content=state.latest_content,
                              web_context=state.daily_web_context,
                              feedback=state.error_feedback)
    
    response=await llm.ainvoke(input=ref_prompt)
    logger.info(msg="Content Successfully refined.")

    return {
        "latest_content": response.content,
        "error_feedback":None
    }


# Add this to the bottom of head.py

# async def state_save(state: GraphState):
#     """
#     Saves the finalized daily content into the master schedule dictionary
#     and appends the text to a local .txt file for easy reading.
#     """
#     logger.info(msg=f"--- [SAVING] WRITING DAY {state.day_number} CONTENT TO FILE & STATE ---")
    
#     # 1. Write the content to a local .txt file
#     # We replace spaces in the topic name with underscores for a clean filename
#     filename = f"{state.topic.replace(' ', '_')}_Course.txt"
    
#     with open(filename, "a", encoding="utf-8") as f:
#         f.write(f"\n\n{'='*60}\n")
#         f.write(f"DAY {state.day_number}: {state.current_topic}\n")
#         f.write(f"{'='*60}\n\n")
#         if state.latest_content:
#             f.write(state.latest_content)
            
#     logger.info(msg=f"Content successfully appended to {filename}")

#     # 2. Update the master schedule in the LangGraph State
#     updated_day = None
#     for day in state.full_schedule:
#         if day.get("day_number") == state.day_number and day.get("type") == "STUDY_DAY":
#             updated_day = day.copy()
#             # Inject the final content into the dictionary without overwriting the topic_metadata
#             updated_day["final_lesson_content"] = state.latest_content
#             break
            
#     if updated_day:
#         # Returning this 1-item list triggers the add_schedules reducer 
#         # to safely merge this update into the master calendar!
#         return {"full_schedule": [updated_day]}
        
#     return {}