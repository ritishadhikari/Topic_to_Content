import os
import logging
from datetime import date
from dotenv import load_dotenv

# Import the MCP Server SDK
from mcp.server.fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient

# Importing the actual business logic
from backend_code.content_generator_code.pipeline_runner import run_pipeline
from backend_code.database import db_state

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger=logging.getLogger(name="CourseGeneratorMCP")

# Initialize the MCP Server
mcp=FastMCP(name="CourseGeneratorServer")

# Generate new course
@mcp.tool()
async def generate_new_course(topic: str, duration_months: float, off_days: list[str]) ->str:
    """
    Triggers the AI Agent pipeline to research and generate a comprehensive daily study course.
    Use this tool ONLY when the user explicitly asks to generate, create, or bild a NEW course syllabus.

    Args:
        topic: The main subject the user wants to learn (e.g., "Advanced Python")
        duration_months: How long the course should last in months (e.g., 1.5).
        off_days: A list of days of the week to take off (e.g.: ["Sunday","Wednesday"])
    """
    logger.info(f"LLM requested to generate course for: {topic}")

    try:
        # Manually connect to MongoDB since FastAPI's lifespan is not running here
        mongo_uri=os.environ.get("MONGO_URI")
        db_state.client=AsyncIOMotorClient(host=mongo_uri)
        db_state.db=db_state.client.ai_course_generator
        await run_pipeline(
            topic=topic,
            duration_months=duration_months,
            off_days=off_days,
            start_date=date.today()
        )
        
        # Clean up the connection
        db_state.client.close()
        return f"Successfully generated the course for {topic}. The data has been saved to the database."
    except Exception as e:
        logger.error(msg=f"Pipeline failed: {e}",exc_info=True)
        return f"Error: Failed to generate course. {str(e)}"
        
    
    
# Read an existing course
@mcp.tool()
async def get_course_summary(topic: str) -> str:
    """
    Fetches an existing course curriculum from the MongoDB database.
    Use this tool when the user asks to view, read, summarize, or check if a course already exists.

    Args:
        topic: The exact name of the course to retrieve.
    """
    logger.info(f"LLM requested summary for existing course: {topic}")

    try:
        mongo_uri=os.environ.get("MONGO_URI")
        db_state.client=AsyncIOMotorClient(host=mongo_uri)
        db_state.db=db_state.client.ai_course_generator

        clean_topic=topic.replace("_"," ")
        cursor=db_state.db.daily_lessons.find(
            docs={'course_topic':clean_topic}).sort("day_number",1)
        lessons=await cursor.to_list(length=180)

        db_state.client.close()

        if not lessons:
            return f"No Course found for the topic {topic}. You should ask the user if they would want to generate it?"
        
        # Format the database JSON into a readable string for the LLM
        summary=f"Course: {clean_topic} \nTotal Lessons Found: {len(lessons)}"

        for lesson in lessons[:5]:
            summary+=f"Day {lesson["day_number"]}: {lesson["daily_topics"]}\n"
        summary+="\n...(More lessons are available in the database)"
        return summary
    
    except Exception as e:
        return f"Database Error: {str(e)}"
    

# Start the Server

if __name__=="__main__":
    logger.info(msg="Starting FastMCP Server on STDIO...")
    mcp.run()