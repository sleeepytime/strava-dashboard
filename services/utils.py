# utils.py

import numpy as np
from datetime import timedelta

def format_time_simple(seconds: int) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def format_time_detailed(seconds: int) -> str:
    return str(timedelta(seconds=int(seconds)))

def format_pace(min_per_mile: float) -> str:
    if min_per_mile is None or np.isnan(min_per_mile):
        return "N/A"
    minutes = int(min_per_mile)
    seconds = int(round((min_per_mile - minutes) * 60))
    if seconds == 60: # Handle rounding overflow
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"
