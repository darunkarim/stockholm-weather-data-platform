-- Staging model for the Silver temperature data.
-- This model reads the table that Python loaded into Azure SQL.
-- We keep this layer simple and use it as the foundation for our Gold models.

SELECT
    reference_date,
    temperature_c,
    quality

FROM dbo.silver_temperature