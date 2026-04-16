from typing import Dict, List
from datetime import date, timedelta

def add_schedules(existing: List[Dict],new: List[Dict]) -> List[Dict]:
    if len(existing)==0:    return new
    else:
        new_map={}
        for old_info in existing:   new_map[old_info['date']]=old_info

        for new_info in new:    new_map[new_info['date']]=new_info

        return sorted(new_map.values(), key=lambda k: k['date'])


async def get_exact_end_date(start_date: date, months_to_add: float) -> date:
    """
    Calculates the exact calendar end date by converting months to days.
    (Uses 30.44 days as the average month length to handle floats like 1.5)
    """
    total_days = int(months_to_add * 30.44)
    end_date = start_date + timedelta(days=total_days)
    return end_date
