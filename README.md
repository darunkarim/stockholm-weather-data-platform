\# Stockholm Weather Data Platform



A data engineering portfolio project that collects, processes, validates, and analyzes historical and daily weather data from SMHI for Stockholm.



The project demonstrates a complete data pipeline using Python, Azure, SQL, and Power BI.



\## Architecture



SMHI API

&#x20;  ↓

Python ingestion

&#x20;  ↓

Data validation \& transformation

&#x20;  ↓

Azure Data Lake Storage

&#x20;  ↓

Azure SQL

&#x20;  ↓

Power BI



\## Technologies



\- Python

\- Pandas

\- SQL

\- Azure Data Lake Storage

\- Azure SQL

\- Power BI

\- SMHI Open Data API

\- Git \& GitHub



\## Data Pipeline



\### 1. Data ingestion



Weather data is retrieved from the SMHI Open Data API using Python.



The pipeline currently handles:



\- Historical temperature data

\- Recent temperature data

\- Daily temperature ingestion

\- Data validation

\- Combining historical and recent datasets



\### 2. Data validation



The pipeline validates the data before it is stored.



Examples of validation checks include:



\- Missing temperatures

\- Duplicate dates

\- Date range

\- Data structure



\### 3. Bronze layer



Raw and combined weather data is stored in Azure Data Lake Storage.



Example structure:



```text

bronze/

└── temperature/

&#x20;   └── stockholm/

&#x20;       ├── 2026/

&#x20;       │   └── 09/

&#x20;       │       └── temperature\_2026-09-13.csv

&#x20;       └── complete/

&#x20;           └── stockholm\_temperature\_complete.csv



4\. Azure SQL



Processed weather data is loaded into Azure SQL for further analysis and reporting.



5\. Power BI



The data is visualized in Power BI to explore Stockholm's temperature trends over time.



Current dashboard includes:



Average temperature

Maximum temperature

Minimum temperature

Number of recorded days

Temperature over time

Yearly temperature trends

Temperature distribution

Dataset



The project uses daily mean air temperature data from:



SMHI station: Stockholm-Observatoriekullen A

Station ID: 98230

Parameter: Daily mean air temperature



The current dataset covers Stockholm from 1996 to the present.



Project Goals



The project is being developed incrementally to demonstrate common data engineering concepts:



Data ingestion

ETL/ELT pipelines

Data validation

Cloud storage

Data warehousing

SQL

Data transformation

Data visualization

Pipeline automation



Future improvements include:



Silver and Gold data layers

dbt transformations

Azure Data Factory

CI/CD

Infrastructure as Code with Terraform

Automated daily pipelines

Weather forecasting / machine learning

Project Status



🚧 Work in progress



The project is continuously being developed and improved as part of my Data Engineering portfolio.

