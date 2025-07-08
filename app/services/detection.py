from ..core.ml_engine import MLService
from ..utils.log_parser import parse_snort_log
from ..models.models import Alert
from ..db.database import SessionLocal

class DetectionService:
    def __init__(self):
        self.ml_service = MLService()

    def process_snort_log(self, log_line: str):
        parsed_data = parse_snort_log(log_line)
        if parsed_data:
            # Perform ML inference
            # For now, let's assume parsed_data can be directly used by MLService.predict
            # In a real scenario, you'd extract/transform features from parsed_data
            # Example: features = [parsed_data["source_port"], parsed_data["destination_port"], ...]
            # For this example, we'll just use dummy features for prediction
            dummy_features = [0.0] * self.ml_service.input_size # Replace with actual feature extraction
            ml_prediction = self.ml_service.predict(dummy_features)

            # Save alert to database
            db = SessionLocal()
            try:
                alert = Alert(
                    source_ip=parsed_data.get("source_ip"),
                    destination_ip=parsed_data.get("destination_ip"),
                    source_port=parsed_data.get("source_port"),
                    destination_port=parsed_data.get("destination_port"),
                    protocol=parsed_data.get("protocol"),
                    alert_message=parsed_data.get("alert_message"),
                    ml_prediction=ml_prediction,
                    snort_sid=parsed_data.get("snort_sid")
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)
                print(f"Saved alert to DB: {alert.alert_message} (ML Prediction: {ml_prediction})")
            except Exception as e:
                db.rollback()
                print(f"Error saving alert to DB: {e}")
            finally:
                db.close()
        else:
            print(f"Could not parse log line: {log_line}")

# This would be called by snort_wrapper.py or a dedicated log processing worker
# Example usage (for testing):
if __name__ == "__main__":
    detection_service = DetectionService()
    # Simulate a Snort log line
    sample_log_line = '[**] [1:2000000:1] ET POLICY Outbound SSH Connection [**] [Classification: Attempted Administrator Privilege Gain] [Priority: 1] {TCP} 192.168.1.100:54321 -> 1.2.3.4:22'
    detection_service.process_snort_log(sample_log_line)
