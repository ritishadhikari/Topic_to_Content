from motor import motor_asyncio
import os
import asyncio
from dotenv import load_dotenv
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

load_dotenv()

mongo_uri=os.getenv("MONGO_URI")

client=motor_asyncio.AsyncIOMotorClient(host=mongo_uri)

db=client.ai_course_generator
collection=db.checkpoints

async def check_results():
    result= await collection.find_one(filter={'thread_id':'course_generation_Generative_AI_with_MCP,_Langgraph_and_FastAPI'})
    raw_data = result['checkpoint']
    serde=JsonPlusSerializer()
    checkpont_results=serde.loads_typed(data=('msgpack',raw_data))
    channel_values=checkpont_results['channel_values']

    day_number=channel_values.get("day_number",0)
    total_study_days=channel_values.get("total_study_days",0)
    
    return day_number,total_study_days
    

if __name__=="__main__":
    response=asyncio.run(main=check_results())
    print(response)