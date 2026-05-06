import asyncio
import logging
from datetime import date
from langgraph.graph import StateGraph, START, END
import traceback

# import from head.py
from backend_code.content_generator_code.head import (
    GraphState, input_processor,
    curriculum_researcher, schedule_architect,
    daily_content_researcher, daily_content_generator,
    code_presence_checker, code_syntax_checker,
    pedagogical_validator, refresher_generator,
    route_after_code_check, mongo_db_save, state_updater
)
import os
from motor.motor_asyncio import AsyncIOMotorClient
from backend_code.database import db_state
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                    )
logger=logging.getLogger("PipelineRunner")

async def loop_incrementer(state: GraphState):
    """
    Increments the day counter and resets the daily variables so the next iteration of the loop starts fresh
    """
    logger.info(f"\n-- [LOOPING] MOVING TO DAY {state.day_number+1} ---")
    return {
        'day_number': state.day_number+1,
        'current_topic': None, 
        'daily_web_context': None, 
        'latest_content': None,
        'has_code': False,
        'refresher_questions': None
    }

async def loop_router(state: GraphState):
    """
    Checks if we have reached our study days limit
    """
    if state.day_number>3 or state.day_number > state.total_study_days: return END
    else: return "daily_content_researcher"

workflow=StateGraph(state_schema=GraphState)

workflow.add_node(node="input_processor",action=input_processor)
workflow.add_node(node="curriculum_researcher", action=curriculum_researcher)
workflow.add_node(node="schedule_architect", action=schedule_architect)
workflow.add_node(node="daily_content_researcher", action=daily_content_researcher)
workflow.add_node(node="daily_content_generator", action=daily_content_generator)
workflow.add_node(node="code_presence_checker", action=code_presence_checker)
workflow.add_node(node="code_syntax_checker", action=code_syntax_checker)
workflow.add_node(node="pedagogical_validator", action=pedagogical_validator)
workflow.add_node(node="refresher_generator", action=refresher_generator)
workflow.add_node(node="database_saver", action=mongo_db_save)
workflow.add_node(node="state_updater", action=state_updater)
workflow.add_node(node="loop_incrementer", action=loop_incrementer)

workflow.add_edge(start_key=START, end_key="input_processor")
workflow.add_edge(start_key="input_processor", end_key="curriculum_researcher")
workflow.add_edge(start_key="curriculum_researcher", end_key="schedule_architect")
workflow.add_edge(start_key="schedule_architect", end_key="daily_content_researcher")
workflow.add_edge(start_key="daily_content_researcher", end_key="daily_content_generator")
workflow.add_edge(start_key="daily_content_generator", end_key="code_presence_checker")

workflow.add_conditional_edges(
                               source="code_presence_checker",
                               path=route_after_code_check,
                               path_map={
                                   'code_syntax_checker': 'code_syntax_checker',
                                   'pedagogical_validator':'pedagogical_validator'
                                    }
                               )
workflow.add_edge(start_key="code_syntax_checker",end_key="pedagogical_validator")

workflow.add_edge(start_key="pedagogical_validator", end_key="refresher_generator")
workflow.add_edge(start_key="refresher_generator", end_key="database_saver")
workflow.add_edge(start_key="database_saver", end_key="state_updater")
workflow.add_edge(start_key="state_updater", end_key="loop_incrementer")

workflow.add_conditional_edges(
    source="loop_incrementer",
    path=loop_router,
    path_map={
        'daily_content_researcher':'daily_content_researcher',
        END:END
    }
)

async def run_pipeline(topic: str, username: str, 
                       duration_months: float, off_days: list, 
                       start_date: date=date.today()):
    logger.info(msg="="*60)
    logger.info(msg=f"STARTING LANGGRAPH FULL PIPELINE FOR {topic.upper()}")
    logger.info(msg="="*60)

    initial_input={
        "topic": topic,
        "username": username,
        "duration_months": duration_months,
        "off_days":off_days,
        "start_date": start_date
    }

    mongo_uri=os.environ.get("MONGO_URI")
    sync_client=MongoClient(host=mongo_uri)
    # Initialize the MongoDB Checkpointer
    checkpointer=MongoDBSaver(client=sync_client, db_name="ai_course_generator")
    
    # Compile the graph with the checkpointer attached
    app=workflow.compile(checkpointer=checkpointer)

    # Generate the unique "Saveslot" (thread_id) based on the course name
    clean_topic=topic.replace(" ","_")
    thread_id=f"course_generation_{username}_{clean_topic}"
    config={"configurable":{"thread_id":thread_id}}

    try:
        # check the database to see if this course crashed halfway through previously
        current_state=await app.aget_state(config=config)
        if len(current_state.next)==0 :  # brand new course since nothing inside the tuple
            logger.info(msg=f"Starting fresh pipeline for {topic}")
            final_state=await app.ainvoke(input=initial_input, config=config)
        else:  # crash has happened and hence None is passed to resume exactly where it left off
            logger.warning(f"Resuming crashed pipeline for {topic} from node: {current_state.next}")
            final_state=await app.ainvoke(input=None, config=config)

        logger.info(msg="="*60)
        logger.info(msg="✅ FULL COURSE GENERATION COMPLETED SUCCESSFULLY")
        logger.info(msg="="*60)
        # file_name=f"{initial_input['topic'].replace(' ','_')}_Course.md"
        # logger.info(f"[SUCCESS] The lessons and quizzes have been perfectly written to: {file_name}")
        logger.info(f"[SUCCESS] The lessons and quizzes have been perfectly written and has been inserted to the database")
    except Exception as e:
        logger.error(msg=f"❌ error during execution: {e}", exc_info=True)
        os.makedirs("demo_files", exist_ok=True)
        with open(file="demo_files/mcp_crash_report.txt",mode="w") as f:
            f.write(f"CRASH REPORT:\n{traceback.format_exc()}")


if __name__=="__main__":
    asyncio.run(run_pipeline(
        topic="Generative AI with MCP, Langgraph and FastAPI",
        duration_months=1.5,
        off_days=["Sunday","Thursday"]
        ))