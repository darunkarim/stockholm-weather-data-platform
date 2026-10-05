{{ config(materialized='table') }}

SELECT
    station_id,
    observation_time_utc,

    CAST(observation_time_utc AS DATE) AS observation_date,

    YEAR(observation_time_utc) AS year,

    MONTH(observation_time_utc) AS month,

    DATENAME(
        month,
        observation_time_utc
    ) AS month_name,

    DAY(observation_time_utc) AS day,

    DATEPART(
        hour,
        observation_time_utc
    ) AS hour,

    CASE
        WHEN MONTH(observation_time_utc) IN (12, 1, 2)
            THEN 'Winter'

        WHEN MONTH(observation_time_utc) IN (3, 4, 5)
            THEN 'Spring'

        WHEN MONTH(observation_time_utc) IN (6, 7, 8)
            THEN 'Summer'

        ELSE 'Autumn'
    END AS season,

    temperature_c,
    quality

FROM {{ ref('stg_silver_temperature_hourly') }}