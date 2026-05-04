#strava_process_activities

import pandas as pd
import numpy as np
import math

# Load your CSV
df = pd.read_csv("preprocessed_strava_activities.csv")

# See the first 5 rows
print(df.head())
print()

# Remove meter from distance and convert to float for calculations
df['distance_meters'] = df['distance_meters'].astype(str).str.replace(' meter', '', regex=False).astype(float)

# Convert distance from meters to miles
df['distance_miles'] = df['distance_meters'] / 1609.34

# Remove meter from total_elevation_gain and convert to float for calculations
df['total_elevation_gain_meters'] = df['total_elevation_gain_meters'].astype(str).str.replace(' meter', '', regex=False).astype(float)
# Convert elevation_gain from meters to feet
df['total_elevation_gain_feet'] = df['total_elevation_gain_meters'] * 3.28084

# Convert date to iso format
df['date'] = pd.to_datetime(df['date'])
# Convert date to human readable format
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['month_name'] = df['date'].dt.month_name()
df['weekday'] = df['date'].dt.weekday  # 0 = Monday
df['weekday_name'] = df['date'].dt.day_name()
df['week'] = df['date'].dt.isocalendar().week
#print(df[['date', 'year', 'month' , 'weekday_name']].head())

# Calculate pace
df['pace_min_per_mile'] = df['moving_time_seconds'] / 60 / df['distance_miles']

def min_sec_format(x):
    # Total seconds
    total_seconds = round(x * 60)  # x is minutes as a float
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"

df['pace_min_per_mile_str'] = df['pace_min_per_mile'].apply(min_sec_format)

df = df.sort_values('date')
# Cumulative miles by month
df['month_cumulative_miles'] = df.groupby(['year', 'month'])['distance_miles'].cumsum()

# Cumulative miles overall
df['total_cumulative_miles'] = df['distance_miles'].cumsum()

# 1️ Distance conversion check
mask_distance = ~np.isclose(df['distance_miles'], df['distance_meters'] / 1609.344)
if mask_distance.any():
    print("Distance conversion mismatch in these rows:")
    print(df.loc[mask_distance, ['id','distance_meters','distance_miles']])

# 2️ Month cumulative miles check
for (year, month), group in df.groupby(['year','month']):
    if group['month_cumulative_miles'].diff().min() < 0:
        print(f"Month cumulative miles decreasing in {year}-{month}:")
        print(group.loc[group['month_cumulative_miles'].diff() < 0, 
                        ['id','month_cumulative_miles','distance_miles']])

# 3 Total cumulative miles check
mask_total = df['total_cumulative_miles'].diff() < 0
if mask_total.any():
    print("Total cumulative miles decreased in these rows:")
    print(df.loc[mask_total, ['id','total_cumulative_miles','distance_miles']])

# 4️ Pace check (moving_time_seconds / distance_miles)
calculated_pace = df['moving_time_seconds'] / df['distance_miles'] / 60
mask_pace = ~np.isclose(calculated_pace, df['pace_min_per_mile'])
if mask_pace.any():
    print("Pace calculation mismatch in these rows:")
    print(df.loc[mask_pace, ['id','moving_time_seconds','distance_miles','pace_min_per_mile']])
    
# 5 Pace check (pace_min_per_mile_str should have seconds < 60)
invalid_pace_str = df[df['pace_min_per_mile_str'].str.split(':').apply(lambda x: int(x[1]) >= 60)]
if not invalid_pace_str.empty:
    print("Warning: Found pace strings with invalid seconds:")
    print(invalid_pace_str[['id', 'pace_min_per_mile_str']])

# See the first 5 rows
print(df.head())

# Save a new processed CSV
df.to_csv("processed_strava_activities.csv", index=False)
print("\nActivities saved to processed_strava_activites.csv")