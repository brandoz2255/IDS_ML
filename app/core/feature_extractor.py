import numpy as np
from typing import Dict, List, Any
import re
from collections import Counter

class NetworkFeatureExtractor:
    """Extract features from network traffic data for ML models"""
    
    def __init__(self):
        self.port_classes = {
            'web': [80, 443, 8080, 8443],
            'email': [25, 110, 143, 993, 995],
            'ftp': [20, 21],
            'ssh': [22],
            'dns': [53],
            'dhcp': [67, 68],
            'telnet': [23],
            'snmp': [161, 162]
        }
    
    def extract_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract comprehensive features from alert data"""
        features = []
        
        # Basic network features
        features.extend(self._extract_ip_features(alert_data))
        features.extend(self._extract_port_features(alert_data))
        features.extend(self._extract_protocol_features(alert_data))
        features.extend(self._extract_message_features(alert_data))
        features.extend(self._extract_temporal_features(alert_data))
        features.extend(self._extract_behavioral_features(alert_data))
        
        return features
    
    def _extract_ip_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract IP-based features"""
        features = []
        
        source_ip = alert_data.get('source_ip', '0.0.0.0')
        dest_ip = alert_data.get('destination_ip', '0.0.0.0')
        
        # IP address entropy and characteristics
        features.append(self._calculate_ip_entropy(source_ip))
        features.append(self._calculate_ip_entropy(dest_ip))
        features.append(float(self._is_private_ip(source_ip)))
        features.append(float(self._is_private_ip(dest_ip)))
        features.append(float(self._is_multicast_ip(source_ip)))
        features.append(float(self._is_multicast_ip(dest_ip)))
        
        return features
    
    def _extract_port_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract port-based features"""
        features = []
        
        src_port = alert_data.get('source_port', 0)
        dst_port = alert_data.get('destination_port', 0)
        
        # Port characteristics
        features.append(float(src_port))
        features.append(float(dst_port))
        features.append(float(src_port < 1024))  # Privileged port
        features.append(float(dst_port < 1024))  # Privileged port
        features.append(float(self._get_port_class(src_port)))
        features.append(float(self._get_port_class(dst_port)))
        
        return features
    
    def _extract_protocol_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract protocol-based features"""
        features = []
        
        protocol = alert_data.get('protocol', 'UNKNOWN').upper()
        
        # Protocol one-hot encoding
        protocols = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS']
        for p in protocols:
            features.append(float(protocol == p))
        
        return features
    
    def _extract_message_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract features from alert message"""
        features = []
        
        message = alert_data.get('alert_message', '')
        
        # Message characteristics
        features.append(float(len(message)))
        features.append(float(len(message.split())))
        features.append(float(self._count_special_chars(message)))
        features.append(float('attack' in message.lower()))
        features.append(float('scan' in message.lower()))
        features.append(float('exploit' in message.lower()))
        
        return features
    
    def _extract_temporal_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract temporal features"""
        features = []
        
        # For now, use dummy temporal features
        # In practice, these would be derived from timestamp analysis
        features.append(0.0)  # Hour of day (normalized)
        features.append(0.0)  # Day of week
        features.append(0.0)  # Time since last alert from same source
        
        return features
    
    def _extract_behavioral_features(self, alert_data: Dict[str, Any]) -> List[float]:
        """Extract behavioral features"""
        features = []
        
        # Snort SID-based features
        snort_sid = alert_data.get('snort_sid', 0)
        features.append(float(snort_sid))
        features.append(float(snort_sid > 1000000))  # High SID indicator
        
        return features
    
    def _calculate_ip_entropy(self, ip: str) -> float:
        """Calculate entropy of IP address"""
        try:
            octets = ip.split('.')
            if len(octets) != 4:
                return 0.0
            
            # Calculate entropy based on octet distribution
            counter = Counter(octets)
            total = len(octets)
            entropy = 0.0
            
            for count in counter.values():
                p = count / total
                if p > 0:
                    entropy -= p * np.log2(p)
            
            return entropy
        except:
            return 0.0
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is in private ranges"""
        try:
            octets = [int(x) for x in ip.split('.')]
            if len(octets) != 4:
                return False
            
            # Private IP ranges
            if octets[0] == 10:
                return True
            if octets[0] == 172 and 16 <= octets[1] <= 31:
                return True
            if octets[0] == 192 and octets[1] == 168:
                return True
            
            return False
        except:
            return False
    
    def _is_multicast_ip(self, ip: str) -> bool:
        """Check if IP is multicast"""
        try:
            first_octet = int(ip.split('.')[0])
            return 224 <= first_octet <= 239
        except:
            return False
    
    def _get_port_class(self, port: int) -> int:
        """Get port class (0-7 for different service types)"""
        for i, (service, ports) in enumerate(self.port_classes.items()):
            if port in ports:
                return i
        return len(self.port_classes)  # Unknown service
    
    def _count_special_chars(self, text: str) -> int:
        """Count special characters in text"""
        special_chars = re.findall(r'[^a-zA-Z0-9\s]', text)
        return len(special_chars)