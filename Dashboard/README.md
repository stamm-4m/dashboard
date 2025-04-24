# ⚙️ STAMM Dashboard

STAMM is a comprehensive framework designed to facilitate the monitoring and maintenance of soft sensors powered by machine learning models. It ensures the reliability and accuracy of predictive systems by continuously tracking model performance, detecting drift, and enabling proactive maintenance. With a focus on industrial applications, STAMM helps optimise data-driven decision-making by providing real-time insights and automated adaptation mechanisms for evolving processes.

---

## 📁 Project Structure
```
MLops/ 
├── Dashboards/ # Main Dash web app 
│ ├── assets/ # Static assets (CSS, logos, icons) 
│ ├── callbacks/ # Interactive callbacks for app components 
│ ├── components/ # Reusable visual components 
│ ├── Data/ # Input/output datasets for visualizations 
│ ├── Drift_detectors/ # Algorithms for drift detection 
│ └── env/ # Environment variable files 
│ ├── InfluxDb/ # InfluxDB integration 
│    └── InfluxDBHandler.py # InfluxDB client and I/O functions 
│ ├── layouts/ # Dash layout components (page templates) 
| ├── pages/ # Route definitions for multi-page app 
| ├── Prediction/ # Model prediction logic 
| ├── utils/ # Utility functions 
│ ├── app.py # Entry point for running the Dash app 
| ├── config.py # Configuration file (InfluxDB, paths) 
| ├── requirements.txt # Python dependencies
| ├── save-prediction-influxDB.py # Script to log predictions in InfluxDB 
| ├── save-training-influxDB.py # Script to log training metadata 
```

---

## 🧰 Technologies Used

- **Python 3.8+**
- **Dash (by Plotly)** for building web dashboards
- **InfluxDB** for time-series storage of predictions and metrics
- **Pandas / NumPy / Scikit-learn** for data handling and model logic

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://gitlab.com/your-username/mlops-dashboard.git
cd mlops-dashboard
```
---

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.\.venv\Scripts\activate       # Windows
```
### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
### 4. Setup Environment Variables

Create a .env file in the root directory or inside Dashboards/env/ with the following structure:
```python

INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_organization
INFLUXDB_BUCKET=your_bucket_name
```
### ▶️ Running the App

To launch the Dash application locally:

```bash
python app.py
Visit http://127.0.0.1:8050 in your browser to view the app.
```