from typing import Dict, List
from datetime import date
import calendar

def add_schedules(existing: List[Dict],new: List[Dict]) -> List[Dict]:
    if len(existing)==0:    return new
    else:
        new_map={}
        for old_info in existing:   new_map[old_info['date']]=old_info

        for new_info in new:    new_map[new_info['date']]=new_info

        return sorted(new_map.values(), key=lambda k: k['date'])


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
