from pydantic import BaseModel, Field
from typing import List
from datetime import timedelta


################### Pydantic Schema to enforce the Exact Topic Generation ###################
class DailyTopic(BaseModel):
    day_number:int = Field(description="The sequential day number (1,2,3 ...)")
    topic_title: str=Field(description="The specific sub-topic to study on this day")

class CurriculumPlan(BaseModel):
    daily_topics: List[DailyTopic]=Field(
        description="The complete list of topics. The length of this list MUST exactly match the requested number of study days"
    )

#############################################################################################