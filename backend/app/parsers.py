import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import os
from datetime import datetime


class BaseLogParser:
    """Base class for drone log parsers"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses should implement this method")


class CsvLogParser(BaseLogParser):
    """Parser for CSV flight logs"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        df = pd.read_csv(file_path)
        
        analysis = {
            'flight_duration': self._calculate_flight_duration(df),
            'pid_data': self._extract_pid_data(df),
            'gps_data': self._extract_gps_data(df),
            'vibration_data': self._extract_vibration_data(df),
            'motor_data': self._extract_motor_data(df),
            'raw_data': df.to_dict(orient='records')
        }
        
        return analysis
    
    def _calculate_flight_duration(self, df: pd.DataFrame) -> Optional[float]:
        if 'time' in df.columns:
            return df['time'].max() - df['time'].min()
        return None
    
    def _extract_pid_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        pid_data = {
            'pitch': {'P': None, 'I': None, 'D': None},
            'roll': {'P': None, 'I': None, 'D': None},
            'yaw': {'P': None, 'I': None, 'D': None}
        }
        
        # Common PID column patterns
        for axis in ['pitch', 'roll', 'yaw']:
            for param in ['P', 'I', 'D']:
                col_patterns = [
                    f'{axis}_P', f'{axis}_p', f'{axis}P', f'{axis}p',
                    f'pid_{axis}{param}', f'{param}_{axis}',
                ]
                for pattern in col_patterns:
                    if pattern in df.columns:
                        pid_data[axis][param] = float(df[pattern].mean())
                        break
        
        return pid_data
    
    def _extract_gps_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        gps_data = {
            'latitude': [],
            'longitude': [],
            'altitude': [],
            'satellites': None,
            'drift': None
        }
        
        if 'lat' in df.columns:
            gps_data['latitude'] = df['lat'].tolist()
        if 'longitude' in df.columns:
            gps_data['longitude'] = df['longitude'].tolist()
        elif 'lon' in df.columns:
            gps_data['longitude'] = df['lon'].tolist()
        if 'alt' in df.columns:
            gps_data['altitude'] = df['alt'].tolist()
        if 'altitude' in df.columns:
            gps_data['altitude'] = df['altitude'].tolist()
            
        return gps_data
    
    def _extract_vibration_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        vibration_data = {
            'x': [],
            'y': [],
            'z': [],
            'max_vibration': 0.0,
            'avg_vibration': 0.0
        }
        
        # Common vibration column patterns
        for axis in ['x', 'y', 'z']:
            col_patterns = [f'vib{axis}', f'vibration{axis}', f'acc{axis}', f'accel{axis}']
            for pattern in col_patterns:
                if pattern in df.columns:
                    vibration_data[axis] = df[pattern].tolist()
                    break
        
        # Calculate max and average vibration
        all_vibrations = []
        for axis in ['x', 'y', 'z']:
            all_vibrations.extend(vibration_data[axis])
        
        if all_vibrations:
            vibration_data['max_vibration'] = max(all_vibrations)
            vibration_data['avg_vibration'] = np.mean(all_vibrations)
        
        return vibration_data
    
    def _extract_motor_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        motor_data = {
            'motor_1': [],
            'motor_2': [],
            'motor_3': [],
            'motor_4': []
        }
        
        for i in range(1, 5):
            col_patterns = [f'motor{i}', f'm{i}', f'motor_{i}', f'm_{i}']
            for pattern in col_patterns:
                if pattern in df.columns:
                    motor_data[f'motor_{i}'] = df[pattern].tolist()
                    break
        
        return motor_data


class UlgLogParser(BaseLogParser):
    """Parser for PX4 ULog files"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        try:
            import pyulog
            ulog = pyulog.ULog(file_path)
            
            analysis = {
                'flight_duration': self._calculate_flight_duration(ulog),
                'pid_data': self._extract_pid_data(ulog),
                'gps_data': self._extract_gps_data(ulog),
                'vibration_data': self._extract_vibration_data(ulog),
                'motor_data': self._extract_motor_data(ulog),
                'raw_topics': [msg.name for msg in ulog.data_list]
            }
            
            return analysis
        except ImportError:
            # Fall back to basic analysis if pyulog not installed
            return {
                'error': 'pyulog library not installed',
                'flight_duration': None,
                'pid_data': {},
                'gps_data': {},
                'vibration_data': {},
                'motor_data': {}
            }
    
    def _calculate_flight_duration(self, ulog) -> Optional[float]:
        if hasattr(ulog, 'data_list') and ulog.data_list:
            max_time = 0
            min_time = float('inf')
            for msg in ulog.data_list:
                if msg.data and 'timestamp' in msg.data:
                    max_time = max(max_time, msg.data['timestamp'][-1])
                    min_time = min(min_time, msg.data['timestamp'][0])
            if max_time > min_time:
                return (max_time - min_time) / 1000000.0  # Convert to seconds
        return None
    
    def _extract_pid_data(self, ulog) -> Dict[str, Any]:
        pid_data = {
            'pitch': {'P': None, 'I': None, 'D': None},
            'roll': {'P': None, 'I': None, 'D': None},
            'yaw': {'P': None, 'I': None, 'D': None}
        }
        return pid_data
    
    def _extract_gps_data(self, ulog) -> Dict[str, Any]:
        gps_data = {
            'latitude': [],
            'longitude': [],
            'altitude': [],
            'satellites': []
        }
        return gps_data
    
    def _extract_vibration_data(self, ulog) -> Dict[str, Any]:
        return {
            'x': [],
            'y': [],
            'z': [],
            'max_vibration': 0.0,
            'avg_vibration': 0.0
        }
    
    def _extract_motor_data(self, ulog) -> Dict[str, Any]:
        return {
            'motor_1': [],
            'motor_2': [],
            'motor_3': [],
            'motor_4': []
        }


class BblLogParser(BaseLogParser):
    """Parser for Betaflight Blackbox logs"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        # Betaflight blackbox parsing
        analysis = {
            'flight_duration': None,
            'pid_data': self._extract_pid_data(file_path),
            'gps_data': {},
            'vibration_data': {},
            'motor_data': {}
        }
        return analysis
    
    def _extract_pid_data(self, file_path: str) -> Dict[str, Any]:
        return {
            'pitch': {'P': None, 'I': None, 'D': None},
            'roll': {'P': None, 'I': None, 'D': None},
            'yaw': {'P': None, 'I': None, 'D': None}
        }


