# Configuration file for Smart Home AI Agent
# Production-grade settings and environment defaults

import os
from dotenv import load_dotenv

load_dotenv()

# ===== MQTT Configuration =====
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TOPICS = {
    "lights": "home/lights",
    "thermostat": "home/thermostat",
    "hvac": "home/hvac",
    "water_heater": "home/water_heater",
    "plugs": "home/plugs",
    "sensors": "home/sensors/+"
}

# ===== Flask Configuration =====
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 10))

# ===== Streamlit Configuration =====
STREAMLIT_THEME = "light"
STREAMLIT_PAGE_TITLE = "Smart Home AI Agent"
STREAMLIT_LAYOUT = "wide"

# ===== API Keys =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")

# ===== Dataset Configuration =====
DATASETS = {
    "uci_household": "uciml/electric-power-consumption-data-set",
    "london_smart_meter": "zoya77/london-smartgrid-household-energy-usage-dataset",
    "smart_meter_generic": "ziya07/smart-meter-electricity-consumption-dataset",
    "smart_home_energy": "mexwell/smart-home-energy-consumption",
    "iot_sensors": "ziya07/iot-sensor-network-dataset"
}

DATA_PATHS = {
    "uci_household": "data/uci_household/",
    "london_smart_meter": "data/london_smart_meter/",
    "smart_meter_generic": "data/smart_meter_generic/",
    "smart_home_energy": "data/smart_home_energy/",
    "iot_sensors": "data/iot_sensors/"
}

# ===== Forecasting Configuration =====
FORECAST_PERIODS = int(os.getenv("FORECAST_PERIODS", 24))
FORECAST_MODEL = os.getenv("FORECAST_MODEL", "prophet")  # prophet or lstm
MIN_ENERGY_THRESHOLD = float(os.getenv("MIN_ENERGY_THRESHOLD", 500))  # watts
MAX_ENERGY_THRESHOLD = float(os.getenv("MAX_ENERGY_THRESHOLD", 5000))  # watts

# ===== Agent Configuration =====
AGENT_DECISION_INTERVAL = int(os.getenv("AGENT_DECISION_INTERVAL", 300))  # seconds
AGENT_RULES_ENGINE = os.getenv("AGENT_RULES_ENGINE", "hybrid")  # rule-based or hybrid
OCCUPANCY_DETECTION = os.getenv("OCCUPANCY_DETECTION", "True").lower() == "true"
WEATHER_AWARE = os.getenv("WEATHER_AWARE", "True").lower() == "true"
AUTO_OPTIMIZATION = os.getenv("AUTO_OPTIMIZATION", "True").lower() == "true"

# ===== Logging Configuration =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/smart_home_agent.log")

# ===== Device Definitions =====
DEVICES = {
    "lights": {
        "control_type": "binary",
        "states": ["on", "off"],
        "power_rating": 100,  # watts
        "priority": "low"
    },
    "thermostat": {
        "control_type": "continuous",
        "min_temp": 15,
        "max_temp": 30,
        "power_rating": 3000,
        "priority": "high"
    },
    "hvac": {
        "control_type": "binary",
        "states": ["on", "off"],
        "power_rating": 5000,
        "priority": "high"
    },
    "water_heater": {
        "control_type": "binary",
        "states": ["on", "off"],
        "power_rating": 4500,
        "priority": "medium"
    },
    "plugs": {
        "control_type": "binary",
        "states": ["on", "off"],
        "power_rating": 2000,
        "priority": "low"
    }
}

# ===== Optimization Rules =====
OPTIMIZATION_RULES = {
    "peak_hours": {
        "start": 17,
        "end": 21,
        "target_reduction": 0.20  # 20% reduction
    },
    "off_peak_hours": {
        "start": 23,
        "end": 7,
        "allow_charging": True
    },
    "comfort_constraints": {
        "min_light_level": 200,  # lux
        "max_temp_variance": 2,  # degrees
        "humidity_range": (30, 60)  # percent
    }
}

import logging
logging.getLogger(__name__).info("Configuration loaded successfully")
