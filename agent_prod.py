"""
Production-Grade Smart Home AI Agent
Handles intelligent automation, optimization, and context-aware decisions
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import requests
from collections import defaultdict

# LLM Integration
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from mqtt_client import MQTTClient
from forecasting_prod import EnergyForecaster
from config import *

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RulesEngine:
    """Intelligent rule-based decision engine"""
    
    def __init__(self, device_config: Dict):
        self.device_config = device_config
        self.device_states = defaultdict(dict)
        self.historical_data = defaultdict(list)
        
    def evaluate(self, context: Dict) -> Dict[str, str]:
        """
        Evaluate automation rules based on current context
        
        Args:
            context: {
                'time': datetime,
                'temperature': float,
                'humidity': float,
                'occupancy': bool,
                'energy_consumed': float,
                'weather': str,
                'device_states': Dict,
                'forecast': List[Dict]
            }
        
        Returns:
            decisions: {'device_name': 'action'}
        """
        decisions = {}
        current_hour = context.get('time', datetime.now()).hour
        
        # Rule 1: Peak Hour Energy Reduction (5 PM - 9 PM)
        if OPTIMIZATION_RULES['peak_hours']['start'] <= current_hour < OPTIMIZATION_RULES['peak_hours']['end']:
            decisions.update(self._apply_peak_hour_rules(context))
        
        # Rule 2: Occupancy-Based Automation
        if OCCUPANCY_DETECTION and context.get('occupancy'):
            decisions.update(self._apply_occupancy_rules(context))
        
        # Rule 3: Weather-Aware Adjustments
        if WEATHER_AWARE:
            decisions.update(self._apply_weather_rules(context))
        
        # Rule 4: Comfort Constraints
        decisions.update(self._apply_comfort_rules(context))
        
        # Rule 5: Off-Peak Optimization
        if OPTIMIZATION_RULES['off_peak_hours']['start'] <= current_hour or current_hour < OPTIMIZATION_RULES['off_peak_hours']['end']:
            decisions.update(self._apply_offpeak_rules(context))
        
        logger.info(f"Rules evaluation generated {len(decisions)} decisions")
        return decisions
    
    def _apply_peak_hour_rules(self, context: Dict) -> Dict[str, str]:
        """Reduce energy consumption during peak hours"""
        decisions = {}
        target_reduction = OPTIMIZATION_RULES['peak_hours']['target_reduction']
        current_load = context.get('energy_consumed', 0)
        
        if current_load > MIN_ENERGY_THRESHOLD:
            # Reduce HVAC to eco mode
            decisions['hvac'] = 'eco_mode'
            # Reduce water heater
            decisions['water_heater'] = 'low'
            # Optimize lighting
            decisions['lights'] = 'dim:70'  # 70% brightness
        
        return decisions
    
    def _apply_occupancy_rules(self, context: Dict) -> Dict[str, str]:
        """Adjust devices based on occupancy"""
        decisions = {}
        occupancy = context.get('occupancy', False)
        
        if occupancy:
            # Ensure comfort when occupied
            decisions['lights'] = 'on:comfort'
            decisions['hvac'] = 'auto'
            decisions['thermostat'] = '22'  # 22°C comfort temperature
        else:
            # Energy saving when unoccupied
            decisions['lights'] = 'off'
            decisions['hvac'] = 'low'
            decisions['thermostat'] = '18'  # 18°C eco temperature
        
        return decisions
    
    def _apply_weather_rules(self, context: Dict) -> Dict[str, str]:
        """Adjust based on weather conditions"""
        decisions = {}
        weather = context.get('weather', 'clear').lower()
        
        if 'rain' in weather or 'snow' in weather:
            decisions['water_heater'] = 'on'  # Ensure hot water availability
        
        if 'sunny' in weather:
            # Leverage natural light
            decisions['lights'] = 'off'
        
        if 'cold' in weather or 'snow' in weather:
            decisions['thermostat'] = '23'  # Increase temperature
        elif 'hot' in weather:
            decisions['thermostat'] = '21'  # Decrease temperature
        
        return decisions
    
    def _apply_comfort_rules(self, context: Dict) -> Dict[str, str]:
        """Maintain comfort constraints"""
        decisions = {}
        temperature = context.get('temperature', 22)
        humidity = context.get('humidity', 50)
        
        min_comfort_temp = 20
        max_comfort_temp = 24
        
        if temperature < min_comfort_temp:
            decisions['thermostat'] = 'increase'
        elif temperature > max_comfort_temp:
            decisions['thermostat'] = 'decrease'
        
        if humidity < OPTIMIZATION_RULES['comfort_constraints']['humidity_range'][0]:
            decisions['humidifier'] = 'on'
        elif humidity > OPTIMIZATION_RULES['comfort_constraints']['humidity_range'][1]:
            decisions['dehumidifier'] = 'on'
        
        return decisions
    
    def _apply_offpeak_rules(self, context: Dict) -> Dict[str, str]:
        """Optimize during off-peak hours"""
        decisions = {}
        
        # Allow water heater charging in off-peak
        if OPTIMIZATION_RULES['off_peak_hours']['allow_charging']:
            decisions['water_heater'] = 'charge'
        
        # Schedule background tasks
        decisions['plugs'] = 'schedule:laundry'
        
        return decisions


class ContextBuilder:
    """Builds rich context from multiple data sources"""
    
    def __init__(self, mqtt_client: MQTTClient, forecaster: EnergyForecaster):
        self.mqtt_client = mqtt_client
        self.forecaster = forecaster
        self.weather_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def build(self) -> Dict[str, Any]:
        """Build comprehensive context"""
        context = {
            'time': datetime.now(),
            'temperature': self._get_temperature(),
            'humidity': self._get_humidity(),
            'occupancy': self._detect_occupancy(),
            'energy_consumed': self._get_current_energy(),
            'weather': self._fetch_weather(),
            'device_states': self.mqtt_client.get_device_states(),
            'forecast': self.forecaster.forecast_energy(periods=24),
            'historical_avg_energy': self._get_historical_average(),
            'peak_prediction': self._predict_peak()
        }
        return context
    
    def _get_temperature(self) -> float:
        """Get current temperature from sensors"""
        states = self.mqtt_client.get_device_states()
        temp_data = states.get('temperature_sensor', None)
        return self._to_float(temp_data, 22.0)
    
    def _get_humidity(self) -> float:
        """Get current humidity from sensors"""
        states = self.mqtt_client.get_device_states()
        humidity_data = states.get('humidity_sensor', None)
        return self._to_float(humidity_data, 50.0)
    
    def _detect_occupancy(self) -> bool:
        """Detect occupancy using motion sensors and energy patterns"""
        states = self.mqtt_client.get_device_states()
        motion = states.get('motion_sensor', None)

        motion_val = False
        if motion is not None:
            if isinstance(motion, dict):
                motion_val = bool(motion.get('value'))
            else:
                motion_val = bool(motion)

        # Also check if lights or devices are in use
        device_usage = False
        for device in ['lights', 'thermostat']:
            dev = states.get(device, None)
            if isinstance(dev, dict):
                state = dev.get('state') or dev.get('value')
            else:
                state = dev
            if isinstance(state, str) and state.lower() == 'on':
                device_usage = True
                break

        return motion_val or device_usage
    
    def _get_current_energy(self) -> float:
        """Get current energy consumption"""
        states = self.mqtt_client.get_device_states()
        energy_meter = states.get('energy_meter', None)
        return self._to_float(energy_meter, 0.0)
    
    def _fetch_weather(self) -> str:
        """Fetch weather data from OpenWeather API"""
        if not OPENWEATHER_API_KEY:
            return "unknown"
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q=London&appid={OPENWEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['weather'][0]['main'].lower()
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
        
        return "clear"

    def _to_float(self, val: any, default: float) -> float:
        """Coerce various payload formats to float safely."""
        try:
            if val is None:
                return default
            if isinstance(val, dict):
                # Look for common keys
                for key in ('value', 'reading', 'payload'):
                    if key in val:
                        return float(val[key])
                return default
            return float(val)
        except Exception:
            return default
    
    def _get_historical_average(self) -> float:
        """Calculate historical average energy consumption"""
        # Would integrate with database/time-series store
        return 1500.0  # Mock value
    
    def _predict_peak(self) -> bool:
        """Predict if peak load is approaching"""
        forecast = self.forecaster.forecast_energy(periods=4)
        if forecast:
            future_avg = np.mean([f['yhat'] for f in forecast])
            return future_avg > MAX_ENERGY_THRESHOLD
        return False


class SmartHomeAgent:
    """
    Production-grade Smart Home AI Agent
    Orchestrates decisions from rules engine and LLM
    """
    
    def __init__(self):
        self.mqtt_client = MQTTClient()
        self.forecaster = EnergyForecaster()
        self.rules_engine = RulesEngine(DEVICES)
        self.context_builder = ContextBuilder(self.mqtt_client, self.forecaster)
        
        # Initialize LLM if available
        if OPENAI_AVAILABLE and (OPENAI_API_KEY or DEEPSEEK_API_KEY):
            api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
            base_url = DEEPSEEK_BASE_URL if DEEPSEEK_API_KEY else None
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None
        
        self.decision_history = []
        logger.info("SmartHomeAgent initialized")
    
    def process_command(self, command: str, user_context: Optional[Dict] = None) -> str:
        """
        Process user commands with context awareness
        
        Args:
            command: User's natural language command
            user_context: Optional context about the user
        
        Returns:
            Response string with execution details
        """
        logger.info(f"Processing command: {command}")
        
        try:
            # Build rich context
            context = self.context_builder.build()
            context.update(user_context or {})
            
            # Check if command matches device control pattern
            device_response = self._try_device_control(command, context)
            if device_response:
                return device_response
            
            # Check if command is informational
            info_response = self._try_information_query(command, context)
            if info_response:
                return info_response
            
            # Use LLM for complex reasoning
            if self.client:
                return self._process_with_llm(command, context)
            else:
                return "Command understood but LLM unavailable"
        
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            return f"Error processing command: {str(e)}"
    
    def _try_device_control(self, command: str, context: Dict) -> Optional[str]:
        """Attempt to parse and execute device control commands"""
        command_lower = command.lower()
        
        # Pattern: "turn [on/off] [device]"
        if "turn" in command_lower:
            parts = command_lower.split()
            action = parts[1] if len(parts) > 1 else None
            device = parts[2] if len(parts) > 2 else None
            
            if action in ['on', 'off'] and device:
                return self.control_device(device, action)
        
        # Pattern: "set [device] to [value]"
        if "set" in command_lower:
            parts = command_lower.split()
            if "to" in parts:
                to_idx = parts.index("to")
                device = parts[1] if len(parts) > 1 else None
                value = parts[to_idx + 1] if len(parts) > to_idx + 1 else None
                
                if device and value:
                    return self.control_device(device, value)
        
        return None
    
    def _try_information_query(self, command: str, context: Dict) -> Optional[str]:
        """Handle informational queries"""
        command_lower = command.lower()
        
        if "forecast" in command_lower or "energy" in command_lower:
            forecast = self.forecaster.forecast_energy(periods=12)
            avg_forecast = np.mean([f['yhat'] for f in forecast])
            return f"Energy forecast (next 12h avg): {avg_forecast:.0f}W"
        
        if "weather" in command_lower:
            weather = self.context_builder._fetch_weather()
            return f"Current weather: {weather}"
        
        if "temperature" in command_lower or "temp" in command_lower:
            temp = context.get('temperature', 22.0)
            return f"Current temperature: {temp:.1f}°C"
        
        if "occupancy" in command_lower:
            occupancy = context.get('occupancy', False)
            return f"Occupancy status: {'Occupied' if occupancy else 'Unoccupied'}"
        
        if "device" in command_lower or "status" in command_lower:
            devices = context.get('device_states', {})
            return json.dumps(devices, indent=2)
        
        return None
    
    def control_device(self, device: str, action: str) -> str:
        """Execute device control via MQTT"""
        try:
            topic = MQTT_TOPICS.get(device, f"home/{device}")
            self.mqtt_client.publish(topic, action)
            
            decision_record = {
                'timestamp': datetime.now().isoformat(),
                'device': device,
                'action': action,
                'source': 'user_command'
            }
            self.decision_history.append(decision_record)
            
            logger.info(f"Device control executed: {device} -> {action}")
            return f"✓ {device} set to {action}"
        except Exception as e:
            logger.error(f"Device control error: {e}")
            return f"✗ Failed to control {device}: {str(e)}"
    
    def _process_with_llm(self, command: str, context: Dict) -> str:
        """Use LLM for intelligent reasoning"""
        try:
            system_prompt = f"""
