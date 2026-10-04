# Product Data ETL Pipeline & Analytics Dashboard

A Data Engineering project that extracts product data from an API, transforms and validates it, loads it into PostgreSQL, and presents insights through an interactive Streamlit dashboard.

## Project Overview

This project demonstrates an end-to-end ETL (Extract, Transform, Load) workflow using Python. It processes product-catalog data from DummyJSON and makes it available for SQL analysis and interactive visualization.

## Architecture

```text
DummyJSON API
     ↓
Extract product data
     ↓
Transform and validate
     ↓
Load into PostgreSQL
     ↓
SQL analytics
     ↓
Streamlit dashboard
```

## Tech Stack

- **Python** — ETL pipeline and data processing
- **REST API** — product-data extraction
- **PostgreSQL** — relational data storage
- **SQL** — analytical queries
- **Pandas** — data manipulation
- **Streamlit** — interactive dashboard
- **Plotly** — data visualizations
- **Docker** — containerization
- **Pytest / unittest** — testing
- **Git and GitHub** — version control

## Features

- API-based product-data extraction
- Data cleaning, transformation, and validation
- PostgreSQL storage with rerunnable upserts
- Logging for pipeline execution and errors
- Interactive dashboard with filtering and analysis
- Database integration tests
- Docker image for running the ETL pipeline

## Project Structure

```text
first_project_py/
├── src/
│   ├── api_client.py
│   ├── db_connection.py
│   ├── load_product.py
│   └── dashboard.py
├── tests/
├── data/
├── logs/
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── README.md
└── .env
```

## Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

   `pip install -r requirements.txt`

4. Create a local `.env` file with your PostgreSQL connection settings:

   `DB_HOST=localhost`  
   `DB_PORT=5432`  
   `DB_NAME=learning_db`  
   `DB_USER=your_username`  
   `DB_PASSWORD=your_password`

5. Create the PostgreSQL `products` table using the schema required by the pipeline.
6. Run the ETL pipeline:

   `python src/load_product.py`

7. Launch the dashboard:

   `streamlit run src/dashboard.py`

## Run Tests

Run the database integration tests with:

`python -m unittest discover -s tests -v`

If pytest is installed, you can also use:

`python -m pytest -v`

These database tests require a reachable PostgreSQL instance with the expected database and table configured.

## Run with Docker

Build the image from the project root:

`docker build -t first-project-py .`

Run the pipeline when PostgreSQL is running on your Mac:

`docker run --rm --env-file .env -e DB_HOST=host.docker.internal first-project-py`

Keep `.env` private and never commit database credentials.

## Data Source

Product-catalog data from the [DummyJSON Products API](https://dummyjson.com/products).

The source provides sample product data for development and demonstration; it is not a live sales or customer database.

## Learning Outcomes

- Building an API-to-database ETL pipeline
- Validating structured data
- Working with PostgreSQL and SQL analytics
- Creating data dashboards
- Logging and testing data workflows
- Containerizing a Python application with Docker

## Future Improvements

- Schedule automated pipeline runs
- Add data-quality and transformation unit tests
- Introduce CI with GitHub Actions
- Deploy the dashboard to a hosted environment
