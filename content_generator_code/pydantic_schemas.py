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

################# Code Presence Checker #####################################################
class CodePresence(BaseModel):
    has_code: bool=Field(description="True if the text contains executable code blocks (Python, JSON, CLI Commands, etc), False otherwise.")


################# Code Syntax Checker #######################################################
class SyntaxReview(BaseModel):
    is_valid: bool=Field(description="True if all code snippets are syntactically correct and follow best practices")
    corrected_content: str=Field(description="If errors exist, provide the FULL lesson text with the fixed code. If Valid, return the original text")

################# Pedagogical Validator #######################################################
class PedagogicalReview(BaseModel):
    is_pedagogically_sound:bool =Field(description="True if the lesson is highly engaging, easy to grasp, and uses strong analogies.")
    feedback: str=Field(description="Brief internal feedback on what was improved (or why it was already good)")
    # revised_content: str=Field(description="The fully polished, easy-to-grasp lesson text. It it was already perfect, return the original text")