You are an intelligent smart home automation agent. You help users control their home devices
and optimize energy consumption. Current context:
- Time: {context['time'].strftime('%Y-%m-%d %H:%M:%S')}
- Temperature: {context['temperature']:.1f}°C
- Humidity: {context['humidity']:.1f}%
- Occupancy: {'Yes' if context['occupancy'] else 'No'}
- Current Energy: {context['energy_consumed']:.0f}W
- Weather: {context['weather']}
- Predicted Peak: {'Yes' if context['peak_prediction'] else 'No'}

Available devices: lights, thermostat, hvac, water_heater, plugs
Available actions: on, off, increase, decrease, auto, eco_mode

Respond concisely with specific recommendations.
"""
            
            response = self.client.chat.completions.create(
                model="deepseek-chat" if DEEPSEEK_API_KEY else "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            result = response.choices[0].message.content
            logger.info(f"LLM response: {result}")
            return result
        
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            return "Could not process with AI reasoning"
    
    def get_optimization_decision(self) -> Dict[str, str]:
        """
        Autonomous decision making for energy optimization
        Called periodically by background process
        """
        context = self.context_builder.build()
        decisions = self.rules_engine.evaluate(context)
        
        # Apply decisions
        for device, action in decisions.items():
            try:
                self.control_device(device, action)
                decision_record = {
                    'timestamp': datetime.now().isoformat(),
                    'device': device,
                    'action': action,
                    'source': 'autonomous_optimization'
                }
                self.decision_history.append(decision_record)
            except Exception as e:
                logger.error(f"Failed to apply decision {device}->{action}: {e}")
        
        return decisions
    
    def get_decision_history(self, limit: int = 100) -> List[Dict]:
        """Get recent decision history"""
        return self.decision_history[-limit:]
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        context = self.context_builder.build()
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'context': context,
            'device_count': len(context['device_states']),
            'recent_decisions': len(self.decision_history),
            'mqtt_connected': self.mqtt_client.is_connected(),
            'forecaster_ready': self.forecaster.model is not None,
            'llm_available': self.client is not None
        }

if __name__ == "__main__":
    # Test the agent
    agent = SmartHomeAgent()
    
    # Test commands
    print("1. Turn on lights:")
    print(agent.process_command("turn on lights"))
    
    print("\n2. Set thermostat to 23°C:")
    print(agent.process_command("set thermostat to 23"))
    
    print("\n3. Energy forecast:")
    print(agent.process_command("what is the energy forecast"))
    
    print("\n4. Agent status:")
    print(json.dumps(agent.get_agent_status(), indent=2, default=str))
