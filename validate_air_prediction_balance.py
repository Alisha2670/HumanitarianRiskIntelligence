from collections import Counter
from itertools import product

import pandas as pd

from app_air_predictor import build_model_input, load_artifacts


def generate_scenarios():
    regions = ["North", "South", "East", "West", "Northeast"]
    district_types = ["Urban", "Semi-Urban", "Rural"]
    traffic_levels = ["low", "moderate", "high"]
    haze_levels = ["none", "light", "dense"]
    smoke_levels = ["none", "mild", "strong"]
    burning_flags = ["no", "yes"]
    ventilation_levels = ["good", "average", "poor"]
    cooking_fuels = ["clean_electric", "lpg", "biomass"]
    seasons = ["summer", "normal", "winter", "monsoon"]
    industry_levels = ["none", "light", "heavy"]

    scenarios = []
    for (
        region,
        district_type,
        traffic,
        haze,
        smoke,
        burning,
        ventilation,
        cooking_fuel,
        season,
        industry,
    ) in product(
        regions,
        district_types,
        traffic_levels,
        haze_levels,
        smoke_levels,
        burning_flags,
        ventilation_levels,
        cooking_fuels,
        seasons,
        industry_levels,
    ):
        scenarios.append(
            {
                "Region": region,
                "State": "Unseen Test State",
                "District_Type": district_type,
                "traffic_level": traffic,
                "visible_haze": haze,
                "smell_of_smoke": smoke,
                "open_burning_nearby": burning,
                "ventilation_quality": ventilation,
                "indoor_cooking_fuel": cooking_fuel,
                "season": season,
                "nearby_industry": industry,
            }
        )
    return scenarios


def main():
    model, feature_columns = load_artifacts()
    scenarios = generate_scenarios()
    input_rows = [build_model_input(s, feature_columns) for s in scenarios]
    X = pd.concat(input_rows, ignore_index=True)

    predictions = model.predict(X)
    proba = model.predict_proba(X)
    poor_class_idx = list(model.classes_).index("Poor")
    poor_probs = proba[:, poor_class_idx]

    counts = Counter(predictions)
    total = len(predictions)

    print("Total scenarios tested:", total)
    print("Prediction distribution:")
    for cls in ["Good", "Moderate", "Poor"]:
        c = counts.get(cls, 0)
        pct = (c / total) * 100
        print(f"- {cls}: {c} ({pct:.2f}%)")

    print("\nAverage Poor probability:", round(sum(poor_probs) / total, 4))
    print("Max Poor probability:", round(max(poor_probs), 4))
    print("Min Poor probability:", round(min(poor_probs), 4))

    dominant_class, dominant_count = counts.most_common(1)[0]
    dominant_pct = (dominant_count / total) * 100
    if dominant_pct > 85:
        print(
            f"\nALERT: Class '{dominant_class}' dominates at {dominant_pct:.2f}%."
            " Revisit mapping rules to reduce prediction collapse."
        )
    else:
        print("\nPASS: Predictions are reasonably distributed across classes.")


if __name__ == "__main__":
    main()
