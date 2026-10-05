SELECT
    station_id,
    observation_time_utc,
    COUNT(*) AS duplicate_count
FROM {{ ref('gold_temperature_hourly') }}
GROUP BY
    station_id,
    observation_time_utc
HAVING COUNT(*) > 1