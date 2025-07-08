import pytest
import torch
import numpy as np
from unittest.mock import patch, MagicMock
from app.core.ml_engine import MLService, SimpleMLP

def test_simple_mlp_forward():
    """Test SimpleMLP forward pass"""
    model = SimpleMLP(input_size=10, hidden_size=20, num_classes=2)
    test_input = torch.randn(1, 10)
    output = model(test_input)
    
    assert output.shape == (1, 2)
    assert output.dtype == torch.float32

def test_ml_service_initialization():
    """Test MLService initialization"""
    with patch('os.path.exists', return_value=False):
        ml_service = MLService()
        assert ml_service.model is not None
        assert ml_service.input_size == 10
        assert ml_service.hidden_size == 20
        assert ml_service.num_classes == 2

def test_ml_service_prediction():
    """Test MLService prediction"""
    with patch('os.path.exists', return_value=False):
        ml_service = MLService()
        test_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        prediction = ml_service.predict(test_data)
        assert isinstance(prediction, int)
        assert prediction in [0, 1]

def test_ml_service_prediction_invalid_input():
    """Test MLService prediction with invalid input"""
    with patch('os.path.exists', return_value=False):
        ml_service = MLService()
        
        # Test with wrong input size
        test_data = [0.1, 0.2]  # Only 2 features instead of 10
        with pytest.raises(RuntimeError):
            ml_service.predict(test_data)

def test_ml_service_model_loading():
    """Test MLService model loading"""
    with patch('os.path.exists', return_value=True):
        with patch('torch.load') as mock_load:
            mock_load.return_value = {}
            ml_service = MLService()
            mock_load.assert_called_once()

def test_ml_service_model_saving():
    """Test MLService model saving"""
    with patch('os.path.exists', return_value=False):
        with patch('torch.save') as mock_save:
            ml_service = MLService()
            mock_save.assert_called()

def test_ml_service_retraining():
    """Test MLService retraining"""
    with patch('os.path.exists', return_value=False):
        with patch('torch.save') as mock_save:
            ml_service = MLService()
            
            # Mock GPU availability
            with patch('torch.cuda.is_available', return_value=False):
                ml_service.retrain_model()
                
            # Verify model was saved after retraining
            mock_save.assert_called()

def test_cuda_detection():
    """Test CUDA detection"""
    with patch('os.path.exists', return_value=False):
        with patch('torch.cuda.is_available', return_value=True):
            ml_service = MLService()
            assert ml_service.device.type == 'cuda'
        
        with patch('torch.cuda.is_available', return_value=False):
            ml_service = MLService()
            assert ml_service.device.type == 'cpu'

def test_model_training_loop():
    """Test model training loop functionality"""
    with patch('os.path.exists', return_value=False):
        ml_service = MLService()
        
        # Test that retraining completes without errors
        try:
            ml_service.retrain_model()
            assert True
        except Exception as e:
            pytest.fail(f"Retraining failed with error: {e}")

def test_model_inference_time():
    """Test model inference performance"""
    with patch('os.path.exists', return_value=False):
        ml_service = MLService()
        test_data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        import time
        start_time = time.time()
        prediction = ml_service.predict(test_data)
        inference_time = time.time() - start_time
        
        # Inference should be fast (< 1 second)
        assert inference_time < 1.0
        assert isinstance(prediction, int)