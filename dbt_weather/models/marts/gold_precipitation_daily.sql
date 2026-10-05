{{ config(materialized='table') }}

SELECT
    station_id,
    reference_date,
    YEAR(reference_date) AS year,
    MONTH(reference_date) AS month,
    DATENAME(month, reference_date) AS month_name,

    CASE
        WHEN MONTH(reference_date) IN (12, 1, 2)
            THEN 'Winter'
        WHEN MONTH(reference_date) IN (3, 4, 5)
            THEN 'Spring'
        WHEN MONTH(reference_date) IN (6, 7, 8)
            THEN 'Summer'
        ELSE 'Autumn'
    END AS season,

    precipitation_mm,
    quality

FROM {{ ref('stg_silver_precipitation') }}