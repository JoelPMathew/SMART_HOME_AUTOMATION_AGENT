"""
Production-Grade MQTT Client
Handles device communication and state management
"""

import logging
import paho.mqtt.client as mqtt
import json
import os
from typing import Dict, Callable, Optional
from collections import defaultdict

from config import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPICS

logger = logging.getLogger(__name__)

class MQTTClient:
    """
    MQTT client for smart home device communication
    Handles subscriptions, publishing, and state management
    """
    
    def __init__(self):
        self.broker = MQTT_BROKER
        self.port = MQTT_PORT
        self.username = MQTT_USERNAME
        self.password = MQTT_PASSWORD
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1 if hasattr(mqtt, 'CallbackAPIVersion') else None)
        self.devices = defaultdict(dict)
        self.connected = False
        self.callbacks = {}
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        logger.info(f"MQTT Client initialized for {self.broker}:{self.port}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("✓ Connected to MQTT Broker")
            
            # Subscribe to all topics
            for device_name, topic in MQTT_TOPICS.items():
                if "+" in topic:
                    # Wildcard subscription
                    client.subscribe(topic)
                    logger.info(f"  Subscribed to {topic}")
                else:
                    client.subscribe(topic)
                    logger.info(f"  Subscribed to {topic}")
        else:
            self.connected = False
            logger.error(f"Failed to connect, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection (rc={rc})")
        else:
            logger.info("Cleanly disconnected from MQTT Broker")
    
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8', errors='replace')
            
            # Extract device name from topic (e.g., "home/lights" -> "lights")
            parts = topic.split('/')
            device_name = parts[-1] if parts else 'unknown'
            
            # Try to parse as JSON
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                payload_data = payload
            
            # Store state
            self.devices[device_name] = {
                'value': payload_data,
                'topic': topic,
                'timestamp': msg.timestamp
            }
            
            logger.debug(f"Received: {device_name} = {payload_data}")
            
            # Trigger callbacks
            if device_name in self.callbacks:
                for callback in self.callbacks[device_name]:
                    try:
                        callback(device_name, payload_data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
        
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    def connect(self, reconnect: bool = True):
        """
        Connect to MQTT broker
        
        Args:
            reconnect: Enable automatic reconnection
        """
        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            self.client.connect(self.broker, self.port, keepalive=60)
            
            if reconnect:
                self.client.reconnect_delay_set(min_delay=1, max_delay=32)
            
            self.client.loop_start()
            logger.info(f"MQTT connection initiated to {self.broker}:{self.port}")
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT disconnected")
        except Exception as e:
            logger.error(f"Disconnection error: {e}")
    
    def publish(self, topic: str, message: any, retain: bool = False, qos: int = 1) -> bool:
        """
        Publish message to topic
        
        Args:
            topic: MQTT topic
            message: Message payload
            retain: Retain message on broker
            qos: Quality of Service (0, 1, 2)
        
        Returns:
            Success status
        """
        try:
            if isinstance(message, dict):
                payload = json.dumps(message)
            else:
                payload = str(message)
            
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Publish failed (rc={result.rc})")
                return False
        
        except Exception as e:
            logger.error(f"Publish error: {e}")
            return False
    
    def subscribe(self, topic: str, callback: Optional[Callable] = None, qos: int = 1):
        """
        Subscribe to topic with optional callback
        
        Args:
            topic: MQTT topic (supports wildcards)
            callback: Function to call on message
            qos: Quality of Service
        """
        try:
            self.client.subscribe(topic, qos=qos)
            
            if callback:
                device_name = topic.split('/')[-1]
                if device_name not in self.callbacks:
                    self.callbacks[device_name] = []
                self.callbacks[device_name].append(callback)
            
            logger.info(f"Subscribed to {topic}")
        
        except Exception as e:
            logger.error(f"Subscription error: {e}")
    
    def get_device_state(self, device_name: str) -> Optional[any]:
        """Get device current state"""
        if device_name in self.devices:
            return self.devices[device_name]['value']
        return None
    
    def get_device_states(self) -> Dict[str, any]:
        """Get all device states"""
        return {
            name: data['value']
            for name, data in self.devices.items()
        }
    
    def wait_for_state(self, device_name: str, timeout: int = 5) -> Optional[any]:
        """Wait for device to report state"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            state = self.get_device_state(device_name)
            if state is not None:
                return state
            time.sleep(0.1)
        
        return None
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected
    
    def get_connection_status(self) -> Dict[str, any]:
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'broker': self.broker,
            'port': self.port,
            'devices_count': len(self.devices),
            'devices': list(self.devices.keys())
        }

if __name__ == "__main__":
    # Test MQTT client
    client = MQTTClient()
    
    try:
        print("Connecting to MQTT...")
        client.connect()
        
        print("Publishing test message...")
        client.publish("home/test", {"message": "Hello from Python"})
        
        print("Device states:")
        import time
        time.sleep(2)
        print(client.get_device_states())
        
        print("Status:")
        print(client.get_connection_status())
    
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()
