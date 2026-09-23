import json
from pathlib import Path

CROP_DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "sample_data"
    / "crops.json"
)


ANALYSIS_RULES = {
    "rice": {
        "preferred_storage": "Dry, clean and well-ventilated grain storage",
        "high_risk_humidity": 70,
        "high_risk_temperature": 32,
        "actions": [
            "Dry grain to a safe moisture level before long-term storage",
            "Keep bags or containers off the floor",
            "Protect grain from rainwater and roof leakage",
            "Inspect regularly for insects and fungal growth"
        ]
    },
    "onion": {
        "preferred_storage": "Cool, dry and well-ventilated onion storage",
        "high_risk_humidity": 75,
        "high_risk_temperature": 30,
        "actions": [
            "Keep onions dry",
            "Provide good air circulation",
            "Avoid direct contact with the floor",
            "Remove damaged or rotting bulbs regularly"
        ]
    },
    "ragi": {
        "preferred_storage": "Dry, low-moisture grain storage",
        "high_risk_humidity": 65,
        "high_risk_temperature": 32,
        "actions": [
            "Dry grain properly before storage",
            "Use clean and moisture-resistant containers",
            "Keep storage area dry and ventilated",
            "Inspect periodically for insects"
        ]
    },
    "tomato": {
        "preferred_storage": "Cool, shaded and ventilated storage",
        "high_risk_humidity": 80,
        "high_risk_temperature": 30,
        "actions": [
            "Handle tomatoes carefully to avoid bruising",
            "Remove damaged fruits",
            "Keep produce shaded",
            "Avoid trapping excessive moisture around the produce"
        ]
    },
    "maize": {
        "preferred_storage": "Dry, well-ventilated grain storage",
        "high_risk_humidity": 70,
        "high_risk_temperature": 32,
        "actions": [
            "Dry maize adequately before storage",
            "Protect from moisture and rain",
            "Use clean storage containers",
            "Monitor for insects and fungal growth"
        ]
    },
    "sugarcane": {
        "preferred_storage": "Short-duration shaded storage with rapid processing",
        "high_risk_humidity": 85,
        "high_risk_temperature": 35,
        "actions": [
            "Avoid prolonged storage after harvest",
            "Keep harvested cane shaded",
            "Minimize physical damage during handling",
            "Plan transportation or processing quickly"
        ]
    }
}


def load_crop_data():
    with open(CROP_DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        crop["id"]: crop
        for crop in data["supported_crops"]
    }


CROP_DATA = ANALYSIS_RULES
CROP_INFORMATION = load_crop_data()