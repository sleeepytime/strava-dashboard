#strava_fetch_activities

import os
import json
import time
import requests
import pandas as pd
from stravalib.client import Client

# --- STEP 1: LOAD CREDENTIALS (HYBRID) ---
IS_GITHUB = os.getenv("GITHUB_ACTIONS") == "true"

if IS_GITHUB:
    print("Running in GitHub Actions mode...")
    CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
    CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
else:
    print("Running in Local mode...")
    if not os.path.exists("tokens.json"):
        raise FileNotFoundError("tokens.json not found. Run local auth first.")
    
    with open("tokens.json", "r") as f:
        tokens_data = json.load(f)
        CLIENT_ID = tokens_data["client_id"]
        CLIENT_SECRET = tokens_data["client_secret"]
        REFRESH_TOKEN = tokens_data["refresh_token"]

# --- STEP 2: REFRESH TOKEN ---
print("Refreshing access token...")
response = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
)

tokens_res = response.json()

# Handle potential API errors
if 'access_token' not in tokens_res:
    print("Error refreshing token:", tokens_res)
    exit(1)

access_token = tokens_res["access_token"]
new_refresh_token = tokens_res["refresh_token"]
new_expires_at = tokens_res["expires_at"]

# --- STEP 3: UPDATE LOCAL TOKENS (ONLY IF LOCAL) ---
# We don't try to update tokens on GitHub because environment variables are immutable.
if not IS_GITHUB:
    tokens_data["access_token"] = access_token
    tokens_data["refresh_token"] = new_refresh_token
    tokens_data["expires_at"] = new_expires_at
    with open("tokens.json", "w") as f:
        json.dump(tokens_data, f, indent=4)
    print("Local tokens.json updated.")

# --- STEP 4: INITIALIZE CLIENT & FETCH ---
client = Client(access_token=access_token)

try:
    df_existing = pd.read_csv("preprocessed_strava_activities.csv")
    existing_ids = set(df_existing['id'])
except FileNotFoundError:
    df_existing = pd.DataFrame()
    existing_ids = set()

new_activities = []
print("Fetching activities...")

for a in client.get_activities():
    if a.id in existing_ids:
        continue 
    
    new_activities.append({
        "id": a.id,
        "date": a.start_date_local,
        "name": a.name,
        "type": a.type,
        "elapsed_time_seconds": int(a.elapsed_time.total_seconds()),
        "moving_time_seconds": int(a.moving_time.total_seconds()),
        "distance_meters": a.distance,
        "total_elevation_gain_meters": a.total_elevation_gain,
        "summary_polyline": a.map.summary_polyline if a.map else None
    })

# --- STEP 5: SAVE DATA ---
if new_activities:
    df_new = pd.DataFrame(new_activities)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined['date'] = pd.to_datetime(df_combined['date'])
    df_combined.sort_values(by='date', ascending=True, inplace=True)
    
    df_combined.to_csv("preprocessed_strava_activities.csv", index=False)
    print(f"Success! Added {len(new_activities)} new activities.")
else:
    print("No new activities found.")