# 📦 Multi-db-connector

A flexible and extensible Python package to connect to multiple database types — currently supporting InfluxDB and PostgreSQL — for use in dashboards, data pipelines (e.g., Airflow), and more.

🚀 Features

* Unified API to connect and query different database types.
* Easy to extend with new database connectors (MongoDB, MySQL, etc.).
* Can be reused across Dash apps, Airflow DAGs, or CLI tools.
* Clean structure for testability and production-readiness.

## 📁 Project Structure
```
multi-db-connector/
├── multi_db_connector/
│   ├── __init__.py
│   ├── base.py
│   ├── influxdb_connector.py
│   ├── postgres_connector.py
│   └── factory.py
├── tests/
│   └── test_factory.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md

```

## Install (Dev Mode)

```bash
pip install -e .
```

## 📦 Requirements

* influxdb-client
* psycopg2-binary
* pandas
* python-dotenv

These are automatically installed via pyproject.toml.

## ⚙️ Usage
### Step 1: Define Your Config
Use .env, Python dictionary, or external config to define:

InfluxDB Example

```python
from multi_db_connector.factory import get_connector

config = {
    "type": "influxdb",
    "url": "http://localhost:8086",
    "token": "your-token",
    "org": "your-org"
}
```

PostgreSQL Example

```python
from multi_db_connector.factory import get_connector

config = {
    "type": "postgres",
    "dbname": "my_database",
    "user": "my_user",
    "password": "my_password",
    "host": "localhost",
    "port": 5432
}
```

### Step 2: Connect and Query

```python

from multi_db_connector.factory import get_connector

# Instantiate the right connector
connector = get_connector(config)

# Connect to the DB
connector.connect()

# Run a query
result_df = connector.query("SELECT * FROM your_table")  # PostgreSQL example

# Close connection
connector.close()

```
## 📊 Querying Examples

### 🔍 PostgreSQL Queries
You can write any standard SQL query:

```python
"SELECT * FROM users"
"SELECT COUNT(*) FROM logs WHERE status = 'ERROR'"
"SELECT created_at FROM events ORDER BY created_at DESC LIMIT 10"
```

###  📈 InfluxDB Queries (Flux)
You must use Flux query language:

```python

flux_query = """
from(bucket: "sensor-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "temperature")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
"""
result_df = connector.query(flux_query)

```
Returns a pandas.DataFrame.


## ➕ Adding New Databases
Create a new file like mongodb_connector.py

Inherit from BaseDBConnector

Implement connect, query, close

Register it inside factory.py
