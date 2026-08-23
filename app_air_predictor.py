import pickle
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


NUMERIC_COLS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
CATEGORICAL_COLS = ["Region", "State", "District_Type"]
SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3}

# Mid-band defaults reduce class collapse toward one label.
BASELINE_FEATURES = {
    "PM2.5": 65.0,
    "PM10": 130.0,
    "NO2": 35.0,
    "SO2": 18.0,
    "CO": 1.4,
    "O3": 35.0,
}


def _clamp_features(features: Dict[str, float]) -> Dict[str, float]:
    bounds = {
        "PM2.5": (5.0, 450.0),
        "PM10": (10.0, 600.0),
        "NO2": (5.0, 220.0),
        "SO2": (2.0, 150.0),
        "CO": (0.2, 10.0),
        "O3": (5.0, 180.0),
    }
    for key, (low, high) in bounds.items():
        features[key] = float(np.clip(features[key], low, high))
    return features


def _escalate_severity(current: str, candidate: str) -> str:
    if SEVERITY_RANK[candidate] > SEVERITY_RANK[current]:
        return candidate
    return current


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def estimate_scientific_features(user_input: Dict) -> Dict[str, float]:
    """
    Map observable day-to-day conditions to air pollutant estimates.
    Users provide practical inputs; model still consumes scientific features.
    """
    f = BASELINE_FEATURES.copy()

    traffic_level = str(user_input.get("traffic_level", "moderate")).lower()
    if traffic_level == "low":
        f["PM2.5"] -= 10
        f["PM10"] -= 18
        f["NO2"] -= 8
        f["CO"] -= 0.2
    elif traffic_level == "high":
        f["PM2.5"] += 18
        f["PM10"] += 32
        f["NO2"] += 16
        f["CO"] += 0.5

    visible_haze = str(user_input.get("visible_haze", "light")).lower()
    if visible_haze == "none":
        f["PM2.5"] -= 12
        f["PM10"] -= 18
    elif visible_haze == "dense":
        f["PM2.5"] += 28
        f["PM10"] += 46
        f["NO2"] += 6

    smell_of_smoke = str(user_input.get("smell_of_smoke", "mild")).lower()
    if smell_of_smoke == "none":
        f["PM2.5"] -= 8
        f["CO"] -= 0.2
    elif smell_of_smoke == "strong":
        f["PM2.5"] += 22
        f["PM10"] += 24
        f["CO"] += 0.8

    open_burning_nearby = str(user_input.get("open_burning_nearby", "no")).lower()
    if open_burning_nearby == "yes":
        f["PM2.5"] += 30
        f["PM10"] += 40
        f["CO"] += 0.7

    ventilation_quality = str(user_input.get("ventilation_quality", "average")).lower()
    if ventilation_quality == "good":
        f["PM2.5"] -= 6
        f["CO"] -= 0.1
    elif ventilation_quality == "poor":
        f["PM2.5"] += 12
        f["CO"] += 0.4

    indoor_cooking_fuel = str(user_input.get("indoor_cooking_fuel", "lpg")).lower()
    if indoor_cooking_fuel == "clean_electric":
        f["PM2.5"] -= 8
        f["CO"] -= 0.2
    elif indoor_cooking_fuel == "biomass":
        f["PM2.5"] += 20
        f["PM10"] += 15
        f["CO"] += 0.7

    season = str(user_input.get("season", "normal")).lower()
    if season == "winter":
        f["PM2.5"] += 16
        f["PM10"] += 18
        f["NO2"] += 6
    elif season == "monsoon":
        f["PM2.5"] -= 10
        f["PM10"] -= 15
        f["NO2"] -= 3
        f["O3"] -= 4
    elif season == "summer":
        f["O3"] += 14

    nearby_industry = str(user_input.get("nearby_industry", "light")).lower()
    if nearby_industry == "none":
        f["SO2"] -= 5
        f["NO2"] -= 4
    elif nearby_industry == "heavy":
        f["SO2"] += 16
        f["NO2"] += 10
        f["PM10"] += 12

    return _clamp_features(f)


