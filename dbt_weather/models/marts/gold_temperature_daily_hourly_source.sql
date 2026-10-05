{{ config(materialized='table') }}

SELECT
    station_id,

    CAST(
        observation_time_utc AS DATE
    ) AS observation_date,

    YEAR(observation_time_utc) AS year,

    MONTH(observation_time_utc) AS month,

    DATENAME(
        month,
        observation_time_utc
    ) AS month_name,

    CASE
        WHEN MONTH(observation_time_utc) IN (12, 1, 2)
            THEN 'Winter'

        WHEN MONTH(observation_time_utc) IN (3, 4, 5)
            THEN 'Spring'

        WHEN MONTH(observation_time_utc) IN (6, 7, 8)
            THEN 'Summer'

        ELSE 'Autumn'
    END AS season,

    COUNT(*) AS observation_count,

    AVG(temperature_c) AS avg_temperature_c,

    MIN(temperature_c) AS min_temperature_c,

    MAX(temperature_c) AS max_temperature_c

FROM {{ ref('stg_silver_temperature_hourly') }}

GROUP BY
    station_id,
    CAST(observation_time_utc AS DATE),
    YEAR(observation_time_utc),
    MONTH(observation_time_utc),
    DATENAME(
        month,
        observation_time_utc
    ),
    CASE
        WHEN MONTH(observation_time_utc) IN (12, 1, 2)
            THEN 'Winter'

        WHEN MONTH(observation_time_utc) IN (3, 4, 5)
            THEN 'Spring'

        WHEN MONTH(observation_time_utc) IN (6, 7, 8)
            THEN 'Summer'

        ELSE 'Autumn'
    END