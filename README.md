# STAMM Dashboard

## Direct usage

```bash
python3 -m stamm_dashboard.app
```

## Poetry usage

### Install Poetry

```bash
pip install poetry
```

### Install dependencies

```bash
# Make sure Poetry is installed
poetry install  # This will create the virtual environment and install project dependencies

# Activate the virtual environment created by Poetry
poetry shell  # This activates the Poetry virtual environment

# Verify that you're in the virtual environment by running:
which python  # macOS/Linux
# or
where python  # Windows
```
### Setup Environment Variables

Create a .env file in the root directory or inside Dashboards/env/ with the following structure:
```python

INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_organization
INFLUXDB_BUCKET=your_bucket_name
BACH_ID=_measurement
BASE_URL_API = url_ml_repository_api
```
### ▶️ Running the App

```bash
poetry run stamm -p 8081 -d
```
