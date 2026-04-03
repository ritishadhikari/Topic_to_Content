from typing import List, Optional, Annotated, Dict,
from datetime import date, datetime
from pydantic import BaseModel, Field

def add_schedules(existing: List[Dict],new: List[Dict]) -> list[Dict]:
    return existing+new

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