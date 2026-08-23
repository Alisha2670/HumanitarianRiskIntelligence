import pickle
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


NUMERIC_COLS = ["pH", "DO", "BOD", "Nitrate", "Coliform", "Conductivity"]
CATEGORICAL_COLS = ["Region", "State", "District_Type"]
SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3}


# Conservative mid-risk defaults prevent "always low" behavior.
BASELINE_FEATURES = {
    "pH": 7.0,
    "DO": 5.5,
    "BOD": 4.5,
    "Nitrate": 35.0,
    "Coliform": 260.0,
    "Conductivity": 540.0,
}


def _clamp_features(features: Dict[str, float]) -> Dict[str, float]:
    bounds = {
        "pH": (5.5, 9.0),
        "DO": (0.5, 10.0),
        "BOD": (0.5, 15.0),
        "Nitrate": (1.0, 180.0),
        "Coliform": (0.0, 5000.0),
        "Conductivity": (50.0, 2500.0),
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
    Map simple real-life conditions to scientific features expected by the model.
    This mapping is intentionally designed to avoid low-risk-only collapse.
    """
    f = BASELINE_FEATURES.copy()

    # Expected values: "clear", "slightly_turbid", "muddy"
    turbidity = str(user_input.get("water_appearance", "slightly_turbid")).lower()
    if turbidity == "clear":
        f["Coliform"] -= 80
        f["BOD"] -= 0.8
    elif turbidity == "muddy":
        f["Coliform"] += 220
        f["BOD"] += 1.5
        f["DO"] -= 0.8

    # Expected values: "none", "mild", "strong"
    sewage_smell = str(user_input.get("sewage_smell", "mild")).lower()
    if sewage_smell == "none":
        f["Coliform"] -= 80
        f["BOD"] -= 0.6
    elif sewage_smell == "strong":
        f["Coliform"] += 260
        f["BOD"] += 2.0
        f["DO"] -= 0.8

    # Expected values: "none", "light", "heavy"
    nearby_industry = str(user_input.get("nearby_industry", "light")).lower()
    if nearby_industry == "none":
        f["Conductivity"] -= 120
        f["Nitrate"] -= 4
    elif nearby_industry == "heavy":
        f["Conductivity"] += 250
        f["Nitrate"] += 10
        f["BOD"] += 0.8

    # Expected values: "no", "yes"
    recent_flood = str(user_input.get("recent_flood", "no")).lower()
    if recent_flood == "yes":
        f["Coliform"] += 260
        f["Nitrate"] += 10
        f["DO"] -= 0.7

    # Expected values: "dry", "normal", "monsoon"
    season = str(user_input.get("season", "normal")).lower()
    if season == "dry":
        f["Conductivity"] += 90
        f["DO"] -= 0.2
    elif season == "monsoon":
        f["Coliform"] += 120
        f["Nitrate"] += 6
        f["DO"] -= 0.3

    # Expected values: "river", "lake", "tap", "borewell"
    water_source = str(user_input.get("water_source", "lake")).lower()
    if water_source == "tap":
        f["Coliform"] -= 120
        f["BOD"] -= 0.8
        f["DO"] += 0.4
    elif water_source == "borewell":
        f["Conductivity"] += 120
        f["Nitrate"] += 8
    elif water_source == "river":
        f["Coliform"] += 60

    # Expected values: "no", "yes"
    dead_fish_reported = str(user_input.get("dead_fish_reported", "no")).lower()
    if dead_fish_reported == "yes":
        f["DO"] -= 1.6
        f["BOD"] += 2.2
        f["Coliform"] += 140

    return _clamp_features(f)


def water_scenario_health(input_dict: Dict[str, float]) -> Dict[str, object]:
    """
    Build disease and precaution advisory from water condition values.
    """
    ph = float(input_dict.get("pH", 7.0))
    do = float(input_dict.get("DO", 5.5))
    bod = float(input_dict.get("BOD", 3.0))
    nitrate = float(input_dict.get("Nitrate", 20.0))
    coliform = float(input_dict.get("Coliform", 100.0))
    _ = float(input_dict.get("Conductivity", 500.0))

    diseases: List[str] = []
    precautions: List[str] = [
        "Drink clean, treated water",
        "Wash hands before handling water and food",
        "Store water in covered containers",
    ]
    severity = "Low"

    if coliform > 500:
        diseases.extend(["Cholera", "Typhoid", "Dysentery"])
        precautions.extend(
            ["Boil water", "Avoid direct consumption", "Use UV/RO treatment"]
        )
        severity = _escalate_severity(severity, "High")

    if nitrate > 50:
        diseases.append("Methemoglobinemia (Blue Baby Syndrome)")
        precautions.extend(["Avoid use for infants", "Use treated water"])
        severity = _escalate_severity(severity, "High")

    if bod > 6:
        diseases.append("Gastrointestinal infections")
        precautions.append("Use advanced filtration")
        severity = _escalate_severity(severity, "Moderate")

    if ph < 5.5 or ph > 9:
        diseases.extend(["Skin irritation", "Eye damage"])
        precautions.append("Avoid direct contact")
        severity = _escalate_severity(severity, "Moderate")

    if do < 4:
        precautions.append("Water ecosystem severely degraded")
        severity = _escalate_severity(severity, "Moderate")

    if severity == "Low":
        diseases.append("No major disease stress currently")
        precautions.extend(
            [
                "Continue routine water hygiene practices",
                "Monitor water quality periodically",
            ]
        )
    elif severity == "Moderate" and not diseases:
        diseases.append("Moderate water-related health risk")
        precautions.append("Use treated or filtered water until conditions improve")

    return {
        "diseases": _dedupe_keep_order(diseases),
        "severity": severity,
        "precautions": _dedupe_keep_order(precautions),
    }


def load_artifacts(
    model_path: str = "water_model.pkl", feature_cols_path: str = "feature_columns.pkl"
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
    # Guarantees strict feature order to avoid mismatch in production.
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
    health_advisory = water_scenario_health(estimated)
    return pred_label, proba_map, estimated, health_advisory


if __name__ == "__main__":
    # Example app-style input with non-scientific fields only.
    sample_user_input = {
        "Region": "East",
        "State": "Bihar",
        "District_Type": "Rural",
        "water_appearance": "muddy",
        "sewage_smell": "strong",
        "nearby_industry": "light",
        "recent_flood": "yes",
        "season": "monsoon",
        "water_source": "river",
        "dead_fish_reported": "yes",
    }

    label, proba, estimated_features, health_advisory = predict_with_explanation(
        sample_user_input
    )
    print("Predicted risk:", label)
    print("Class probabilities:", proba)
    print("Estimated scientific features:", estimated_features)
    print("Health advisory:", health_advisory)
