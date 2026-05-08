import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from challenge import app


class TestBatchPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    def test_should_get_predict(self):
        data = {
            "flights": [
                {
                    "OPERA": "Aerolineas Argentinas", 
                    "TIPOVUELO": "N", 
                    "MES": 3
                }
            ]
        }
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"predict": [0]})

    def test_should_get_predict_batch(self):
        """Test batch prediction with multiple flights."""
        data = {
            "flights": [
                {"OPERA": "Aerolineas Argentinas", "TIPOVUELO": "N", "MES": 3},
                {"OPERA": "Grupo LATAM", "TIPOVUELO": "I", "MES": 7},
                {"OPERA": "Sky Airline", "TIPOVUELO": "N", "MES": 12}
            ]
        }
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("predict", result)
        self.assertEqual(len(result["predict"]), 3)
        self.assertTrue(all(isinstance(p, int) for p in result["predict"]))
    

    def test_should_failed_unkown_column_1(self):
        data = {       
            "flights": [
                {
                    "OPERA": "Aerolineas Argentinas", 
                    "TIPOVUELO": "N",
                    "MES": 13
                }
            ]
        }
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 400)

    def test_should_failed_unkown_column_2(self):
        data = {        
            "flights": [
                {
                    "OPERA": "Aerolineas Argentinas", 
                    "TIPOVUELO": "O", 
                    "MES": 13
                }
            ]
        }
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 400)
    
    def test_should_failed_unkown_column_3(self):
        data = {        
            "flights": [
                {
                    "OPERA": "Argentinas", 
                    "TIPOVUELO": "O", 
                    "MES": 13
                }
            ]
        }
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 400)

    @patch("challenge.api.load_model")
    def test_should_return_500_on_model_error(self, mock_load_model):
        """Test 500 response when model loading fails."""
        mock_load_model.side_effect = RuntimeError("Model corrupted")
        
        data = {
            "flights": [
                {"OPERA": "Aerolineas Argentinas", "TIPOVUELO": "N", "MES": 3}
            ]
        }
        response = self.client.post("/predict", json=data)
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())