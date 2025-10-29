# STAMM Dashboard

## Clone repository

First, download project source

```bash
git clone git@gitlab.com:stamm-4m/dashboard.git
cd dashboard
```

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
`-p` indicates the port and `-d` activates debug mode.