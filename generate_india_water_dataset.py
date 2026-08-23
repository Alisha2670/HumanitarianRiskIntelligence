import pandas as pd
import numpy as np
import random

np.random.seed(42)

# ---------------------------
# ALL STATES + UTs (India)
# ---------------------------
india_regions = {
    "North": ["Punjab", "Haryana", "Himachal Pradesh", "Uttarakhand", "Delhi", "Chandigarh"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan", "Goa", "Dadra and Nagar Haveli and Daman and Diu"],
    "South": ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh", "Telangana", "Puducherry"],
    "East": ["West Bengal", "Bihar", "Jharkhand", "Odisha"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
    "Northeast": ["Assam", "Arunachal Pradesh", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Tripura", "Sikkim"],
    "Islands": ["Andaman and Nicobar Islands", "Lakshadweep"],
    "Northwest": ["Jammu and Kashmir", "Ladakh"],
}

# ---------------------------
# Region-based pollution profiles
# ---------------------------
region_profile = {
    "North": {"nitrate": 1.4, "coliform": 1.2, "industrial": 1.2},
    "West": {"nitrate": 1.2, "coliform": 1.1, "industrial": 1.5},
    "South": {"nitrate": 1.0, "coliform": 1.0, "industrial": 1.2},
    "East": {"nitrate": 1.2, "coliform": 1.6, "industrial": 1.1},
    "Central": {"nitrate": 1.1, "coliform": 1.2, "industrial": 1.0},
    "Northeast": {"nitrate": 0.9, "coliform": 1.3, "industrial": 0.8},
    "Islands": {"nitrate": 0.7, "coliform": 0.8, "industrial": 0.6},
    "Northwest": {"nitrate": 1.1, "coliform": 1.0, "industrial": 1.0},
}

district_types = ["Urban", "Semi-Urban", "Rural"]


# ---------------------------
# Generate correlated sample
# ---------------------------
def generate_sample(risk, region):
    profile = region_profile[region]

    # Core relationship: BOD ↑ → DO ↓
    if risk == "Low":
        bod = np.random.normal(2, 0.7)
        do = 8 - (bod * 0.5) + np.random.normal(0, 0.4)
    elif risk == "Medium":
        bod = np.random.normal(4.5, 1.2)
        do = 6 - (bod * 0.4) + np.random.normal(0, 0.5)
    else:
        bod = np.random.normal(8, 2)
        do = 4 - (bod * 0.3) + np.random.normal(0, 0.6)

    nitrate = np.random.normal(30, 15) * profile["nitrate"]
    coliform = abs(np.random.normal(200, 300)) * profile["coliform"]
    conductivity = np.random.normal(500, 200) * profile["industrial"]

    ph = np.random.normal(7.2, 0.8)

    return {
        "pH": round(ph, 2),
        "DO": round(max(0.5, do), 2),
        "BOD": round(max(0.5, bod), 2),
        "Nitrate": round(max(1, nitrate), 2),
        "Coliform": int(max(0, coliform)),
        "Conductivity": round(max(50, conductivity), 2),
        "Risk": risk,
    }


# ---------------------------
# Create dataset
# ---------------------------
data = []
classes = ["Low", "Medium", "High"]
rows_per_class = 600  # total = 1800

for risk in classes:
    for _ in range(rows_per_class):
        region = random.choice(list(india_regions.keys()))
        state = random.choice(india_regions[region])
        district_type = random.choice(district_types)

        row = generate_sample(risk, region)
        row["Region"] = region
        row["State"] = state
        row["District_Type"] = district_type

        data.append(row)

df = pd.DataFrame(data)
df = df.sample(frac=1).reset_index(drop=True)

output_file = "india_water_quality_full.csv"
df.to_csv(output_file, index=False)

print("Dataset generated:", output_file)
print("Dataset shape:", df.shape)
print(df.head())
