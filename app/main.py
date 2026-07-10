from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import numpy as np
import torch
import torch.nn as nn
import joblib

# ==========================================================
# FastAPI Application
# ==========================================================
app = FastAPI(
    title="Cyber Threat Detection API",
    description="A PyTorch-powered API for detecting malicious system events.",
    version="1.0.0"
)

# ==========================================================
# Enable CORS
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://3aeb312f-febf-4aa9-9419-e8abd467cd23.lovableproject.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Request Schema
# ==========================================================
class PredictionRequest(BaseModel):
    userId: int
    mountNamespace: int
    argsNum: int
    returnValue: int


# ==========================================================
# Neural Network Architecture
# ==========================================================
class CyberThreatDetector(nn.Module):
    def __init__(self, input_dim):
        super().__init__()

        self.network = nn.Sequential(
            # Hidden Layer 1
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),

            # Hidden Layer 2
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.3),

            # Output Layer
            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.network(x).squeeze()


# ==========================================================
# Load trained model
# ==========================================================
model = CyberThreatDetector(input_dim=4)

model.load_state_dict(
    torch.load(
        "models/best_model.pth",
        map_location=torch.device("cpu"),
        weights_only=True
    )
)

model.eval()


# ==========================================================
# Load the scaler
# ==========================================================
scaler = joblib.load("models/scaler.pkl")


# ==========================================================
# Health Check Endpoint
# ==========================================================
@app.get("/")
def home():
    return {
        "message": "Cyber Threat Detection API is running"
    }


# ==========================================================
# Prediction Endpoint
# ==========================================================
@app.post("/predict")
def predict(request: PredictionRequest):

    print("=== PREDICT ENDPOINT CALLED ===")

    # Collect the incoming features
    features = [
        request.userId,
        request.mountNamespace,
        request.argsNum,
        request.returnValue
    ]

    # Convert to a NumPy array (2D because StandardScaler expects it)
    features = np.array([features])

    # Scale the features
    features = scaler.transform(features)

    # Convert the scaled features into a PyTorch tensor
    features = torch.tensor(features, dtype=torch.float32)

    # Run inference
    with torch.no_grad():
        logits = model(features)
        probability = torch.sigmoid(logits).item()

    # Debugging output (temporary)
    print("Logits:", logits.item())
    print("Probability:", probability)

    # Convert probability into a class label
    prediction = "Malicious" if probability >= 0.5 else "Benign"

    # Return the prediction and confidence score
    return {
        "prediction": prediction,
        "probability": round(probability, 4)
    }