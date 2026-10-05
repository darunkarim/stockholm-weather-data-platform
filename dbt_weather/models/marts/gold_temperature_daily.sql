{{ config(materialized='table') }}

-- Gold model for daily temperature analysis.
-- This model transforms the Silver data into a format
-- that is easier to use in Power BI and other analytics tools.

SELECT
    reference_date,

    -- Extract year and month from the date
    YEAR(reference_date) AS year,
    MONTH(reference_date) AS month,

    -- Get the month name
    DATENAME(month, reference_date) AS month_name,

    -- Categorize each date into a season
    CASE
        WHEN MONTH(reference_date) IN (12, 1, 2) THEN 'Winter'
        WHEN MONTH(reference_date) IN (3, 4, 5) THEN 'Spring'
        WHEN MONTH(reference_date) IN (6, 7, 8) THEN 'Summer'
        ELSE 'Autumn'
    END AS season,

    temperature_c,
    quality

FROM {{ ref('stg_silver_temperature') }}