def air_scenario_health(input_dict: Dict[str, float]) -> Dict[str, object]:
    """
    Build disease and precaution advisory from air condition values.
    """
    pm25 = float(input_dict.get("PM2.5", 30.0))
    _ = float(input_dict.get("PM10", 70.0))
    no2 = float(input_dict.get("NO2", 25.0))
    so2 = float(input_dict.get("SO2", 12.0))
    co = float(input_dict.get("CO", 1.0))
    _ = float(input_dict.get("O3", 30.0))

    diseases: List[str] = []
    precautions: List[str] = [
        "Stay hydrated and avoid prolonged exposure in polluted zones",
        "Keep indoor spaces ventilated and dust-free",
        "Track local AQI before outdoor activity",
    ]
    severity = "Low"

    if pm25 > 120:
        diseases.extend(
            ["Severe asthma", "Lung inflammation", "Cardiovascular risk"]
        )
        precautions.extend(["Stay indoors", "Wear N95 mask", "Use air purifier"])
        severity = _escalate_severity(severity, "High")
    elif 60 <= pm25 <= 120:
        diseases.extend(["Mild asthma", "Allergies"])
        precautions.append("Limit outdoor exposure")
        severity = _escalate_severity(severity, "Moderate")

    if no2 > 80:
        diseases.append("Respiratory irritation")
        precautions.append("Avoid traffic-heavy areas")
        severity = _escalate_severity(severity, "Moderate")

    if so2 > 40:
        diseases.append("Bronchitis")
        precautions.append("Avoid industrial zones")
        severity = _escalate_severity(severity, "Moderate")

    if co > 2:
        diseases.append("Oxygen deprivation (hypoxia risk)")
        precautions.append("Ensure ventilation")
        severity = _escalate_severity(severity, "High")

    if severity == "Low":
        diseases.append("No major disease stress currently")
        precautions.extend(
            [
                "Maintain routine respiratory care",
                "Prefer outdoor exercise during cleaner air hours",
            ]
        )
    elif severity == "Moderate" and not diseases:
        diseases.append("Moderate respiratory health risk")
        precautions.append("Reduce intense outdoor activity until air improves")

    return {
        "diseases": _dedupe_keep_order(diseases),
        "severity": severity,
        "precautions": _dedupe_keep_order(precautions),
    }


def load_artifacts(
    model_path: str = "air_model.pkl", feature_cols_path: str = "air_feature_columns.pkl"
):
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(feature_cols_path, "rb") as f:
        feature_columns = pickle.load(f)
    return model, feature_columns


def build_model_input(user_input: Dict, feature_columns) -> pd.DataFrame:
    estimated = estimate_scientific_features(user_input)
    row = {k: estimated[k] for k in NUMERIC_COLS}
    row["Region"] = user_input.get("Region", "Unknown")
    row["State"] = user_input.get("State", "Unknown")
    row["District_Type"] = user_input.get("District_Type", "Semi-Urban")

    df = pd.DataFrame([row])
    return df[feature_columns]


def predict_with_explanation(
    user_input: Dict,
) -> Tuple[str, Dict[str, float], Dict[str, float], Dict[str, object]]:
    model, feature_columns = load_artifacts()
    model_input = build_model_input(user_input, feature_columns)
    pred_label = model.predict(model_input)[0]
    probs = model.predict_proba(model_input)[0]
    proba_map = {cls: float(prob) for cls, prob in zip(model.classes_, probs)}
    estimated = estimate_scientific_features(user_input)
    health_advisory = air_scenario_health(estimated)
    return pred_label, proba_map, estimated, health_advisory


if __name__ == "__main__":
    sample_user_input = {
        "Region": "North",
        "State": "Delhi",
        "District_Type": "Urban",
        "traffic_level": "high",
        "visible_haze": "dense",
        "smell_of_smoke": "strong",
        "open_burning_nearby": "yes",
        "ventilation_quality": "poor",
        "indoor_cooking_fuel": "lpg",
        "season": "winter",
        "nearby_industry": "light",
    }

    label, proba, estimated_features, health_advisory = predict_with_explanation(
        sample_user_input
    )
    print("Predicted air quality:", label)
    print("Class probabilities:", proba)
    print("Estimated scientific features:", estimated_features)
    print("Health advisory:", health_advisory)
