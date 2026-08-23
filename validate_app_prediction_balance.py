from collections import Counter
from itertools import product

import pandas as pd

from app_risk_predictor import build_model_input, load_artifacts


def generate_scenarios():
    regions = ["North", "South", "East", "West", "Northeast"]
    district_types = ["Urban", "Semi-Urban", "Rural"]
    appearances = ["clear", "slightly_turbid", "muddy"]
    smell_levels = ["none", "mild", "strong"]
    industry_levels = ["none", "light", "heavy"]
    flood_flags = ["no", "yes"]
    seasons = ["dry", "normal", "monsoon"]
    water_sources = ["tap", "lake", "river", "borewell"]
    fish_flags = ["no", "yes"]

    scenarios = []
    for (
        region,
        district_type,
        appearance,
        smell,
        industry,
        flood,
        season,
        source,
        fish,
    ) in product(
        regions,
        district_types,
        appearances,
        smell_levels,
        industry_levels,
        flood_flags,
        seasons,
        water_sources,
        fish_flags,
    ):
        scenarios.append(
            {
                "Region": region,
                "State": "Unseen Test State",
                "District_Type": district_type,
                "water_appearance": appearance,
                "sewage_smell": smell,
                "nearby_industry": industry,
                "recent_flood": flood,
                "season": season,
                "water_source": source,
                "dead_fish_reported": fish,
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
    high_class_idx = list(model.classes_).index("High")
    high_risk_probs = proba[:, high_class_idx]

    counts = Counter(predictions)
    total = len(predictions)

    print("Total scenarios tested:", total)
    print("Prediction distribution:")
    for cls in ["Low", "Medium", "High"]:
        c = counts.get(cls, 0)
        pct = (c / total) * 100
        print(f"- {cls}: {c} ({pct:.2f}%)")

    print("\nAverage High-risk probability:", round(sum(high_risk_probs) / total, 4))
    print("Max High-risk probability:", round(max(high_risk_probs), 4))
    print("Min High-risk probability:", round(min(high_risk_probs), 4))

    # Simple guardrail alerts.
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
