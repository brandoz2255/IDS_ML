import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import signal
import sys

from ..core.ml_engine import MLService
from ..core.feature_extractor import NetworkFeatureExtractor
from ..models.models import Alert
from ..db.database import SessionLocal
from ..utils.logging import get_logger
from ..monitoring.metrics import record_alert_processed, record_snort_alert
from .redis_client import get_redis_client

logger = get_logger(__name__)

class AlertProcessor:
    """Process alerts from stream in real-time"""
    
    def __init__(self):
        self.ml_service = MLService()
        self.feature_extractor = NetworkFeatureExtractor()
        self.redis_client = get_redis_client()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Stream and queue names
        self.raw_alerts_stream = "raw_alerts"
        self.processed_alerts_stream = "processed_alerts"
        self.ml_queue = "ml_processing_queue"
        
        # Consumer configuration
        self.consumer_group = "alert_processors"
        self.consumer_name = f"processor_{datetime.now().timestamp()}"
    
    async def start_processing(self):
        """Start the alert processing loop"""
        self.running = True
        logger.info("Starting alert processor", 
                   consumer_group=self.consumer_group,
                   consumer_name=self.consumer_name)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                await self._process_batch()
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
        except Exception as e:
            logger.error("Error in processing loop", error=str(e))
        finally:
            await self._cleanup()
    
    async def _process_batch(self):
        """Process a batch of alerts"""
        try:
            # Consume alerts from stream
            alerts = self.redis_client.consume_alerts(
                stream_name=self.raw_alerts_stream,
                consumer_group=self.consumer_group,
                consumer_name=self.consumer_name,
                count=10,
                block=1000
            )
            
            if alerts:
                logger.info(f"Processing {len(alerts)} alerts")
                
                # Process alerts in parallel
                tasks = [self._process_single_alert(alert) for alert in alerts]
                await asyncio.gather(*tasks, return_exceptions=True)
        
        except Exception as e:
            logger.error("Error processing batch", error=str(e))
    
    async def _process_single_alert(self, alert_data: Dict[str, Any]):
        """Process a single alert"""
        try:
            # Extract features
            features = self.feature_extractor.extract_features(alert_data)
            
            # Run ML inference in thread pool (CPU-bound operation)
            loop = asyncio.get_event_loop()
            ml_prediction = await loop.run_in_executor(
                self.executor, 
                self.ml_service.predict, 
                features
            )
            
            # Enhance alert data with ML prediction
            enhanced_alert = alert_data.copy()
            enhanced_alert['ml_prediction'] = ml_prediction
            enhanced_alert['ml_confidence'] = 0.85  # Placeholder
            enhanced_alert['features'] = features
            enhanced_alert['processed_timestamp'] = datetime.utcnow().isoformat()
            
            # Save to database
            await self._save_alert_to_db(enhanced_alert)
            
            # Publish to processed stream
            self.redis_client.publish_alert(
                self.processed_alerts_stream, 
                enhanced_alert
            )
            
            # Update metrics
            record_alert_processed(
                alert_type=alert_data.get('alert_message', 'unknown'),
                ml_prediction=ml_prediction
            )
            
            record_snort_alert()
            
            logger.info("Processed alert", 
                       alert_id=alert_data.get('id'),
                       ml_prediction=ml_prediction,
                       source_ip=alert_data.get('source_ip'))
        
        except Exception as e:
            logger.error("Error processing alert", 
                        alert_id=alert_data.get('id'),
                        error=str(e))
    
    async def _save_alert_to_db(self, alert_data: Dict[str, Any]):
        """Save processed alert to database"""
        try:
            db = SessionLocal()
            
            # Create Alert object
            alert = Alert(
                source_ip=alert_data.get('source_ip'),
                destination_ip=alert_data.get('destination_ip'),
                source_port=alert_data.get('source_port'),
                destination_port=alert_data.get('destination_port'),
                protocol=alert_data.get('protocol'),
                alert_message=alert_data.get('alert_message'),
                ml_prediction=alert_data.get('ml_prediction'),
                snort_sid=alert_data.get('snort_sid')
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            # Cache recent alert for quick access
            self.redis_client.set_cache(
                f"recent_alert_{alert.id}",
                alert_data,
                expire=3600
            )
            
        except Exception as e:
            logger.error("Error saving alert to database", error=str(e))
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up alert processor")
        self.executor.shutdown(wait=True)
        self.redis_client.close()

class AlertIngestionService:
    """Service for ingesting raw alerts into the stream"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.raw_alerts_stream = "raw_alerts"
    
    def ingest_snort_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Ingest Snort alert into processing stream"""
        try:
            # Add metadata
            alert_data['source'] = 'snort'
            alert_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            # Publish to stream
            message_id = self.redis_client.publish_alert(
                self.raw_alerts_stream,
                alert_data
            )
            
            logger.info("Ingested Snort alert", 
                       message_id=message_id,
                       source_ip=alert_data.get('source_ip'))
            return True
            
        except Exception as e:
            logger.error("Failed to ingest alert", error=str(e))
            return False
    
    def ingest_custom_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Ingest custom alert into processing stream"""
        try:
            # Add metadata
            alert_data['source'] = 'custom'
            alert_data['ingestion_timestamp'] = datetime.utcnow().isoformat()
            
            # Publish to stream
            message_id = self.redis_client.publish_alert(
                self.raw_alerts_stream,
                alert_data
            )
            
            logger.info("Ingested custom alert", 
                       message_id=message_id)
            return True
            
        except Exception as e:
            logger.error("Failed to ingest custom alert", error=str(e))
            return False

# Global services
alert_processor = None
ingestion_service = None

def get_alert_processor() -> AlertProcessor:
    """Get global alert processor instance"""
    global alert_processor
    if alert_processor is None:
        alert_processor = AlertProcessor()
    return alert_processor

def get_ingestion_service() -> AlertIngestionService:
    """Get global ingestion service instance"""
    global ingestion_service
    if ingestion_service is None:
        ingestion_service = AlertIngestionService()
    return ingestion_service