# Smart Home AI Agent - Production-Grade Deployment Guide

## 🏠 Project Overview

**Smart Home AI Agent** is a production-grade intelligent home automation system that combines:
- **Real-time device control** via MQTT
- **AI-powered optimization** with context awareness
- **Energy forecasting** using Prophet/LSTM
- **Natural language commands** with LLM integration
- **Professional dashboard** with Streamlit
- **RESTful API** with Flask

### Key Features

✅ **Context-Aware Automation**
- Time-based rules (peak hours, off-peak optimization)
- Occupancy detection
- Weather-aware adjustments
- Comfort constraints enforcement

✅ **Energy Optimization**
- 20% peak-hour load reduction
- Autonomous decision making
- Historical pattern analysis
- Predictive peak detection

✅ **Multi-Channel Control**
- Natural language commands
- Direct device control
- Quick action modes (Goodnight, Away, Morning)
- RESTful API endpoints

✅ **Advanced Forecasting**
- 24-168 hour energy predictions
- Prophet time-series model
- LSTM deep learning support
- Confidence intervals

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repo_url>
cd smart-home-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
python main.py setup
```

### 2. Configuration

Edit `.env` with your settings:

```bash
# MQTT (your broker address)
MQTT_BROKER=localhost
MQTT_PORT=1883

# APIs
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
OPENWEATHER_API_KEY=...

# Kaggle (for datasets)
KAGGLE_USERNAME=...
KAGGLE_KEY=...
```

### 3. Start the System

**Option A: Development Mode**
```bash
python main.py dev
# Starts both backend and frontend automatically
```

**Option B: Manual Start**

Terminal 1 - Backend:
```bash
python main.py backend --port 5000
```

Terminal 2 - Frontend:
```bash
python main.py frontend --port 8501
```

### 4. Access the Dashboard

- **Frontend Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:5000/health
- **Swagger UI**: http://localhost:5000/docs (optional)

---

## 📁 Project Structure

```
smart-home-agent/
├── config.py                 # Configuration management
├── agent_prod.py            # Main AI agent (Rules + LLM)
├── app_prod.py              # Flask REST API backend
├── ui_streamlit.py          # Streamlit dashboard frontend
├── mqtt_client.py           # MQTT communication
├── data_loader_prod.py      # Kaggle data integration
├── forecasting_prod.py      # Energy forecasting (Prophet/LSTM)
├── main.py                  # Deployment orchestrator
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
├── README.md               # This file
│
├── data/                   # Datasets (auto-created)
├── logs/                   # Application logs
├── models/                 # Trained models
└── cache/                  # Forecast cache

```

---

## 🔌 API Endpoints Reference

### Health & Status
```
GET  /health              # System health check
GET  /status              # Comprehensive status
```

### Device Control
```
POST /device/control      # Control single device
GET  /devices             # List all devices
GET  /devices/<name>      # Get device state
```

### Commands & Automation
```
POST /command             # Process natural language
POST /optimize            # Get optimization decisions
```

### Energy & Forecasting
```
GET  /forecast            # Energy forecast (24-168h)
GET  /forecast/peak-probability  # Peak load probability
```

### Analytics
```
GET  /history/decisions   # Decision history
GET  /admin/config        # System configuration
```

### Webhooks
```
POST /webhook/mqtt        # MQTT event integration
```

---

## 🎯 Core Components

### 1. SmartHomeAgent (agent_prod.py)

**Intelligent orchestrator** combining rules and LLM reasoning:

```python
agent = SmartHomeAgent()

# User commands
agent.process_command("turn on lights")
agent.process_command("set thermostat to 22")

# Autonomous optimization
decisions = agent.get_optimization_decision()

# Decision tracking
history = agent.get_decision_history(limit=100)
```

### 2. RulesEngine (in agent_prod.py)

**Context-aware automation rules**:
- Peak hour reduction (5 PM - 9 PM): 20% load cut
- Occupancy-based control
- Weather adaptations
- Comfort constraints

### 3. EnergyForecaster (forecasting_prod.py)

**Time-series forecasting**:
```python
forecaster = EnergyForecaster(model_type='prophet')
forecaster.train()  # or train(df)

# Generate forecast
forecast = forecaster.forecast_energy(periods=24)

# Peak probability
prob = forecaster.get_peak_probability()
```

### 4. MQTTClient (mqtt_client.py)

**Device communication**:
```python
client = MQTTClient()
client.connect()

# Publish command
client.publish("home/lights", "on")

# Get states
states = client.get_device_states()
```

### 5. Flask API (app_prod.py)

**RESTful backend**:
```python
# Rate limiting: 30 requests/minute
@app.route("/command", methods=["POST"])
def handle_command():
    # Process command
    # Return JSON response
```

### 6. Streamlit UI (ui_streamlit.py)

**Interactive dashboard** with pages:
- Dashboard: System overview
- Device Control: Individual & quick actions
- Energy Analytics: Forecasts & trends
- Command Center: Natural language input
- Optimization: Auto-optimization & history
- Settings: Configuration

---

## 📊 Data Sources & APIs

### Kaggle Datasets (via Kaggle API)

```python
from data_loader_prod import KaggleDataLoader

loader = KaggleDataLoader()
datasets = loader.load_all_datasets()

