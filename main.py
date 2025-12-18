"""
Smart Home AI Agent - Main Entry Point
Production-grade deployment orchestrator
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartHomeDeployer:
    """Deployment orchestrator for Smart Home AI Agent"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or '.env'
        self.project_root = Path(__file__).parent
        
    def setup_environment(self):
        """Setup environment and dependencies"""
        logger.info("Setting up environment...")
        
        # Create necessary directories
        dirs = ['data', 'logs', 'models', 'cache']
        for dir_name in dirs:
            Path(dir_name).mkdir(exist_ok=True)
            logger.info(f"✓ Directory '{dir_name}' ready")
        
        # Load environment variables
        if Path(self.config_path).exists():
            logger.info(f"Loading configuration from {self.config_path}")
        else:
            logger.warning(f"No .env file found at {self.config_path}")
            self._create_sample_env()
        
        logger.info("✓ Environment setup complete")
    
    def _create_sample_env(self):
        """Create sample .env file"""
        sample_env = """# Smart Home AI Agent Configuration

# ===== MQTT Configuration =====
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# ===== Flask Configuration =====
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=False
API_TIMEOUT=10

# ===== API Keys =====
OPENAI_API_KEY=your_api_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENWEATHER_API_KEY=your_weather_key_here

# ===== Kaggle Configuration =====
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_key

# ===== Agent Settings =====
FORECAST_PERIODS=24
FORECAST_MODEL=prophet
OCCUPANCY_DETECTION=True
WEATHER_AWARE=True
AUTO_OPTIMIZATION=True
"""
        Path(self.config_path).write_text(sample_env)
        logger.info(f"✓ Created sample .env at {self.config_path}")
        logger.info("⚠️  Please update .env with your configuration")
    
    def start_backend(self, port: int = 5000):
        """Start Flask backend"""
        logger.info(f"Starting Flask backend on port {port}...")
        
        try:
            from app_prod import app
            from config import FLASK_HOST, FLASK_DEBUG
            
            logger.info(f"✓ Backend running at http://{FLASK_HOST}:{port}")
            app.run(host=FLASK_HOST, port=port, debug=FLASK_DEBUG, use_reloader=False)
        
        except Exception as e:
            logger.error(f"Backend startup failed: {e}")
            sys.exit(1)
    
    def start_frontend(self, port: int = 8501):
        """Start Streamlit frontend"""
        logger.info(f"Starting Streamlit frontend on port {port}...")
        
        try:
            import subprocess
            subprocess.run([
                'streamlit', 'run',
                'ui_streamlit.py',
                '--server.port', str(port),
                '--server.address', 'localhost'
            ])
        
        except Exception as e:
            logger.error(f"Frontend startup failed: {e}")
            sys.exit(1)
    
    def train_models(self):
        """Train forecasting models"""
        logger.info("Training forecasting models...")
        
        try:
            from data_loader_prod import KaggleDataLoader
            from forecasting_prod import EnergyForecaster
            
            # Load data
            logger.info("Loading data...")
            loader = KaggleDataLoader()
            datasets = loader.load_all_datasets()
            
            # Train forecaster
            logger.info("Training forecaster...")
            forecaster = EnergyForecaster(model_type='prophet')
            
            if datasets['smart_home_energy'] is not None:
                forecaster.train(datasets['smart_home_energy'])
            else:
                forecaster.train()  # Use synthetic data
            
            logger.info("✓ Models trained successfully")
        
        except Exception as e:
            logger.error(f"Model training failed: {e}")
    
    def run_tests(self):
        """Run test suite"""
        logger.info("Running tests...")
        
        try:
            import subprocess
            result = subprocess.run(['pytest', 'tests/', '-v'], capture_output=True)
            print(result.stdout.decode())
            
            if result.returncode == 0:
                logger.info("✓ All tests passed")
            else:
                logger.error("✗ Some tests failed")
        
        except Exception as e:
            logger.warning(f"Test execution failed: {e}")
    
    def deploy_docker(self):
        """Deploy using Docker"""
        logger.info("Building Docker container...")
        
        try:
            import subprocess
            subprocess.run(['docker', 'build', '-t', 'smart-home-agent:latest', '.'])
            logger.info("✓ Docker container built")
        
        except Exception as e:
            logger.error(f"Docker build failed: {e}")
    
    def show_status(self):
        """Show system status"""
        logger.info("System Status:")
        logger.info("=" * 50)
        
        try:
            from agent_prod import SmartHomeAgent
            
            agent = SmartHomeAgent()
            status = agent.get_agent_status()
            
            logger.info(f"Status: {status['status']}")
            logger.info(f"Devices: {status['device_count']}")
            logger.info(f"Recent Decisions: {status['recent_decisions']}")
            logger.info(f"MQTT Connected: {status['mqtt_connected']}")
            logger.info(f"Forecaster Ready: {status['forecaster_ready']}")
            logger.info(f"LLM Available: {status['llm_available']}")
        
        except Exception as e:
            logger.error(f"Status check failed: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Smart Home AI Agent')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Setup environment')
    
    # Backend command
    backend_parser = subparsers.add_parser('backend', help='Start Flask backend')
    backend_parser.add_argument('--port', type=int, default=5000, help='Backend port')
    
    # Frontend command
    frontend_parser = subparsers.add_parser('frontend', help='Start Streamlit frontend')
    frontend_parser.add_argument('--port', type=int, default=8501, help='Frontend port')
    
    # Train command
    subparsers.add_parser('train', help='Train models')
    
    # Test command
    subparsers.add_parser('test', help='Run tests')
    
    # Docker command
    subparsers.add_parser('docker', help='Build Docker container')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Development mode
    dev_parser = subparsers.add_parser('dev', help='Run in development mode')
    dev_parser.add_argument('--skip-backend', action='store_true', help='Skip backend')
    
    args = parser.parse_args()
    
    deployer = SmartHomeDeployer()
    
    if args.command == 'setup':
        deployer.setup_environment()
    
    elif args.command == 'backend':
        deployer.start_backend(args.port)
    
    elif args.command == 'frontend':
        deployer.start_frontend(args.port)
    
    elif args.command == 'train':
        deployer.train_models()
    
    elif args.command == 'test':
        deployer.run_tests()
    
    elif args.command == 'docker':
        deployer.deploy_docker()
    
    elif args.command == 'status':
        deployer.show_status()
    
    elif args.command == 'dev':
        logger.info("Starting in development mode...")
        deployer.setup_environment()
        
        import threading
        
        # Start backend in separate thread
        if not args.skip_backend:
            backend_thread = threading.Thread(target=deployer.start_backend, daemon=True)
            backend_thread.start()
            
            import time
            time.sleep(2)
        
        # Start frontend
        deployer.start_frontend()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
