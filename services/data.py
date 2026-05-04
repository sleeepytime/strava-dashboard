import pandas as pd
import os
from datetime import datetime
from flask import request
from functools import lru_cache

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "processed_strava_activities.csv")
EXPECTED_COLUMNS = [
    "date", "distance_miles", "type", "elapsed_time_seconds", 
    "moving_time_seconds", "total_elevation_gain_feet", "type_clean"
]

@lru_cache(maxsize=1)
def load_data():
    """
    Loads and pre-processes the core dataset with safety checks. 
    Cached to prevent unnecessary disk reads.
    """
    if not os.path.exists(DATA_PATH):
        # Return a "Template" DataFrame with correct columns but no data
        print(f"INFO: {DATA_PATH} not found. Returning empty template.")
        # Create the template
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        # Force the types so .dt and .sum() don't crash
        df["date"] = pd.to_datetime(df["date"])
        df["distance_miles"] = pd.to_numeric(df["distance_miles"])
        return df
     
    # Try to load the data
    try:
        df = pd.read_csv(DATA_PATH)
        # Integrity Check: Is the file empty?
        if df.empty:
            df = pd.DataFrame(columns=EXPECTED_COLUMNS)
            df["date"] = pd.to_datetime(df["date"])
            return df        
        
        # 1. Standardize Dates
        # Using errors='coerce' handles any weirdly formatted strings in the CSV
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df = df.dropna(subset=["date"]) # Remove rows with invalid dates
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

        # 2. Time-based features
        # These are 'expensive' to calculate, so we do them once here
        df["year_month"] = df["date"].dt.to_period("M")
        df["month_num"] = df["date"].dt.month
        df["year"] = df["date"].dt.year

        # 3. Numeric Cleaning & Type Safety
        # Force distance to be a float. fillna(0) ensures stats functions don't crash
        df["distance_miles"] = pd.to_numeric(df["distance_miles"], errors="coerce").fillna(0.0)
        
        # Ensure time columns are integers
        time_cols = ["elapsed_time_seconds", "moving_time_seconds"]
        for col in time_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # 4. Activity Type Normalization
        df["type_clean"] = df["type"].str.lower().str.strip()
        
        # We keep these flags for quick filtering later
        df["is_run"] = df["type_clean"].str.contains("run")
        df["is_walk"] = df["type_clean"].str.contains("walk")

        return df
    
    except Exception as e:
        # Catch unexpected errors (like corrupted CSV formatting)
        print(f"CRITICAL: Error reading {DATA_PATH}: {e}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def filter_df(df, start, end):
    """
    Filters the dataframe by a date range.
    Start/End should be strings in 'YYYY-MM-DD' format.
    """
    if df.empty:
        return df

    # Convert strings to timestamps for comparison
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)

    # Professional filtering: Use boolean masking for speed
    # We use (df["date"] <= end_ts) assuming the user wants to include the 'end' day.
    mask = (df["date"] >= start_ts) & (df["date"] <= end_ts + pd.Timedelta(days=1))
    
    return df.loc[mask]

def get_default_dates(df):
    ytd_start = datetime.now().strftime("%Y-01-01")
    today = datetime.now().strftime("%Y-%m-%d")

    if df.empty:
        return ytd_start, today
    
    min_date = df["date"].min().strftime("%Y-%m-%d")
    #max_date = df["date"].max().strftime("%Y-%m-%d") #last activity 
    return min_date, today #max_date

def parse_activity_types(types_param):
    if types_param is None: return ["run", "walk"]
    if types_param == "": return []
    return types_param.split(",")

def get_current_view_data(args):
    """
    Retrieves and filters data based on URL parameters.
    Handles empty type selections and date boundaries.
    """
    df = load_data().copy()

    if df.empty:
        abs_min, abs_max = get_default_dates(df)
        return df, abs_min, abs_max

    abs_min, abs_max = get_default_dates(df)

    # 1. Date Logic
    # We grab the absolute min/today as fallback defaults
    start = args.get("start") or abs_min
    end = args.get("end") or abs_max
    
    # 2. Apply Date Filter
    df = filter_df(df, start, end)

    # 3. Activity Type Logic
    # Handle the case where 'types' is missing or an empty string
    selected_types = parse_activity_types(args.get("types"))

    #4. Filter the dataframe
    if selected_types:
        df = df[df["type_clean"].isin(selected_types)]
    else:
        # Return an empty dataframe structure if nothing is selected
        df = df.iloc[0:0]

    return df, start, end

def sanitize_row(row_dict):
    """
    A central place to clean row data.
    Ensures no NaNs/None types reach the frontend.
    """
    # Define your default values
    defaults = {
        "name": "Untitled Activity",
        "type_clean": "Activity",
        "distance_miles": 0.0,
        "moving_time_seconds": 0,
        "total_elevation_gain_feet": 0,
        "month_cumulative_miles": 0.0,
        "total_cumulative_miles": 0.0
    }
    
    cleaned = {}
    for key, default in defaults.items():
        val = row_dict.get(key)
        # Use simple logic: if it's missing or NaN, use the default
        cleaned[key] = default if (pd.isna(val) or val is None) else val
        
    return cleaned

def calculate_intensity(miles):
    if miles == 0:
        return 0
    elif miles < 3:
        return 1
    elif miles < 6:
        return 2
    else:
        return 3
