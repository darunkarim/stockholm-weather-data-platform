{{ config(materialized='table') }}

SELECT
    observation_date AS reference_date,

    YEAR(observation_date) AS year,
    MONTH(observation_date) AS month,
    DATENAME(month, observation_date) AS month_name,

    CASE
        WHEN MONTH(observation_date) IN (12, 1, 2)
            THEN 'Winter'
        WHEN MONTH(observation_date) IN (3, 4, 5)
            THEN 'Spring'
        WHEN MONTH(observation_date) IN (6, 7, 8)
            THEN 'Summer'
        ELSE 'Autumn'
    END AS season,

    AVG(wind_speed_mps) AS avg_wind_speed_mps,
    MIN(wind_speed_mps) AS min_wind_speed_mps,
    MAX(wind_speed_mps) AS max_wind_speed_mps,
    COUNT(*) AS wind_observation_count

FROM {{ ref('stg_silver_wind') }}

GROUP BY
    observation_date