from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from weather import get_weather
from database import get_connection
from crop_data import CROP_DATA


app = FastAPI(
    title="KrishiNova API",
    description="AI-assisted post-harvest crop loss prevention system",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

class FarmerCreate(BaseModel):
    name: str
    crop: str
    location: str
    quantity_kg: Optional[float] = None
    storage_available: Optional[str] = None


class CropAnalysisRequest(BaseModel):
    crop: str
    location: str
    quantity_kg: Optional[float] = None
    storage_available: Optional[str] = None
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    rainfall_expected: Optional[bool] = None


# ---------------------------------------------------------
# CROP KNOWLEDGE BASE
# ---------------------------------------------------------

CROP_RULES = CROP_DATA


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "KrishiNova backend running",
        "version": "1.0.0",
        "status": "healthy"
    }


# ---------------------------------------------------------
# FARMER REGISTRATION
# ---------------------------------------------------------

@app.post("/farmers")
def add_farmer(farmer: FarmerCreate):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO farmers
        (name, crop, location, quantity_kg, storage_available)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, crop, location, quantity_kg, storage_available
        """,
        (
            farmer.name,
            farmer.crop,
            farmer.location,
            farmer.quantity_kg,
            farmer.storage_available
        )
    )

    row = cursor.fetchone()

    conn.commit()

    cursor.close()
    conn.close()

    return {
        "message": "Farmer added successfully",
        "farmer": {
            "id": row[0],
            "name": row[1],
            "crop": row[2],
            "location": row[3],
            "quantity_kg": row[4],
            "storage_available": row[5]
        }
    }


# ---------------------------------------------------------
# GET FARMERS
# ---------------------------------------------------------

@app.get("/farmers")
def get_farmers():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            crop,
            location,
            quantity_kg,
            storage_available,
            created_at
        FROM farmers
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "crop": row[2],
            "location": row[3],
            "quantity_kg": row[4],
            "storage_available": row[5],
            "created_at": row[6]
        }
        for row in rows
    ]


# ---------------------------------------------------------
# POST-HARVEST ANALYSIS
# ---------------------------------------------------------

@app.post("/analysis")
def crop_analysis(request: CropAnalysisRequest):

    crop = request.crop.strip().lower()

    # ---------------------------------------------------------
    # CHECK CROP
    # ---------------------------------------------------------

    if crop not in CROP_RULES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Crop is not currently supported",
                "supported_crops": list(CROP_RULES.keys())
            }
        )

    rules = CROP_RULES[crop]

    # ---------------------------------------------------------
    # GET REAL WEATHER
    # ---------------------------------------------------------

    try:

        weather_data = get_weather(request.location)
        weather_available = True

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception:

        # Weather service may be temporarily unavailable
        # or rate-limited.
        #
        # KrishiNova should still perform crop analysis
        # instead of completely failing.

        weather_available = False

        weather_data = {
            "location": request.location,
            "country": None,
            "latitude": None,
            "longitude": None,

           "temperature_c": request.temperature_c if request.temperature_c is not None else 25.0,
"humidity_percent": request.humidity_percent if request.humidity_percent is not None else 70.0,

            "precipitation_mm": None,

            "rain_mm": None,

            "rain_probability_percent": None,

            "rainfall_expected": (
                request.rainfall_expected
                if request.rainfall_expected is not None
                else False
            )
        }

    # ---------------------------------------------------------
    # WEATHER VALUES
    # ---------------------------------------------------------

    temperature = weather_data["temperature_c"]

    humidity = weather_data["humidity_percent"]

    rainfall_expected = weather_data["rainfall_expected"]


    # ---------------------------------------------------------
    # RISK CALCULATION
    # ---------------------------------------------------------

    risk_score = 0

    risk_factors = []


    # ---------------------------------------------------------
    # TEMPERATURE
    # ---------------------------------------------------------

    if temperature is not None:

        if temperature >= rules["high_risk_temperature"]:

            risk_score += 2

            risk_factors.append(
                f"High temperature ({temperature}°C)"
            )


    # ---------------------------------------------------------
    # HUMIDITY
    # ---------------------------------------------------------

    if humidity is not None:

        if humidity >= rules["high_risk_humidity"]:

            risk_score += 2

            risk_factors.append(
                f"High humidity ({humidity}%)"
            )


    # ---------------------------------------------------------
    # RAIN
    # ---------------------------------------------------------

    if rainfall_expected:

        risk_score += 2

        risk_factors.append(
            "Rainfall expected"
        )


    # ---------------------------------------------------------
    # STORAGE
    # ---------------------------------------------------------

    if request.storage_available:

        storage = request.storage_available.lower()

        if "open" in storage or "outdoor" in storage:

            risk_score += 2

            risk_factors.append(
                "Produce is exposed to outdoor conditions"
            )


    # ---------------------------------------------------------
    # RISK LEVEL
    # ---------------------------------------------------------

    if risk_score >= 5:

        risk_level = "HIGH"

    elif risk_score >= 3:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"


    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    return {

        "crop": crop,

        "location": request.location,

        "quantity_kg": request.quantity_kg,

        "risk": {
            "score": risk_score,
            "level": risk_level,
            "factors": risk_factors
        },

        "recommended_storage": rules[
            "preferred_storage"
        ],

        "recommended_actions": rules[
            "actions"
        ],

        "weather": {

            "available": weather_available,

            "temperature_c": temperature,

            "humidity_percent": humidity,

            "precipitation_mm": weather_data[
                "precipitation_mm"
            ],

            "rain_mm": weather_data[
                "rain_mm"
            ],

            "rain_probability_percent": weather_data[
                "rain_probability_percent"
            ],

            "rainfall_expected": rainfall_expected
        }
    }


# ---------------------------------------------------------
# SUPPORTED CROPS
# ---------------------------------------------------------

@app.get("/crops")
def get_supported_crops():

    return {
        "supported_crops": list(CROP_RULES.keys())
    }


# ---------------------------------------------------------
# WEATHER
# ---------------------------------------------------------

@app.get("/weather")
def weather(location: str):

    try:

        return get_weather(location)

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=f"Weather service error: {str(error)}"
        )