{{ config(materialized='view') }}

SELECT
    station_id,
    observation_time_utc,
    observation_date,
    wind_speed_mps,
    quality,
    year,
    month,
    day,
    hour

FROM dbo.silver_wind