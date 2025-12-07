<img src="images/WhatsApp Image 2025-12-07 at 13.16.12_c2be6901.jpg" alt="Project Screenshot" width="800">

# Google Books ETL Pipeline with Apache Airflow

This project implements an ETL (Extract, Transform, Load) pipeline using Apache Airflow to fetch book data from Google Books API and store it in a PostgreSQL database.

## 📋 Project Overview

The pipeline performs the following operations:
1. **Extract**: Fetches data engineering books from Google Books API
2. **Transform**: Cleans and deduplicates the fetched book data
3. **Load**: Stores the processed data into a PostgreSQL database table

## 🏗️ Project Structure

```
GOOGLE_BOOKS_ETL/
├── dags/
│   └── dag.py                 # Main Airflow DAG definition
├── config/
│   └── airflow.cfg            # Airflow configuration file
├── plugins/                   # Custom Airflow plugins (currently empty)
├── logs/                      # Airflow execution logs
├── docker-compose.yaml        # Docker Compose configuration for Airflow stack
└── README.md                  # This file
```

## 📁 File Descriptions

### `dags/dag.py`
The main DAG file that defines the ETL workflow. It contains:
- **`get_google_books_data()`**: Fetches book data from Google Books API
  - Retrieves book titles, authors, prices, and ratings using Google Books API
  - Handles pagination to fetch multiple pages
  - Removes duplicates based on book titles
  - Stores data in XCom for task communication
- **`create_books_table()`**: Creates the `books` table in PostgreSQL if it doesn't exist
  - Table schema: `id`, `title`, `author`, `price`, `rating`
- **`insert_book_data_into_postgres()`**: Loads the extracted data into PostgreSQL
  - Retrieves data from XCom
  - Inserts records into the `books` table

**DAG Configuration:**
- **DAG ID**: `fetch_and_store_google_books`
- **Schedule**: Runs daily (`timedelta(days=1)`)
- **Tasks**: 
  1. `fetch_book_data` → Fetches 50 books by default
  2. `create_table` → Creates PostgreSQL table
  3. `insert_book_data` → Inserts data into database

### `docker-compose.yaml`
Docker Compose configuration that sets up the complete Airflow stack:
- **PostgreSQL**: Database for Airflow metadata and book data
- **Redis**: Message broker for Celery executor
- **Airflow Services**:
  - `airflow-apiserver`: REST API server (port 8080)
  - `airflow-scheduler`: Schedules and monitors DAGs
  - `airflow-dag-processor`: Processes DAG files
  - `airflow-worker`: Executes tasks using Celery
  - `airflow-triggerer`: Handles deferred tasks
  - `airflow-init`: Initializes Airflow database and creates admin user
- **pgAdmin**: PostgreSQL administration tool (port 5050)
- **Flower**: Celery monitoring tool (optional, port 5555)

### `config/airflow.cfg`
Airflow configuration file containing settings for:
- DAG folder paths
- Executor configuration
- Database connections
- Logging settings
- Security settings
- And other Airflow core configurations

### `plugins/`
Directory for custom Airflow plugins. Currently empty but can be used to add:
- Custom operators
- Custom hooks
- Custom sensors
- Custom executors

### `logs/`
Directory where Airflow stores execution logs for all DAG runs and tasks.

## 🚀 Prerequisites

Before running this project, ensure you have:

1. **Docker Desktop** installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Ensure Docker has at least:
     - 4GB RAM
     - 2 CPUs
     - 10GB disk space

2. **Git** (optional, for cloning the repository)

## ⚙️ Setup Instructions

### Step 1: Clone or Navigate to the Project Directory

```bash
cd GOOGLE_BOOKS_ETL
```

### Step 2: Set Environment Variables (Optional)

Create a `.env` file in the project root if you want to customize settings:

```env
AIRFLOW_UID=50000
AIRFLOW_IMAGE_NAME=apache/airflow:3.1.1
AIRFLOW_PROJ_DIR=.
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```

### Step 3: Initialize Airflow (First Time Only)

On Linux/Mac, set the Airflow user ID:

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

On Windows, you can skip this step or manually create `.env` with:
```
AIRFLOW_UID=50000
```

### Step 4: Start the Airflow Stack

```bash
docker-compose up -d
```

This command will:
- Pull required Docker images (first time only)
- Start all services (PostgreSQL, Redis, Airflow components)
- Initialize the Airflow database
- Create an admin user (username: `airflow`, password: `airflow`)

### Step 5: Wait for Services to Start

Wait for all services to be healthy (usually takes 2-3 minutes). Check status:

```bash
docker-compose ps
```

All services should show as "healthy" or "running".

### Step 6: Access Airflow Web UI

Open your browser and navigate to:
- **Airflow Web UI**: http://localhost:8080
- **Login credentials**:
  - Username: `airflow`
  - Password: `airflow`

### Step 7: Configure PostgreSQL Connection in Airflow

Before running the DAG, you need to set up the PostgreSQL connection:

