"""
Weather ETL Pipeline
Extracts current weather from the OpenWeather API, transforms it into a
clean table, and loads it into CSV and SQLite.
"""

import os
import time
import sqlite3
from datetime import datetime

import requests
import pandas as pd

API_KEY = os.environ.get("OWM_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

CITIES = ["Pretoria,ZA", "Cape Town,ZA", "Durban,ZA", "Nairobi,KE", "Cairo,EG",
          "London,GB", "Reykjavik,IS", "Dubai,AE", "Singapore,SG", "Sydney,AU"]


def extract(city, api_key):
    """Fetch raw weather data for one city."""
    try:
        r = requests.get(BASE_URL,
                         params={"q": city, "appid": api_key, "units": "metric"},
                         timeout=10)
        if r.status_code != 200:
            print(f"  {city}: failed ({r.status_code})")
            return None
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"  {city}: connection error - {e}")
        return None


def transform(records):
    """Flatten raw API responses into a clean DataFrame."""
    rows = [{
        "city": d["name"],
        "country": d["sys"]["country"],
        "temp_c": d["main"]["temp"],
        "feels_like_c": d["main"]["feels_like"],
        "humidity_pct": d["main"]["humidity"],
        "pressure_hpa": d["main"]["pressure"],
        "condition": d["weather"][0]["main"],
        "description": d["weather"][0]["description"],
        "wind_speed_ms": d["wind"]["speed"],
        "recorded_at": datetime.utcfromtimestamp(d["dt"]),
    } for d in records]

    df = pd.DataFrame(rows)

    numeric = ["temp_c", "feels_like_c", "humidity_pct", "pressure_hpa", "wind_speed_ms"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["city"] = df["city"].str.strip().str.title()
    df["temp_diff_c"] = df["feels_like_c"] - df["temp_c"]
    df["collected_at"] = pd.Timestamp.now()

    return df.sort_values("temp_c", ascending=False).reset_index(drop=True)


def load(df, csv_path="data/weather_data.csv", db_path="data/weather.db"):
    """Save the clean data to CSV and SQLite."""
    os.makedirs("data", exist_ok=True)

    header = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode="a", header=header, index=False)

    conn = sqlite3.connect(db_path)
    df.to_sql("weather", conn, if_exists="append", index=False)
    conn.close()

    print(f"Loaded {len(df)} rows to {csv_path} and {db_path}")


def main():
    if not API_KEY:
        raise SystemExit("OWM_API_KEY environment variable not set.")

    print("Extracting...")
    raw = []
    for city in CITIES:
        result = extract(city, API_KEY)
        if result:
            raw.append(result)
            print(f"  {city}: OK")
        time.sleep(1)

    if not raw:
        raise SystemExit("No data collected.")

    print(f"\nTransforming {len(raw)} records...")
    df = transform(raw)

    print("Loading...")
    load(df)
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
