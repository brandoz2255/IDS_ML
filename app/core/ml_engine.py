import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

class SimpleMLP(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(SimpleMLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc3 = nn.Linear(hidden_size // 2, num_classes)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc3(out)
        return out

class EnhancedMLP(nn.Module):
    """Enhanced MLP with batch normalization and residual connections"""
    def __init__(self, input_size, hidden_size, num_classes, num_layers=3):
        super(EnhancedMLP, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_classes = num_classes
        
        # Input layer
        self.input_layer = nn.Linear(input_size, hidden_size)
        self.input_bn = nn.BatchNorm1d(hidden_size)
        
        # Hidden layers
        self.hidden_layers = nn.ModuleList()
        self.hidden_bns = nn.ModuleList()
        
        for i in range(num_layers - 1):
            self.hidden_layers.append(nn.Linear(hidden_size, hidden_size))
            self.hidden_bns.append(nn.BatchNorm1d(hidden_size))
        
        # Output layer
        self.output_layer = nn.Linear(hidden_size, num_classes)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        # Input layer
        out = self.input_layer(x)
        out = self.input_bn(out)
        out = self.relu(out)
        out = self.dropout(out)
        
        # Hidden layers with residual connections
        for i, (layer, bn) in enumerate(zip(self.hidden_layers, self.hidden_bns)):
            residual = out
            out = layer(out)
            out = bn(out)
            out = self.relu(out)
            out = self.dropout(out)
            # Add residual connection
            out = out + residual
        
        # Output layer
        out = self.output_layer(out)
        return out

class MLService:
    def __init__(self, model_path="./ml_model.pth", use_enhanced=True):
        self.model_path = model_path
        self.scaler_path = "./scaler.pkl"
        self.isolation_forest_path = "./isolation_forest.pkl"
        self.metrics_path = "./model_metrics.json"
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Model configuration
        self.input_size = 25  # Enhanced feature size
        self.hidden_size = 64
        self.num_classes = 2  # Anomaly or Normal
        self.use_enhanced = use_enhanced
        
        # Initialize components
        self.model = None
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.model_metrics = {}
        
        self._load_model()
        self._load_scaler()
        self._load_isolation_forest()
        self._load_metrics()

    def _load_model(self):
        if os.path.exists(self.model_path):
            print(f"Loading ML model from {self.model_path}")
            if self.use_enhanced:
                self.model = EnhancedMLP(self.input_size, self.hidden_size, self.num_classes).to(self.device)
            else:
                self.model = SimpleMLP(self.input_size, self.hidden_size, self.num_classes).to(self.device)
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.eval()
        else:
            print("No pre-trained model found. Initializing a new model.")
            if self.use_enhanced:
                self.model = EnhancedMLP(self.input_size, self.hidden_size, self.num_classes).to(self.device)
            else:
                self.model = SimpleMLP(self.input_size, self.hidden_size, self.num_classes).to(self.device)
            self._save_model()
    
    def _load_scaler(self):
        if os.path.exists(self.scaler_path):
            self.scaler = joblib.load(self.scaler_path)
            print(f"Loaded scaler from {self.scaler_path}")
        else:
            print("No scaler found. Will fit on first training data.")
    
    def _load_isolation_forest(self):
        if os.path.exists(self.isolation_forest_path):
            self.isolation_forest = joblib.load(self.isolation_forest_path)
            print(f"Loaded isolation forest from {self.isolation_forest_path}")
        else:
            print("No isolation forest found. Will fit on first training data.")
    
    def _load_metrics(self):
        if os.path.exists(self.metrics_path):
            with open(self.metrics_path, 'r') as f:
                self.model_metrics = json.load(f)
            print(f"Loaded metrics from {self.metrics_path}")
        else:
            self.model_metrics = {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "last_updated": None
            }

    def _save_model(self):
        print(f"Saving ML model to {self.model_path}")
        torch.save(self.model.state_dict(), self.model_path)

    def predict(self, data):
        if self.model is None:
            raise ValueError("ML model not loaded.")
        # Convert data to tensor, perform inference
        # This is a placeholder, actual preprocessing will be more complex
        input_tensor = torch.tensor(data, dtype=torch.float32).unsqueeze(0).to(self.device) # Add batch dimension and move to device
        with torch.no_grad():
            output = self.model(input_tensor)
            _, predicted = torch.max(output.data, 1)
        return predicted.item() # 0 for normal, 1 for anomaly (example)

    def retrain_model(self):
        print("Initiating ML model retraining...")
        # In a real scenario, this would involve:
        # 1. Loading historical data from PostgreSQL
        # 2. Preprocessing the data
        # 3. Defining a new model or continuing training an existing one
        # 4. Training loop with loss function and optimizer
        # 5. Evaluation and saving the new model

        # Dummy retraining process
        new_model = SimpleMLP(self.input_size, self.hidden_size, self.num_classes).to(self.device)
        optimizer = optim.Adam(new_model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        # Simulate some training data (replace with actual data loading)
        dummy_inputs = torch.randn(100, self.input_size).to(self.device) # 100 samples, input_size features
        dummy_labels = torch.randint(0, self.num_classes, (100,)).to(self.device) # 100 labels (0 or 1)

        for epoch in range(5): # Simulate 5 epochs
            optimizer.zero_grad()
            outputs = new_model(dummy_inputs)
            loss = criterion(outputs, dummy_labels)
            loss.backward()
            optimizer.step()
            print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

        self.model = new_model
        self._save_model()
        print("ML model retraining complete.")

if __name__ == "__main__":
    # Example usage:
    ml_service = MLService()
    # Simulate some data for prediction
    dummy_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    prediction = ml_service.predict(dummy_data)
    print(f"Prediction for dummy data: {prediction}")

    # Simulate retraining
    ml_service.retrain_model()
    prediction_after_retrain = ml_service.predict(dummy_data)
    print(f"Prediction after retraining: {prediction_after_retrain}")
