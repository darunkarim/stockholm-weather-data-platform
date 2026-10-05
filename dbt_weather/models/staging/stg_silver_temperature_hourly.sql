{{ config(materialized='view') }}

SELECT
    station_id,
    observation_time_utc,
    temperature_c,
    quality
FROM dbo.silver_temperature_hourly