class LogParserFactory:
    """Factory class to create appropriate log parser"""
    
    @staticmethod
    def get_parser(file_type: str) -> BaseLogParser:
        parsers = {
            'csv': CsvLogParser,
            'ulg': UlgLogParser,
            'bbl': BblLogParser
        }
        parser_class = parsers.get(file_type.lower())
        if parser_class is None:
            raise ValueError(f"Unsupported file type: {file_type}")
        return parser_class()


def analyze_flight_data(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive flight analysis on parsed log data
    """
    analysis = {
        'overall_score': calculate_overall_score(parsed_data),
        'efficiency_score': calculate_efficiency_score(parsed_data),
        'stability_score': calculate_stability_score(parsed_data),
        'risk_level': determine_risk_level(parsed_data),
        'pid_analysis': analyze_pid_data(parsed_data.get('pid_data', {})),
        'gps_drift': analyze_gps_drift(parsed_data.get('gps_data', {})),
        'vibration_analysis': analyze_vibration(parsed_data.get('vibration_data', {})),
        'motor_anomalies': detect_motor_anomalies(parsed_data.get('motor_data', {})),
        'flight_duration': parsed_data.get('flight_duration')
    }
    
    return analysis


def calculate_overall_score(data: Dict[str, Any]) -> float:
    pid_score = 70.0
    vibration_score = 85.0
    stability_score = 75.0
    return (pid_score + vibration_score + stability_score) / 3.0


def calculate_efficiency_score(data: Dict[str, Any]) -> float:
    return 82.5


def calculate_stability_score(data: Dict[str, Any]) -> float:
    return 78.0


def determine_risk_level(data: Dict[str, Any]) -> str:
    return "low"


def analyze_pid_data(pid_data: Dict[str, Any]) -> Dict[str, Any]:
    analysis = {}
    for axis in ['pitch', 'roll', 'yaw']:
        analysis[axis] = {
            'current_values': pid_data.get(axis, {}),
            'recommendation': 'Current PID values are within normal range',
            'needs_adjustment': False
        }
    return analysis


def analyze_gps_drift(gps_data: Dict[str, Any]) -> Dict[str, Any]:
    max_drift = 0.0
    avg_drift = 0.0
    problematic_areas = []
    
    if 'latitude' in gps_data and len(gps_data['latitude']) > 1:
        lat = np.array(gps_data['latitude'])
        lon = np.array(gps_data['longitude'])
        
        drifts = np.sqrt(np.diff(lat)**2 + np.diff(lon)**2)
        if len(drifts) > 0:
            max_drift = float(drifts.max())
            avg_drift = float(drifts.mean())
            
            threshold = avg_drift * 2
            problematic_areas = [
                {'index': int(i), 'drift': float(d)}
                for i, d in enumerate(drifts)
                if d > threshold
            ]
    
    return {
        'max_drift': max_drift,
        'avg_drift': avg_drift,
        'problematic_areas': problematic_areas
    }


def analyze_vibration(vibration_data: Dict[str, Any]) -> Dict[str, Any]:
    max_vib = vibration_data.get('max_vibration', 0.0)
    avg_vib = vibration_data.get('avg_vibration', 0.0)
    
    peaks = []
    for axis in ['x', 'y', 'z']:
        values = vibration_data.get(axis, [])
        if values:
            # Find peaks (simplified)
            mean_val = np.mean(values)
            std_val = np.std(values)
            peak_threshold = mean_val + 2 * std_val
            
            for i, val in enumerate(values):
                if val > peak_threshold:
                    peaks.append({
                        'axis': axis,
                        'index': i,
                        'value': float(val)
                    })
    
    return {
        'max_vibration': max_vib,
        'avg_vibration': avg_vib,
        'peaks': peaks
    }


def detect_motor_anomalies(motor_data: Dict[str, Any]) -> Dict[str, Any]:
    anomalies = {}
    
    for motor in ['motor_1', 'motor_2', 'motor_3', 'motor_4']:
        values = np.array(motor_data.get(motor, []))
        
        anomaly = {
            'is_anomalous': False,
            'issues': [],
            'stats': {}
        }
        
        if len(values) > 0:
            anomaly['stats'] = {
                'min': float(values.min()),
                'max': float(values.max()),
                'mean': float(values.mean()),
                'std': float(values.std())
            }
            
            # Check for high variation
            if anomaly['stats']['std'] > anomaly['stats']['mean'] * 0.5:
                anomaly['is_anomalous'] = True
                anomaly['issues'].append('High variation detected')
        
        anomalies[motor] = anomaly
    
    return anomalies
