import asyncio
import logging
from datetime import date
from langgraph.graph import StateGraph, START, END

# import from head.py
from head import (
    GraphState, input_processor,
    curriculum_researcher, schedule_architect,
    daily_content_researcher, daily_content_generator,
    code_presence_checker, code_syntax_checker,
    pedagogical_validator, refresher_generator,
    route_after_code_check, state_save
)

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
    if state.day_number>5 or state.day_number > state.total_study_days: return END
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
workflow.add_node(node="state_save", action=state_save)
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
workflow.add_edge(start_key="refresher_generator", end_key="state_save")
workflow.add_edge(start_key="state_save", end_key="loop_incrementer")

workflow.add_conditional_edges(
    source="loop_incrementer",
    path=loop_router,
    path_map={
        'daily_content_researcher':'daily_content_researcher',
        END:END
    }
)

app=workflow.compile()


async def run_pipeline():
    logger.info(msg="="*60)
    logger.info(msg="STARTING LANGGRAPH FULL PIPELINE LOOP ORCHESTRATION")
    logger.info(msg="="*60)

    initial_input={
        "topic": "Generative AI with MCP, Langgraph and FastAPI",
        "duration_months": 1.5,
        "off_days":["sunday","Thursday"],
        "start_date": date.today()
    }

    try:
        final_state=await app.ainvoke(input=initial_input)
        logger.info(msg="="*60)
        logger.info(msg="✅ FULL COURSE GENERATION COMPLETED SUCCESSFULLY")
        logger.info(msg="="*60)
        file_name=f"{initial_input['topic'].replace(' ','_')}_Course.md"
        logger.info(f"[SUCCESS] The lessons and quizzes have been perfectly written to: {file_name}")
    except Exception as e:
        logger.error(msg=f"❌ error during execution: {e}", exc_info=True)

if __name__=="__main__":
    asyncio.run(run_pipeline())