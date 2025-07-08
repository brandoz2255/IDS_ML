import redis
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from ..utils.logging import get_logger

logger = get_logger(__name__)

class RedisStreamClient:
    """Redis client for stream processing"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 db: int = 0,
                 password: str = None):
        
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')
        
        self.redis_client = None
        self.connect()
    
    def connect(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis", host=self.host, port=self.port)
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    def publish_alert(self, stream_name: str, alert_data: Dict[str, Any]) -> str:
        """Publish alert to Redis stream"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in alert_data:
                alert_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Convert to string format for Redis
            stream_data = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                          for k, v in alert_data.items()}
            
            message_id = self.redis_client.xadd(stream_name, stream_data)
            logger.info("Published alert to stream", 
                       stream=stream_name, 
                       message_id=message_id,
                       alert_id=alert_data.get('id'))
            return message_id
        except Exception as e:
            logger.error("Failed to publish alert", error=str(e))
            raise
    
    def consume_alerts(self, 
                      stream_name: str, 
                      consumer_group: str,
                      consumer_name: str,
                      count: int = 10,
                      block: int = 1000) -> List[Dict[str, Any]]:
        """Consume alerts from Redis stream"""
        try:
            # Create consumer group if it doesn't exist
            try:
                self.redis_client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
            
            # Read messages from stream
            messages = self.redis_client.xreadgroup(
                consumer_group,
                consumer_name,
                {stream_name: '>'},
                count=count,
                block=block
            )
            
            alerts = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    try:
                        # Parse message data
                        alert_data = {}
                        for key, value in fields.items():
                            try:
                                # Try to parse JSON
                                alert_data[key] = json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                alert_data[key] = value
                        
                        alert_data['_message_id'] = msg_id
                        alert_data['_stream'] = stream
                        alerts.append(alert_data)
                        
                        # Acknowledge message
                        self.redis_client.xack(stream_name, consumer_group, msg_id)
                        
                    except Exception as e:
                        logger.error("Failed to parse message", 
                                   message_id=msg_id, 
                                   error=str(e))
            
            return alerts
            
        except Exception as e:
            logger.error("Failed to consume alerts", error=str(e))
            return []
    
    def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """Get information about stream"""
        try:
            info = self.redis_client.xinfo_stream(stream_name)
            return {
                'length': info.get('length', 0),
                'first_entry': info.get('first-entry'),
                'last_entry': info.get('last-entry'),
                'groups': info.get('groups', 0)
            }
        except Exception as e:
            logger.error("Failed to get stream info", error=str(e))
            return {}
    
    def create_alert_queue(self, queue_name: str, alert_data: Dict[str, Any]):
        """Add alert to processing queue"""
        try:
            self.redis_client.lpush(queue_name, json.dumps(alert_data))
            logger.info("Added alert to queue", queue=queue_name)
        except Exception as e:
            logger.error("Failed to add alert to queue", error=str(e))
            raise
    
    def get_alert_from_queue(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Get alert from processing queue"""
        try:
            result = self.redis_client.brpop(queue_name, timeout=timeout)
            if result:
                _, alert_json = result
                return json.loads(alert_json)
            return None
        except Exception as e:
            logger.error("Failed to get alert from queue", error=str(e))
            return None
    
    def set_cache(self, key: str, value: Any, expire: int = 3600):
        """Set value in cache"""
        try:
            self.redis_client.setex(key, expire, json.dumps(value))
        except Exception as e:
            logger.error("Failed to set cache", error=str(e))
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Failed to get cache", error=str(e))
            return None
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Closed Redis connection")

# Global Redis client instance
redis_client = None

def get_redis_client() -> RedisStreamClient:
    """Get global Redis client instance"""
    global redis_client
    if redis_client is None:
        redis_client = RedisStreamClient()
    return redis_client