# Available:
# - UCI Household Power (electric-power-consumption-data-set)
# - London Smart Meter (household-energy-usage-dataset)
# - Smart Home Energy (smart-home-energy-consumption)
# - IoT Sensor Network (iot-sensor-network-dataset)
```

### External APIs

- **OpenWeather API**: Current weather & forecasts
- **OpenAI/Deepseek**: Natural language processing
- **MQTT Broker**: Real-time device communication

---

## 🧠 AI/ML Architecture

### Forecasting Models

**Prophet** (Default)
- Seasonal decomposition
- Holiday effects
- Automatic changepoint detection
- 95% confidence intervals

**LSTM** (Optional)
- Deep learning for complex patterns
- Custom sequence length
- Faster training on GPUs

### Rules Engine

**Hierarchical Decision Making**:
1. Peak hour rules (highest priority)
2. Occupancy-based rules
3. Weather adjustments
4. Comfort constraints
5. Off-peak optimization

### LLM Integration

**Natural Language Processing**:
- Deepseek Chat (recommended)
- OpenAI GPT-3.5/4 (fallback)
- System prompt with device/context info
- Temperature: 0.5 (balanced reasoning)

---

## 🔐 Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t smart-home-agent:latest .

# Run container
docker run -p 5000:5000 -p 8501:8501 \
  -e MQTT_BROKER=broker.local \
  -e OPENAI_API_KEY=sk-... \
  smart-home-agent:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_PORT=5000
  
  frontend:
    build: .
    ports:
      - "8501:8501"
    command: streamlit run ui_streamlit.py
  
  mosquitto:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
```

### Environment Variables

```bash
# MQTT
MQTT_BROKER=mqtt.local
MQTT_PORT=1883
MQTT_USERNAME=user
MQTT_PASSWORD=pass

# APIs
OPENAI_API_KEY=sk-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx
OPENWEATHER_API_KEY=xxxxx

# System
FORECAST_PERIODS=24
FORECAST_MODEL=prophet
AUTO_OPTIMIZATION=True
OCCUPANCY_DETECTION=True
WEATHER_AWARE=True
```

---

## 📈 Monitoring & Logging

### Application Logs
```bash
# Monitor in real-time
tail -f logs/smart_home_agent.log

# View with filtering
grep "ERROR" logs/smart_home_agent.log
```

### Metrics to Track
- MQTT connection uptime
- API response times
- Forecast accuracy
- Device control success rate
- Decision execution frequency

### Status Endpoint
```bash
curl http://localhost:5000/status | jq
```

---

## 🧪 Testing & Validation

### Run Tests
```bash
python main.py test
# or
pytest tests/ -v
```

### Test Coverage
- Unit tests for each component
- Integration tests for workflows
- API endpoint tests
- Device control simulation

### Example Test
```python
def test_device_control():
    agent = SmartHomeAgent()
    result = agent.control_device("lights", "on")
    assert result is not None
    assert "lights" in result
```

---

## 🔧 Troubleshooting

### MQTT Connection Failed
```bash
# Check broker
mosquitto_sub -h localhost -p 1883 -t "home/#"

# Verify configuration
cat .env | grep MQTT
```

### API Rate Limited
```
HTTP 429 - Too Many Requests
Wait 60 seconds or check rate limit configuration
```

### Forecast Generation Slow
```python
# Use cache
forecast = forecaster.forecast_energy(periods=24, use_cache=True)

# Reduce periods for faster response
forecast = forecaster.forecast_energy(periods=6)
```

### LLM Integration Not Working
```bash
# Check API key
echo $OPENAI_API_KEY

# Verify connection
python -c "import openai; print(openai.__version__)"
```

---

## 📚 API Examples

### Command Examples

```bash
# Turn on lights
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/json" \
  -d '{"command": "turn on lights"}'

# Get forecast
curl http://localhost:5000/forecast?periods=24

# Get optimization
curl -X POST http://localhost:5000/optimize \
  -d '{"auto_apply": true}'

# Device control
curl -X POST http://localhost:5000/device/control \
  -H "Content-Type: application/json" \
  -d '{"device": "thermostat", "action": "22"}'
```

---

## 🎓 Learning Resources

- **MQTT**: https://mqtt.org
- **Prophet**: https://facebook.github.io/prophet/
- **Streamlit**: https://docs.streamlit.io
- **Flask**: https://flask.palletsprojects.com
- **OpenAI API**: https://platform.openai.com/docs

---

## 📝 Configuration Reference

All settings in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| MQTT_BROKER | localhost | MQTT broker host |
| FORECAST_PERIODS | 24 | Hours to forecast |
| FORECAST_MODEL | prophet | Model type (prophet/lstm) |
| AUTO_OPTIMIZATION | True | Enable autonomous decisions |
| OCCUPANCY_DETECTION | True | Use motion sensors |
| WEATHER_AWARE | True | Weather-based adjustments |
| API_TIMEOUT | 10 | API request timeout (sec) |

---

## 🚀 Advanced Features

### Custom Rules
```python
def add_custom_rule(context: Dict) -> Dict[str, str]:
    decisions = {}
    if context['temperature'] > 25:
        decisions['hvac'] = 'cool'
    return decisions
```

### Database Integration
```python
# SQLAlchemy integration for decision history
from models import DecisionHistory
db.session.add(DecisionHistory(...))
db.session.commit()
```

### External Integrations
- Home Assistant API
- Google Smart Home
- Alexa Skills
- IFTTT Webhooks

---

## 📞 Support & Issues

For issues, create a GitHub issue with:
1. Error logs
2. Configuration (without secrets)
3. Steps to reproduce
4. Expected vs actual behavior

---

## 📄 License

Production-grade smart home automation system.
Built for research and educational purposes.

---

## 🎯 Roadmap

- [ ] Multi-zone support
- [ ] Voice integration (Alexa, Google)
- [ ] Mobile app (iOS/Android)
- [ ] Advanced ML models (XGBoost, ensemble)
- [ ] Database persistence (PostgreSQL)
- [ ] Kubernetes deployment
- [ ] Real-time monitoring dashboard
- [ ] Automated testing CI/CD

---

**Created:** December 2024
**Version:** 1.0.0
**Status:** Production-Ready ✅