1. In Airflow UI, go to **Admin** → **Connections**
2. Click **+** to add a new connection
3. Configure as follows:
   - **Connection Id**: `books_connection`
   - **Connection Type**: `Postgres`
   - **Host**: `postgres`
   - **Schema**: `airflow` (or create a new database)
   - **Login**: `airflow`
   - **Password**: `airflow`
   - **Port**: `5432`
4. Click **Save**

**Alternative: Create a separate database for books**

If you want to use a separate database for books:

1. Connect to PostgreSQL using pgAdmin (http://localhost:5050) or Docker:
   ```bash
   docker-compose exec postgres psql -U airflow -d airflow
   ```
2. Create a new database:
   ```sql
   CREATE DATABASE books_db;
   ```
3. Update the connection in Airflow to use `books_db` as the schema

### Step 8: Enable and Run the DAG

1. In Airflow UI, find the DAG `fetch_and_store_google_books`
2. Toggle it **ON** (unpause) using the switch on the left
3. Click on the DAG name to view details
4. Click the **Play** button (▶) to trigger a manual run, or wait for the scheduled run

## 🎯 Running the Pipeline

### Manual Execution

1. **Via Airflow UI**:
   - Go to the DAG page
   - Click **Trigger DAG** (play button)

2. **Via Command Line**:
   ```bash
   docker-compose exec airflow-apiserver airflow dags trigger fetch_and_store_google_books
   ```

### Scheduled Execution

The DAG is configured to run automatically every day. No action needed - it will execute based on the schedule.

### Monitor Execution

- **Airflow UI**: View DAG runs, task status, and logs
- **Logs**: Check task logs in the Airflow UI or in the `logs/` directory
- **Database**: Query the `books` table to see loaded data

## 🔍 Verifying Results

### Check Data in PostgreSQL

**Option 1: Using pgAdmin**
1. Open http://localhost:5050
2. Login with:
   - Email: `admin@admin.com`
   - Password: `admin`
3. Add server:
   - Host: `postgres`
   - Port: `5432`
   - Database: `airflow` (or `books_db` if created)
   - Username: `airflow`
   - Password: `airflow`
4. Navigate to the `books` table and view data

**Option 2: Using Docker CLI**
```bash
docker-compose exec postgres psql -U airflow -d airflow -c "SELECT * FROM books LIMIT 10;"
```

## 🛠️ Common Commands

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Slate)
```bash
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-worker
```

### Restart Services
```bash
docker-compose restart
```

### Check Service Status
```bash
docker-compose ps
```

### Access Airflow CLI
```bash
docker-compose exec airflow-apiserver airflow version
docker-compose exec airflow-apiserver airflow dags list
```

## ⚙️ Configuration

### Modify Number of Books to Fetch

Edit `dags/dag.py`, find the `fetch_book_data_task` definition:
```python
op_args=[50],  # Change 50 to desired number
```

### Change DAG Schedule

Edit `dags/dag.py`, find the `dag = DAG(...)` definition:
```python
schedule=timedelta(days=1),  # Change schedule as needed
```

### Customize Database Connection

Update the connection in Airflow UI (Admin → Connections) or modify the connection ID `'books_connection'` in `dag.py` (in `create_books_table()` and `insert_book_data_into_postgres()` functions).

## 🐛 Troubleshooting

### DAG Not Appearing
- Check if DAG file has syntax errors: `docker-compose exec airflow-apiserver airflow dags list-import-errors`
- Ensure DAG is in the `dags/` folder
- Check logs: `docker-compose logs airflow-dag-processor`

### Connection Errors
- Verify PostgreSQL connection is configured correctly in Airflow
- Check if PostgreSQL service is running: `docker-compose ps postgres`
- Test connection: `docker-compose exec postgres pg_isready -U airflow`

### Task Failures
- Check task logs in Airflow UI
- Verify internet connection (for API calls)
- Check if Google Books API is accessible (verify API status)

### Port Already in Use
- Change ports in `docker-compose.yaml` if 8080 or 5050 are already in use
- Update port mappings: `"8081:8080"` for Airflow, `"5051:80"` for pgAdmin

## 📦 Dependencies

The project uses the following Python packages (included in Airflow image):
- `apache-airflow`: Workflow orchestration
- `pandas`: Data manipulation
- `requests`: HTTP requests for API calls
- `psycopg2`: PostgreSQL adapter
- `apache-airflow-providers-postgres`: PostgreSQL provider for Airflow

## 🔐 Security Notes

⚠️ **Important**: This configuration is for **local development only**. Do not use in production without:
- Changing default passwords
- Setting up proper authentication
- Using environment variables for sensitive data
- Implementing proper network security
- Using HTTPS
- Setting up proper backup strategies

## 📝 License

This project uses Apache Airflow, which is licensed under the Apache License 2.0.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📧 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Airflow documentation: https://airflow.apache.org/docs/
3. Check Docker logs for detailed error messages

---

**Happy ETL-ing! 🚀**


