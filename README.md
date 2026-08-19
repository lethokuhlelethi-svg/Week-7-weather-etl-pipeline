# Weather ETL Pipeline

An ETL (Extract, Transform, Load) pipeline that collects live weather data from the OpenWeather API for 10 cities across different climates and hemispheres, cleans it with pandas, and stores it in both CSV and SQLite.

Built as Week 7 of the AnalystLab Africa data analytics internship.

---

## Project Overview

Data analysts rarely receive clean data. It usually has to be pulled from an API or database, reshaped, and stored before any analysis can happen. This project builds that process end to end.

The pipeline:

1. **Extracts** current weather for 10 cities from the OpenWeather API
2. **Transforms** the nested JSON responses into a flat, typed table
3. **Loads** the result into a CSV file and a SQLite database
4. **Analyses** the data to compare temperature, humidity and conditions across cities

The pipeline runs in **append mode**, so each run adds to the stored dataset rather than overwriting it. Running it repeatedly builds a weather history over time.

---

## Data Source

[OpenWeather Current Weather API](https://openweathermap.org/api) — free tier.

Endpoint used: `https://api.openweathermap.org/data/2.5/weather`

**Cities collected:**

| City | Country | Why included |
|---|---|---|
| Pretoria | ZA | Inland highveld |
| Cape Town | ZA | Coastal Mediterranean |
| Durban | ZA | Humid subtropical |
| Nairobi | KE | Equatorial highland |
| Cairo | EG | Desert |
| London | GB | Temperate maritime |
| Reykjavik | IS | Subarctic |
| Dubai | AE | Hot desert |
| Singapore | SG | Equatorial |
| Sydney | AU | Southern hemisphere |

Country codes are included in each query because city names are not unique — there are dozens of places called London, and OpenWeather's geocoding will otherwise return whichever it matches first.

---

## ETL Process

### Extract

A request is made per city with a 10-second timeout. The function returns `None` on failure instead of raising an exception, so a single failed city does not stop the whole run. Requests are spaced one second apart.

Errors are handled at two levels: HTTP status codes (a bad key, a city not found) and connection failures (no network, DNS issues).

### Transform

The API returns deeply nested JSON. Each response is flattened into one row, pulling values from different depths:

| Column | API field | Description |
|---|---|---|
| `city` | `name` | City name |
| `country` | `sys.country` | Country code |
| `temp_c` | `main.temp` | Temperature, Celsius |
| `feels_like_c` | `main.feels_like` | Perceived temperature, Celsius |
| `humidity_pct` | `main.humidity` | Relative humidity, % |
| `pressure_hpa` | `main.pressure` | Air pressure, hPa |
| `condition` | `weather[0].main` | Weather category |
| `description` | `weather[0].description` | Detailed condition |
| `wind_speed_ms` | `wind.speed` | Wind speed, m/s |
| `recorded_at` | `dt` | Measurement time (converted from Unix timestamp) |
| `temp_diff_c` | *derived* | `feels_like_c` minus `temp_c` |
| `collected_at` | *derived* | When the pipeline ran |

Units are written into the column names so a reader never has to guess whether a temperature is Celsius or Fahrenheit.

`recorded_at` and `collected_at` are deliberately separate: one is when the weather station took the measurement, the other is when this pipeline requested it.

All numeric columns are explicitly cast with `pd.to_numeric()`. No coercion was needed on the current data, but the step protects the pipeline if the API ever returns a value as text.

### Load

Two destinations:

- **CSV** — `data/weather_data.csv`, appended with headers written only on first creation
- **SQLite** — `data/weather.db`, table `weather`, using `if_exists="append"`

SQLite was chosen alongside CSV because it supports querying the accumulated history directly with SQL, which a flat file does not.

---

## Tools Used

| Tool | Purpose |
|---|---|
| Python 3 | Language |
| Requests | API calls |
| Pandas | Transformation and analysis |
| SQLite3 | Database storage |
| Matplotlib | Visualisation |
| Google Colab | Development environment |

---

## Setup

```bash
git clone https://github.com/lethokuhlelethi-svg/Week-7-weather-etl-pipeline.git
cd Week-7-weather-etl-pipeline
pip install -r requirements.txt
```

Set your OpenWeather API key as an environment variable:

```bash
export OWM_API_KEY="your_api_key_here"
```

Run the pipeline:

```bash
python etl_pipeline.py
```

**The API key is never stored in this repository.** It is read from an environment variable at runtime, and during development was held in Google Colab's secrets manager. Anyone running this project supplies their own key, free from [openweathermap.org](https://openweathermap.org).

---

## Steps Taken

1. Created an OpenWeather account and generated an API key
2. Stored the key as a Colab secret, outside the notebook file
3. Tested a single API call and inspected the JSON structure
4. Wrote an extraction function with timeout and error handling
5. Collected all 10 cities in a loop, with pacing between requests
6. Flattened the nested responses into a pandas DataFrame
7. Renamed columns, verified data types, checked for missing values
8. Added derived columns for perceived-temperature difference and collection time
9. Saved to CSV and SQLite in append mode
10. Analysed temperature, humidity and condition spread across cities
11. Refactored the notebook into a standalone `etl_pipeline.py` script

---

## Key Findings

From a single collection run (10 cities, 10 rows):

**Temperature ranged 26.2°C across the ten cities.** Dubai was hottest at 38.0°C, Reykjavik coldest at 11.8°C. The ordering follows latitude and season: Dubai and Cairo in northern-hemisphere summer desert climates, Reykjavik near the Arctic Circle, Sydney in southern-hemisphere winter.

**The most humid city was also the coldest.** Reykjavik recorded 76% humidity against Pretoria's 27%. This is not a contradiction , relative humidity measures how close the air is to saturation, and cold air saturates at much lower moisture content. Reykjavik at 76% and Singapore at 80% feel nothing alike. Absolute moisture and relative humidity are different measurements, and only the second one is in this dataset.

**Conditions were evenly split** : 6 clear, 4 cloudy. With one observation per city this is too small a sample to read as a pattern.

**Temperature and humidity are largely independent.** The hottest city was not the most humid, and the driest was not the coldest. Any assumption that the two move together does not hold here.

---

## Limitations

The ten cities span roughly ten time zones, so each was captured at a different point in its own daily cycle — morning in some, evening in others. These are **not like-for-like comparisons**, and a single snapshot cannot separate genuine climate differences from time-of-day effects.

Running the pipeline repeatedly across several days would average this out. The append-mode storage already supports this; only a scheduler is needed.

The dataset also contains only current conditions. There is no historical or forecast data, so no trend analysis is possible from a single run.

---

## Possible Extensions

- Schedule the pipeline hourly (cron, GitHub Actions, or Airflow) to build a genuine time series
- Add a logging layer to record run status and failures
- Include the forecast endpoint for forward-looking analysis
- Build a dashboard over the accumulated SQLite data

---

*Weather data provided by [OpenWeather](https://openweathermap.org).*
