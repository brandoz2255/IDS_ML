from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    source_ip = Column(String, index=True)
    destination_ip = Column(String, index=True)
    source_port = Column(Integer)
    destination_port = Column(Integer)
    protocol = Column(String)
    alert_message = Column(String)
    ml_prediction = Column(Integer) # 0 for normal, 1 for anomaly
    snort_sid = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<Alert(id={self.id}, timestamp={self.timestamp}, message='{self.alert_message}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "protocol": self.protocol,
            "alert_message": self.alert_message,
            "ml_prediction": self.ml_prediction,
            "snort_sid": self.snort_sid,
        }
