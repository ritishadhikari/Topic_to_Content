from typing import Dict, List
from datetime import date
import calendar

def add_schedules(existing: List[Dict],new: List[Dict]) -> list[Dict]:
    return existing+new

async def get_exact_end_date(start_date: date, months_to_add: int) -> date:
    """
    Calculates the exact calendar end date
    Handles year rollovers and end-of-month clipping
    """
    month=start_date.month-1+months_to_add
    year=start_date.year + month//12
    month=month%12 + 1
    day=min(start_date.day, calendar.monthrange(year=year, month=month)[1])
    return date(year, month, day)
