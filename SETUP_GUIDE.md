# Quick Setup Guide

## Initial Setup

1. **Copy environment file template:**
   ```bash
   # Create .env file from template
   # On Windows (PowerShell):
   Copy-Item .env.example .env
   
   # On Linux/Mac:
   cp .env.example .env
   ```

2. **Edit `.env` file** with your settings (optional):
   ```env
   AIRFLOW_UID=50000
   AIRFLOW_IMAGE_NAME=apache/airflow:3.1.1
   AIRFLOW_PROJ_DIR=.
   _AIRFLOW_WWW_USER_USERNAME=airflow
   _AIRFLOW_WWW_USER_PASSWORD=airflow
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Wait for services to be healthy:**
   ```bash
   docker-compose ps
   ```

5. **Access the services:**
   - Airflow UI: http://localhost:8080 (airflow/airflow)
   - pgAdmin: http://localhost:5050 (admin@admin.com/admin)

6. **Configure PostgreSQL connection in Airflow:**
   - Go to Admin → Connections
   - Add connection:
     - Connection Id: `books_connection`
     - Connection Type: `Postgres`
     - Host: `postgres`
     - Schema: `airflow`
     - Login: `airflow`
     - Password: `airflow`
     - Port: `5432`

7. **Enable and run the DAG:**
   - Find `fetch_and_store_google_books` in Airflow UI
   - Toggle it ON
   - Trigger manually or wait for schedule

## Clean Up

To remove old logs and cache files:
```bash
# Remove Python cache
Remove-Item -Recurse -Force dags\__pycache__

# Logs are automatically excluded via .gitignore
```

## Project Files

- **Essential files:**
  - `dags/dag.py` - Main ETL pipeline
  - `docker-compose.yaml` - Docker configuration
  - `README.md` - Full documentation

- **Configuration files:**
  - `.gitignore` - Git ignore rules
  - `requirements.txt` - Python dependencies
  - `PROJECT_STRUCTURE.md` - Project structure

- **Auto-generated (gitignored):**
  - `logs/` - Airflow logs
  - `__pycache__/` - Python cache
  - `.env` - Environment variables (create from template)

