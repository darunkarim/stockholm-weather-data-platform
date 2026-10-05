{{ config(materialized='view') }}

SELECT
    station_id,
    from_utc,
    to_utc,
    reference_date,
    precipitation_mm,
    quality
FROM dbo.silver_precipitation