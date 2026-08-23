from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Reuse existing user-input-to-scientific-feature mappers.
from app_air_predictor import build_model_input as build_air_model_input
from app_air_predictor import estimate_scientific_features as estimate_air_features
from app_risk_predictor import build_model_input as build_water_model_input
from app_risk_predictor import estimate_scientific_features as estimate_water_features


SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3}


def _safe_float(value, default: float = 0.0) -> float:
    """Convert value to float safely; fallback for missing/invalid values."""
    try:
        if value is None:
            return default
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _escalate_severity(current: str, candidate: str) -> str:
    """Return the higher severity between current and candidate."""
    if SEVERITY_RANK[candidate] > SEVERITY_RANK[current]:
        return candidate
    return current


def _dedupe_keep_order(items: List[str]) -> List[str]:
    """Remove duplicates while preserving list order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def water_scenario_health(input_dict: Dict) -> Dict[str, List[str] | str]:
    """
    Build scenario-based health advisory from water scientific parameters.

    Expected keys:
    pH, DO, BOD, Nitrate, Coliform, Conductivity
    """
    ph = _safe_float(input_dict.get("pH"), 7.0)
    do = _safe_float(input_dict.get("DO"), 5.5)
    bod = _safe_float(input_dict.get("BOD"), 3.0)
    nitrate = _safe_float(input_dict.get("Nitrate"), 20.0)
    coliform = _safe_float(input_dict.get("Coliform"), 100.0)
    _ = _safe_float(input_dict.get("Conductivity"), 500.0)  # reserved for future rules

    diseases: List[str] = []
    precautions: List[str] = []
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

    return {
        "diseases": _dedupe_keep_order(diseases),
        "severity": severity,
        "precautions": _dedupe_keep_order(precautions),
    }


def air_scenario_health(input_dict: Dict) -> Dict[str, List[str] | str]:
    """
    Build scenario-based health advisory from air scientific parameters.

    Expected keys:
    PM2.5, PM10, NO2, SO2, CO, O3
    """
    pm25 = _safe_float(input_dict.get("PM2.5"), 30.0)
    _ = _safe_float(input_dict.get("PM10"), 60.0)  # reserved for future rules
    no2 = _safe_float(input_dict.get("NO2"), 25.0)
    so2 = _safe_float(input_dict.get("SO2"), 12.0)
    co = _safe_float(input_dict.get("CO"), 1.0)
    _ = _safe_float(input_dict.get("O3"), 30.0)  # reserved for future rules

    diseases: List[str] = []
    precautions: List[str] = []
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

    return {
        "diseases": _dedupe_keep_order(diseases),
        "severity": severity,
        "precautions": _dedupe_keep_order(precautions),
    }


def _prepare_model_input_frame(input_df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
    """Align incoming dataframe to model features and safely fill missing values."""
    frame = input_df.copy()
    for col in feature_columns:
        if col not in frame.columns:
            frame[col] = pd.NA

    frame = frame[feature_columns].copy()

    # Fill numeric columns with median fallback (or 0.0 if all missing).
    numeric_cols = frame.select_dtypes(include=["number"]).columns.tolist()
    for col in numeric_cols:
        col_median = frame[col].median()
        if pd.isna(col_median):
            col_median = 0.0
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(col_median)

    # Fill non-numeric with string placeholders.
    non_numeric_cols = [c for c in frame.columns if c not in numeric_cols]
    for col in non_numeric_cols:
        frame[col] = frame[col].astype("string").fillna("Unknown")

    return frame


def predict_with_health(model, input_df: pd.DataFrame, type: str, feature_columns=None) -> Dict:
    """
    Predict class with existing model and attach rule-based health advisory.

    Steps:
    1) Predict risk using model
    2) Convert first input row to dict
    3) Call corresponding health function
    4) Return prediction + advisory bundle
    """
    if input_df is None or input_df.empty:
        raise ValueError("input_df must contain at least one row.")

    scenario_type = str(type).strip().lower()
    if scenario_type not in {"water", "air"}:
        raise ValueError("type must be either 'water' or 'air'.")

    if feature_columns is not None:
        model_input_df = _prepare_model_input_frame(input_df, list(feature_columns))
    else:
        model_input_df = input_df.copy()

    prediction = model.predict(model_input_df)[0]

    row_dict = input_df.iloc[0].to_dict()
    if scenario_type == "water":
        health = water_scenario_health(row_dict)
    else:
        health = air_scenario_health(row_dict)

    return {
        "prediction": prediction,
        "diseases": health["diseases"],
        "severity": health["severity"],
        "precautions": health["precautions"],
    }


def load_water_artifacts(
    model_path: str = "water_model.pkl", feature_cols_path: str = "feature_columns.pkl"
) -> Tuple[object, List[str]]:
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(feature_cols_path, "rb") as f:
        feature_columns = pickle.load(f)
    return model, feature_columns


def load_air_artifacts(
    model_path: str = "air_model.pkl", feature_cols_path: str = "air_feature_columns.pkl"
) -> Tuple[object, List[str]]:
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(feature_cols_path, "rb") as f:
        feature_columns = pickle.load(f)
    return model, feature_columns


def predict_water_platform(user_input: Dict) -> Dict:
    """
    Unified water platform flow:
    - map practical inputs -> scientific water features
    - run existing model
    - generate scenario health advisory from scientific values
    """
    model, feature_columns = load_water_artifacts()
    model_input = build_water_model_input(user_input, feature_columns)
    advisory = predict_with_health(model, model_input, "water", feature_columns=feature_columns)
    scientific = estimate_water_features(user_input)

    return {
        "module": "water",
        "prediction": advisory["prediction"],
        "diseases": advisory["diseases"],
        "severity": advisory["severity"],
        "precautions": advisory["precautions"],
        "scientific_features": scientific,
        "model_input": model_input.to_dict(orient="records")[0],
    }


def predict_air_platform(user_input: Dict) -> Dict:
    """
    Unified air platform flow:
    - map practical inputs -> scientific air features
    - run existing model
    - generate scenario health advisory from scientific values
    """
    model, feature_columns = load_air_artifacts()
    model_input = build_air_model_input(user_input, feature_columns)
    advisory = predict_with_health(model, model_input, "air", feature_columns=feature_columns)
    scientific = estimate_air_features(user_input)

    return {
        "module": "air",
        "prediction": advisory["prediction"],
        "diseases": advisory["diseases"],
        "severity": advisory["severity"],
        "precautions": advisory["precautions"],
        "scientific_features": scientific,
        "model_input": model_input.to_dict(orient="records")[0],
    }


def predict_platform(user_input: Dict, type: str) -> Dict:
    """
    Single umbrella entrypoint for both modules.
    type: 'water' or 'air'
    """
    scenario_type = str(type).strip().lower()
    if scenario_type == "water":
        return predict_water_platform(user_input)
    if scenario_type == "air":
        return predict_air_platform(user_input)
    raise ValueError("type must be either 'water' or 'air'.")


def _artifacts_exist() -> bool:
    required = [
        Path("water_model.pkl"),
        Path("feature_columns.pkl"),
        Path("air_model.pkl"),
        Path("air_feature_columns.pkl"),
    ]
    return all(path.exists() for path in required)


if __name__ == "__main__":
    if not _artifacts_exist():
        print("Missing one or more model artifacts. Expected:")
        print("- water_model.pkl")
        print("- feature_columns.pkl")
        print("- air_model.pkl")
        print("- air_feature_columns.pkl")
        raise SystemExit(1)

    # Example usage: WATER module (practical user inputs only).
    water_user_input = {
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
    water_result = predict_platform(water_user_input, type="water")
    print("\n=== WATER HEALTH INTELLIGENCE ===")
    print(water_result)

    # Example usage: AIR module (practical user inputs only).
    air_user_input = {
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
        "nearby_industry": "heavy",
    }
    air_result = predict_platform(air_user_input, type="air")
    print("\n=== AIR HEALTH INTELLIGENCE ===")
    print(air_result)
