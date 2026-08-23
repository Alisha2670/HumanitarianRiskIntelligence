import random

import numpy as np
import pandas as pd

np.random.seed(42)

# ---------------------------
# INDIA REGIONS
# ---------------------------
india_regions = {
    "North": ["Punjab", "Haryana", "Delhi", "Uttarakhand", "Himachal Pradesh"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
    "South": ["Tamil Nadu", "Karnataka", "Kerala", "Telangana", "Andhra Pradesh"],
    "East": ["West Bengal", "Bihar", "Jharkhand", "Odisha"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
    "Northeast": ["Assam", "Meghalaya", "Manipur", "Tripura", "Nagaland"],
    "Islands": ["Andaman and Nicobar Islands", "Lakshadweep"],
    "Northwest": ["Jammu and Kashmir", "Ladakh"],
}

district_types = ["Urban", "Semi-Urban", "Rural"]

# ---------------------------
# REGION POLLUTION PROFILES
# ---------------------------
region_profile = {
    "North": {"pollution": 1.8},
    "West": {"pollution": 1.5},
    "South": {"pollution": 1.1},
    "East": {"pollution": 1.6},
    "Central": {"pollution": 1.3},
    "Northeast": {"pollution": 0.8},
    "Islands": {"pollution": 0.5},
    "Northwest": {"pollution": 0.9},
}


def generate_sample(target_class: str, region: str) -> dict:
    factor = region_profile[region]["pollution"]

    if target_class == "Good":
        pm25 = np.random.normal(30, 10) * factor * 0.6
    elif target_class == "Moderate":
        pm25 = np.random.normal(70, 15) * factor * 0.8
    else:
        pm25 = np.random.normal(130, 25) * factor

    pm25 = max(5, pm25)
    pm10 = pm25 * np.random.uniform(1.5, 2.2)
    no2 = pm25 * np.random.uniform(0.3, 0.6)
    so2 = pm25 * np.random.uniform(0.1, 0.3)
    co = np.random.uniform(0.5, 3.0) * factor
    o3 = np.random.uniform(10, 80)

    return {
        "PM2.5": round(pm25, 2),
        "PM10": round(pm10, 2),
        "NO2": round(no2, 2),
        "SO2": round(so2, 2),
        "CO": round(co, 2),
        "O3": round(o3, 2),
        "Air_Quality": target_class,
    }


def main() -> None:
    data = []
    classes = ["Good", "Moderate", "Poor"]
    rows_per_class = 600  # total = 1800

    for cls in classes:
        for _ in range(rows_per_class):
            region = random.choice(list(india_regions.keys()))
            state = random.choice(india_regions[region])
            district = random.choice(district_types)

            row = generate_sample(cls, region)
            row["Region"] = region
            row["State"] = state
            row["District_Type"] = district
            data.append(row)

    df_air = pd.DataFrame(data).sample(frac=1, random_state=42).reset_index(drop=True)

    output_csv = "india_air_quality_full.csv"
    output_xlsx = "india_air_quality_full.xlsx"
    df_air.to_csv(output_csv, index=False)
    df_air.to_excel(output_xlsx, index=False)

    print("Dataset generated:")
    print(f"- {output_csv}")
    print(f"- {output_xlsx}")
    print("Dataset shape:", df_air.shape)
    print(df_air.head())


if __name__ == "__main__":
    main()
