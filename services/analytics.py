import pandas as pd
from datetime import datetime
from services.data import calculate_intensity, sanitize_row
from services.utils import format_time_simple, format_time_detailed

def compute_stats(df):
    if df.empty:
        return {
            "total_miles": 0,
            "total_time": "0m",
            "total_seconds": 0,
            "total_activities": 0,
        }

    total_miles = float(round(df["distance_miles"].sum(), 2))
    total_seconds = int(df["elapsed_time_seconds"].sum())
    total_time = format_time_simple(total_seconds)
    total_activities = int(len(df))

    return {
        "total_miles": total_miles,
        "total_time": total_time,
        "total_seconds": total_seconds,
        "total_activities": total_activities,
    }

def get_activity_detail(df, mode, selected_date=None):
    if df.empty:
        return {"exists": False}

    # Strategy 1: Explicit lookup for a specific date
    if mode == 'date' and selected_date:
        subset = df[df["date_str"] == selected_date]
        if subset.empty:
            return {"exists": False}
        return build_response(subset, selected_date)
    
    # Strategy 2: Default/Latest lookup
    else: 
        subset = df.sort_values("date", ascending=False).head(1)
        if subset.empty:
            return {"exists": False}
        return build_response(subset, subset.iloc[0]["date_str"])

def build_response(subset, date_value):
    activities = []
    for _, row in subset.iterrows():
        # Convert row to dict for easy access
        raw_data = row.to_dict()
        clean = sanitize_row(raw_data)

        # Ensure we have a valid date/time object to work with
        date_obj = row.get("date")

        polyline = raw_data.get("summary_polyline")
        # Ensure it's None if it's empty, NaN, or an empty string
        if pd.isna(polyline) or polyline == "":
            polyline = None

        # Override specific fields with custom formatting
        activities.append({
            "name": str(clean["name"]),
            "type": str(clean["type_clean"]).capitalize(),
            "date": date_obj.strftime("%b %d, %Y") if pd.notna(date_obj) else "Unknown",
            "time": date_obj.strftime("%I:%M %p").lstrip("0") if pd.notna(date_obj) else "",
            "distance": round(float(clean["distance_miles"]), 2),
            "pace": str(raw_data.get("pace_min_per_mile_str", "N/A")),
            "moving_time": format_time_detailed(int(clean["moving_time_seconds"])),
            "elevation": round(float(clean["total_elevation_gain_feet"]), 0),
            "summary_polyline": polyline,
            "month_total": round(float(clean["month_cumulative_miles"]), 1),
            "total_miles": round(float(clean["total_cumulative_miles"]), 1)
        })

    return {
        "exists": True,
        "activities": activities,
        "date": date_value
    }

def build_timeline(df, start=None, end=None):
    # 1. Setup range
    start_dt = pd.to_datetime(start) if start else df["date"].min()
    #end_dt = pd.to_datetime(end) if end else df["date"].max() # Default to last activity
    end_dt = pd.to_datetime(end) if end else datetime.now() # Default to today
    all_dates = pd.date_range(start_dt, end_dt)

    # 2. Map data for lookups
    miles_per_day = df.groupby(df["date"].dt.strftime("%Y-%m-%d"))["distance_miles"].sum().to_dict()

    # 3. Create a DataFrame of all days in range for easy grouping
    timeline_df = pd.DataFrame({"date": all_dates})
    timeline_df["month_label"] = timeline_df["date"].dt.strftime("%B %Y")
    
    timeline_months = []
    
    # 4. Group by Month and iterate
    # Pandas naturally handles the month buckets for you!
    for label, group in timeline_df.groupby("month_label", sort=False):
        days = []
        for _, row in group.iterrows():
            d = row["date"]
            date_str = d.strftime("%Y-%m-%d")
            days.append({
                "date": date_str,
                "day": d.day,
                "weekday": (d.weekday() + 1) % 7,
                "intensity": calculate_intensity(miles_per_day.get(date_str, 0)),
                "tooltip": f"{date_str}: {miles_per_day.get(date_str, 0):.1f} mi"
            })
        
        timeline_months.append({"label": label, "days": days})

    # Return reversed months, keep days in order
    return timeline_months[::-1]

def build_grouped_metrics(df):
    if df.empty:
        return None
    
    # Calculate the range to decide on smoothing
    range_days = (df["date"].max() - df["date"].min()).days

    # Adaptive Window: 
    # Max view -> 28 days
    # 6 Month view -> 14 days
    # 1 Month view -> 7 days
    # 2 Week view -> 3 days
    if range_days > 365:
        win = 28
    elif range_days > 90:
        win = 14
    elif range_days > 30:
        win = 7
    else:
        win = 3

    # 1. Create a daily sum
    daily = df.groupby(df["date"].dt.date).agg({
        "distance_miles": "sum",
        "moving_time_seconds": "sum",
        "pace_min_per_mile": "mean"
    }).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    # 2. Reindex to include missing days
    all_days = pd.date_range(daily["date"].min(), daily["date"].max(), freq='D')
    daily = daily.set_index("date").reindex(all_days).reset_index()
    daily.rename(columns={"index": "x"}, inplace=True)

    # Now, manually fill ONLY the columns that should be zero on rest days
    daily["distance_miles"] = daily["distance_miles"].fillna(0)
    daily["moving_time_seconds"] = daily["moving_time_seconds"].fillna(0)

    # 3. Calculate Smoothed MILES
    # We use Gaussian smoothing on the daily miles
    daily["miles_smoothed"] = daily["distance_miles"].rolling(
        window=win, win_type='gaussian', min_periods=1, center=True
    ).mean(std=win/4) # Keep std proportional to window

    # 4. Calculate Smoothed PACE (Use the pre-computed pace from data loading)
    daily["raw_pace"] = daily["pace_min_per_mile"].interpolate(method='linear')  # First interpolate missing pace values
    
    # Second: Interpolate missing days so the line doesn't have "holes"
    # This fills in pace for rest days based on surrounding days
    daily["raw_pace"] = daily["raw_pace"].interpolate(method='linear')

    # Third: Apply the Gaussian smoothing to the pace
    daily["pace_smoothed"] = daily["raw_pace"].rolling(
        window=win, win_type='gaussian', min_periods=1, center=True
    ).mean(std=win/4) # Keep std proportional to window

    daily = daily.fillna(0)
    
    # Clean up
    daily["x"] = daily["x"].dt.strftime('%Y-%m-%d')
    return daily
