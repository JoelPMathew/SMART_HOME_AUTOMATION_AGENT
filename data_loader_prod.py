"""
Enhanced Data Loader with Kaggle API Integration
Loads and preprocesses multiple smart home energy datasets
"""

import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional

try:
    import kaggle
    KAGGLE_AVAILABLE = True
except ImportError:
    KAGGLE_AVAILABLE = False

from config import DATASETS, DATA_PATHS

logger = logging.getLogger(__name__)

class KaggleDataLoader:
    """
    Production-grade Kaggle dataset downloader
    Strictly adheres to Kaggle API specifications
    """
    
    def __init__(self):
        self.authenticated = False
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Kaggle API"""
        if not KAGGLE_AVAILABLE:
            logger.warning("Kaggle library not installed. Install: pip install kaggle")
            return
        
        try:
            # Kaggle API requires ~/.kaggle/kaggle.json
            kaggle.api.authenticate()
            self.authenticated = True
            logger.info("✓ Kaggle authentication successful")
        except Exception as e:
            logger.error(f"Kaggle authentication failed: {e}")
            logger.info("Configure: kaggle config set --competition-data path -q")
    
    def download_dataset(self, dataset_name: str, path: str, unzip: bool = True):
        """
        Download dataset from Kaggle
        
        Args:
            dataset_name: Kaggle dataset identifier (e.g., 'uciml/electric-power-consumption-data-set')
            path: Local path to save
            unzip: Automatically unzip downloaded files
        """
        if not self.authenticated or not KAGGLE_AVAILABLE:
            logger.warning(f"Cannot download {dataset_name}: Kaggle not available")
            return
        
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Downloading {dataset_name}...")
            kaggle.api.dataset_download_files(
                dataset_name,
                path=path,
                unzip=unzip
            )
            logger.info(f"✓ Dataset saved to {path}")
        except Exception as e:
            logger.error(f"Download failed for {dataset_name}: {e}")
    
    def load_uci_household_power(self, reload: bool = False) -> Optional[pd.DataFrame]:
        """
        UCI Household Electric Power Consumption Dataset
        Contains: voltage, global intensity, sub metering data
        """
        dataset_name = DATASETS['uci_household']
        path = DATA_PATHS['uci_household']
        
        if reload or not Path(path).exists():
            self.download_dataset(dataset_name, path)
        
        try:
            file_path = os.path.join(path, 'household_power_consumption.txt')
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            df = pd.read_csv(
                file_path,
                sep=';',
                na_values=['?'],
                parse_dates={'datetime': ['Date', 'Time']},
                infer_datetime_format=True,
                low_memory=False
            )
            
            # Replace missing values
            df.fillna(df.mean(numeric_only=True), inplace=True)
            
            logger.info(f"UCI Household Power: {len(df)} records, {df.shape[1]} features")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load UCI data: {e}")
            return None
    
    def load_london_smart_meter(self, reload: bool = False) -> Optional[pd.DataFrame]:
        """
        UK Smart Meter Dataset (London)
        Contains: household energy usage at 30-minute intervals
        """
        dataset_name = DATASETS['london_smart_meter']
        path = DATA_PATHS['london_smart_meter']
        
        if reload or not Path(path).exists():
            self.download_dataset(dataset_name, path)
        
        try:
            file_path = os.path.join(path, 'household_energy_data.csv')
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            df = pd.read_csv(
                file_path,
                parse_dates=['timestamp']
            )
            
            df.fillna(df.mean(numeric_only=True), inplace=True)
            
            logger.info(f"London Smart Meter: {len(df)} records")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load London data: {e}")
            return None
    
    def load_smart_home_energy(self, reload: bool = False) -> Optional[pd.DataFrame]:
        """
        Smart Home Energy Consumption Dataset
        Contains: appliance-level energy usage with weather data
        """
        dataset_name = DATASETS['smart_home_energy']
        path = DATA_PATHS['smart_home_energy']
        
        if reload or not Path(path).exists():
            self.download_dataset(dataset_name, path)
        
        try:
            file_path = os.path.join(path, 'energydata_complete.csv')
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            df = pd.read_csv(
                file_path,
                parse_dates=['date']
            )
            
            df.fillna(df.mean(numeric_only=True), inplace=True)
            
            logger.info(f"Smart Home Energy: {len(df)} records")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load Smart Home data: {e}")
            return None
    
    def load_iot_sensor_data(self, reload: bool = False) -> Optional[pd.DataFrame]:
        """
        IoT Sensor Network Dataset
        Contains: multi-sensor readings from smart home
        """
        dataset_name = DATASETS['iot_sensors']
        path = DATA_PATHS['iot_sensors']
        
        if reload or not Path(path).exists():
            self.download_dataset(dataset_name, path)
        
        try:
            file_path = os.path.join(path, 'sensor_data.csv')
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            df = pd.read_csv(
                file_path,
                parse_dates=['timestamp']
            )
            
            df.fillna(df.mean(numeric_only=True), inplace=True)
            
            logger.info(f"IoT Sensor Data: {len(df)} records")
            return df
        
        except Exception as e:
            logger.error(f"Failed to load IoT data: {e}")
            return None
    
    def load_all_datasets(self, reload: bool = False) -> Dict[str, Optional[pd.DataFrame]]:
        """Load all available datasets"""
        datasets = {
            "uci_household": self.load_uci_household_power(reload),
            "london_smart_meter": self.load_london_smart_meter(reload),
            "smart_home_energy": self.load_smart_home_energy(reload),
            "iot_sensors": self.load_iot_sensor_data(reload)
        }
        
        loaded = sum(1 for v in datasets.values() if v is not None)
        logger.info(f"Loaded {loaded}/{len(datasets)} datasets")
        return datasets


class DataPreprocessor:
    """
    Preprocess time-series data for ML models
    Handles missing values, outliers, and normalization
    """
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, method: str = 'forward_fill') -> pd.DataFrame:
        """
        Handle missing values in time-series
        
        Args:
            df: Input dataframe
            method: 'forward_fill', 'interpolate', or 'mean'
        """
        if method == 'forward_fill':
            return df.fillna(method='ffill').fillna(method='bfill')
        elif method == 'interpolate':
            return df.interpolate(method='linear')
        else:  # mean
            return df.fillna(df.mean(numeric_only=True))
    
    @staticmethod
    def remove_outliers(df: pd.DataFrame, column: str, threshold: float = 3) -> pd.DataFrame:
        """Remove outliers using Z-score method"""
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        return df[z_scores < threshold]
    
    @staticmethod
    def normalize_energy_values(df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """
        Normalize energy values to 0-1 range
        Useful for neural networks
        """
        df_norm = df.copy()
        for col in columns:
            if col in df_norm.columns:
                min_val = df_norm[col].min()
                max_val = df_norm[col].max()
                df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val + 1e-8)
        return df_norm
    
    @staticmethod
    def create_features(df: pd.DataFrame, datetime_col: str) -> pd.DataFrame:
        """
        Create temporal features from datetime column
        Hour, day of week, month, etc.
        """
        df = df.copy()
        if datetime_col not in df.columns:
            return df
        
        df['hour'] = pd.to_datetime(df[datetime_col]).dt.hour
        df['day_of_week'] = pd.to_datetime(df[datetime_col]).dt.dayofweek
        df['day_of_month'] = pd.to_datetime(df[datetime_col]).dt.day
        df['month'] = pd.to_datetime(df[datetime_col]).dt.month
        df['quarter'] = pd.to_datetime(df[datetime_col]).dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        return df
    
    @staticmethod
    def create_lag_features(df: pd.DataFrame, column: str, lags: list = [1, 24, 168]) -> pd.DataFrame:
        """Create lag features for time-series (1h, 24h, 7d)"""
        df = df.copy()
        for lag in lags:
            df[f'{column}_lag_{lag}'] = df[column].shift(lag)
        return df.dropna()


if __name__ == "__main__":
    # Test data loading
    loader = KaggleDataLoader()
    
    print("Loading datasets...")
    datasets = loader.load_all_datasets()
    
    for name, df in datasets.items():
        if df is not None:
            print(f"\n{name}:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)[:5]}...")
            print(f"  Sample:\n{df.head()}")
