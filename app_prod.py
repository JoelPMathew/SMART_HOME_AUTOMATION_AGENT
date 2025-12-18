"""
Production-Grade Flask Backend for Smart Home AI Agent
RESTful API with comprehensive endpoints and error handling
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import threading
import traceback
from datetime import datetime
from typing import Dict, Any

from agent_prod import SmartHomeAgent
from mqtt_client import MQTTClient
from forecasting_prod import EnergyForecaster
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, API_TIMEOUT

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)
limiter = Limiter(app=app, key_func=get_remote_address)

# Initialize components
agent = SmartHomeAgent()
mqtt_client = MQTTClient()
forecaster = EnergyForecaster()

# Background MQTT thread
def start_mqtt_background():
    """Start MQTT client in background"""
    try:
        mqtt_client.connect()
        logger.info("✓ MQTT connected and running in background")
    except Exception as e:
        logger.error(f"MQTT connection error: {e}")
        traceback.print_exc()

mqtt_thread = threading.Thread(target=start_mqtt_background, daemon=True)
mqtt_thread.start()

# ===== HEALTH & STATUS ENDPOINTS =====

@app.route("/health", methods=["GET"])
@limiter.limit("60/minute")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200

@app.route("/status", methods=["GET"])
@limiter.limit("30/minute")
def get_status():
    """Comprehensive system status"""
    try:
        status = agent.get_agent_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== COMMAND ENDPOINTS =====

@app.route("/command", methods=["POST"])
@limiter.limit("30/minute")
def handle_command():
    """
    Process user command
    
    Request body:
    {
        "command": "turn on lights",
        "context": {...optional context...}
    }
    """
    try:
        data = request.get_json(force=True)
        command = data.get("command", "").strip()
        context = data.get("context", {})
        
        if not command:
            return jsonify({"error": "command field is required"}), 400
        
        logger.info(f"Processing command: {command}")
        response = agent.process_command(command, context)
        
        return jsonify({
            "success": True,
            "command": command,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except ValueError as e:
        logger.error(f"Invalid JSON: {e}")
        return jsonify({"error": "Invalid JSON format"}), 400
    except Exception as e:
        logger.error(f"Command error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/device/control", methods=["POST"])
@limiter.limit("60/minute")
def control_device():
    """
    Direct device control
    
    Request body:
    {
        "device": "lights",
        "action": "on"
    }
    """
    try:
        data = request.get_json(force=True)
        device = data.get("device", "").strip().lower()
        action = data.get("action", "").strip().lower()
        
        if not device or not action:
            return jsonify({
                "error": "device and action fields are required"
            }), 400
        
        response = agent.control_device(device, action)
        
        return jsonify({
            "success": True,
            "device": device,
            "action": action,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Device control error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== DEVICE ENDPOINTS =====

@app.route("/devices", methods=["GET"])
@limiter.limit("30/minute")
def get_devices():
    """Get all device states"""
    try:
        devices = mqtt_client.get_device_states()
        return jsonify({
            "devices": devices,
            "count": len(devices),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Get devices error: {e}")
        return jsonify({
            "error": "Unable to fetch device states",
            "message": str(e)
        }), 500

@app.route("/devices/<device_name>", methods=["GET"])
@limiter.limit("60/minute")
def get_device_state(device_name: str):
    """Get specific device state"""
    try:
        states = mqtt_client.get_device_states()
        state = states.get(device_name.lower())
        
        if state is None:
            return jsonify({
                "error": f"Device '{device_name}' not found"
            }), 404
        
        return jsonify({
            "device": device_name,
            "state": state,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Get device state error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== FORECAST ENDPOINTS =====

@app.route("/forecast", methods=["GET"])
@limiter.limit("20/minute")
def get_forecast():
    """
    Get energy forecast
    
    Query parameters:
    - periods: forecast periods (default: 24)
    - format: 'detailed' or 'summary' (default: detailed)
    """
    try:
        periods = request.args.get("periods", 24, type=int)
        periods = max(1, min(periods, 168))  # 1-168 hours
        
        format_type = request.args.get("format", "detailed")
        
        forecast = forecaster.forecast_energy(periods=periods)
        
        if format_type == "summary":
            avg = sum(f['yhat'] for f in forecast) / len(forecast)
            return jsonify({
                "forecast_summary": {
                    "average": avg,
                    "min": min(f['yhat'] for f in forecast),
                    "max": max(f['yhat'] for f in forecast),
                    "periods": periods,
                    "confidence": forecaster.get_forecast_confidence()
                },
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "forecast": forecast,
                "periods": len(forecast),
                "confidence": forecaster.get_forecast_confidence(),
                "timestamp": datetime.now().isoformat()
            }), 200
    
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return jsonify({
            "error": "Forecast service unavailable",
            "message": str(e)
        }), 500

@app.route("/forecast/peak-probability", methods=["GET"])
@limiter.limit("20/minute")
def get_peak_probability():
    """Get probability of peak load"""
    try:
        threshold = request.args.get("threshold", None, type=float)
        
        probability = forecaster.get_peak_probability(threshold)
        
        return jsonify({
            "peak_probability": probability,
            "threshold": threshold,
            "interpretation": "high" if probability > 0.7 else "medium" if probability > 0.3 else "low",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Peak probability error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== OPTIMIZATION ENDPOINTS =====

@app.route("/optimize", methods=["POST"])
@limiter.limit("10/minute")
def get_optimization():
    """
    Trigger optimization decisions
    
    Request body:
    {
        "auto_apply": true/false
    }
    """
    try:
        data = request.get_json(force=True) if request.data else {}
        auto_apply = data.get("auto_apply", False)
        
        decisions = agent.get_optimization_decision()
        
        return jsonify({
            "decisions": decisions,
            "auto_applied": auto_apply,
            "count": len(decisions),
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== HISTORY & ANALYTICS ENDPOINTS =====

@app.route("/history/decisions", methods=["GET"])
@limiter.limit("30/minute")
def get_decision_history():
    """Get decision history"""
    try:
        limit = request.args.get("limit", 100, type=int)
        limit = max(1, min(limit, 1000))
        
        history = agent.get_decision_history(limit=limit)
        
        return jsonify({
            "decisions": history,
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== ERROR HANDLERS =====

@app.errorhandler(429)
def ratelimit_handler(e):
    """Rate limit exceeded"""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later."
    }), 429

@app.errorhandler(404)
def not_found(e):
    """404 Not found"""
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """500 Internal server error"""
    logger.error(f"Internal error: {e}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

# ===== WEBHOOK ENDPOINTS =====

@app.route("/webhook/mqtt", methods=["POST"])
@limiter.limit("100/minute")
def mqtt_webhook():
    """
    MQTT event webhook
    For integration with external systems
    """
    try:
        data = request.get_json(force=True)
        topic = data.get("topic")
        payload = data.get("payload")
        
        logger.info(f"MQTT webhook: {topic} = {payload}")
        
        # Could trigger agent logic here
        return jsonify({
            "success": True,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== ADMIN ENDPOINTS =====

@app.route("/admin/config", methods=["GET"])
@limiter.limit("10/minute")
def get_config():
    """Get system configuration (admin only)"""
    # In production, add authentication
    try:
        from config import DEVICES, MQTT_TOPICS, OPTIMIZATION_RULES
        return jsonify({
            "devices": DEVICES,
            "topics": MQTT_TOPICS,
            "rules": OPTIMIZATION_RULES
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== MAIN =====

if __name__ == "__main__":
    logger.info(f"Starting Smart Home AI Agent Backend")
    logger.info(f"Listening on {FLASK_HOST}:{FLASK_PORT}")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False,
        threaded=True
    )
