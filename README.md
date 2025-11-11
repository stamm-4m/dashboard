# STAMM Dashboard

This repository provides an interactive **Dash-based web dashboard** for monitoring, analyzing, and visualizing machine learning model behavior in production.  

It integrates with **InfluxDB** for time-series data and a **Model Repository API** for managing trained models.

---

## ⚙️ Features

- 📊 **Dash-based web interface** for interactive model and data monitoring.  
- 📈 **InfluxDB integration** for real-time signal tracking.  
- 🤖 **Model Repository API connection** for loading and managing ML models.  
- 🔄 **Modular architecture**: drift detection and database connectors are modular subpackages.  
- 🧩 **Poetry-based dependency management** for clean reproducibility.

---

## 🧰 Requirements


- **Docker** and **Docker Compose** (recommended)
- Or manually:
  - Python **>=3.10, <3.13**
  - [Poetry](https://python-poetry.org/) **1.8+**

---

# 🚀 How to Use the STAMM Dashboard

Follow the steps below to set up and run the **STAMM Dashboard**, an interactive monitoring interface built with Dash, InfluxDB, and the STAMM Model Repository API.


## 🧩 1. Clone repository

Clone the project from GitLab and move into the project directory:

```bash
git clone git@gitlab.com:stamm-4m/dashboard.git
cd dashboard
```

## 🔐 2. Environment Configuration

All sensitive connection settings (such as InfluxDB and Model Repository API credentials) are stored in a .env file.
You can place it either in the project root directory or inside the Dashboard/ folder.

If you require a demo .env configuration, please contact: csuarez@unicauca.edu.co

### 🧾 Example `.env`

```bash
#######################################
# DATABASE CONFIGURATION
#######################################
# Database engine type
DB_ENGINE=influxdb
# InfluxDB server connection
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=my-secret-token
INFLUXDB_ORG=my-org
INFLUXDB_BUCKET=my-bucket

# Data measeurement configuration 
INFLUXDB_MEASUREMENT=bioreactor_obs
INFLUXDB_BATCH_ID=batch_id

# Device and project identification
# Modify according to your specific setup (e.g., Penicillin, E. coli, etc.)
INFLUXDB_DEVICE_ID=my-device
INFLUXDB_PROJECT_NAME=my-

# Predefined buckets (⚠️ do not modify)
INFLUXDB_BUCKET=STAMM_Bucket
INFLUXDB_BUCKET_RAW=stamm_raw
INFLUXDB_BUCKET_PREDICTIONS=stamm_predictions
INFLUXDB_BUCKET_METADATA=stamm_metadata

#######################################
# SQLITE CONFIGURATION
#######################################
# Local SQLite directory (⚠️ do not modify)
DB_SQLITE_DIR=data


#######################################
# MODEL REPOSITORY CONFIGURATION
#######################################
# Base URL of the Model Repository API
BASE_URL_API = my-url-to-api

# Associated project identifier
PROJECT_ID=my-project-id 
```
⚠️ Security note:
Never commit .env files to GitLab. Make sure .env is included in .gitignore.

## 🐳 3. Docker Setup
Ensure that **Docker** and **Docker Compose** are installed and running on your system.
 
Install Docker Compose (if it’s not installed) and open it, making sure it’s running.

[Install Docker](https://docs.docker.com/get-docker/)

[Install Docker Compose
](https://docs.docker.com/compose/install/)

Once installed, verify your setup with:
```bash
docker --version
docker compose version
```

## ▶️ 4. Run the Dashboard (One-Click Start)

You can start the full environment with a single click or command.

### 🪟 For Windows

Run the following script as **Administrator**:

-run_docker.bat

🐧 For Linux / macOS

```bash
chmod +x run_docker.sh
./run_docker.sh
```

The script will:

1. Build and start the Docker Compose environment.
2. Automatically launch the Dashboard when ready.
3. Open the interface at:

👉 http://localhost:8050

Once running, the Dashboard will automatically connect to the configured **InfluxDB** instance and the **Model Repository API**.

The executable file will start the Docker Compose, and when it’s ready, it will open http://localhost:8050/ where you can use STAMM.


## 🧠 Quick Debug Commands

If you need to check container logs or troubleshoot:
```bash
# List running containers
docker ps

# View dashboard logs
docker logs -f dashboard

# Restart the dashboard container
docker restart dashboard

# Stop all running containers
docker compose down
```

# ⚙️ Direct Usage via Poetry

You can also run **STAMM Dashboard** directly using [Poetry](https://python-poetry.org/), without Docker.  
This method is ideal for **development**, **testing**, or **lightweight execution** environments.

## 📦 1. Install Poetry

If you don’t have Poetry installed yet, run the following command:

```bash
pip install poetry
```
You can verify the installation with:
```bash
poetry --version
```

## 🧩 2. Install Project Dependencies

Once Poetry is installed, install all required dependencies:
```bash
poetry install
```
This command will:

-Create a virtual environment automatically.

-Install all dependencies defined in pyproject.toml.

If you only want to install the main (non-dev) dependencies, use:
```bash
poetry install --only main
```

## ▶️ 3. Running the App

```bash
poetry run stamm -p 8081 -d
```
`-p` indicates the port and `-d` activates debug mode.

# 📫 Contact

For questions, demo environments, or academic collaborations, please contact:

Carlos Suárez - 🎓 Universidad del Cauca 

📧 csuarez@unicauca.edu.co

