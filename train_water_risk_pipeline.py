import pickle
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def load_dataset() -> pd.DataFrame:
    """Load dataset from .xlsx first, then fallback to .csv."""
    xlsx_path = Path("india_water_quality_full.xlsx")
    csv_path = Path("india_water_quality_full.csv")

    if xlsx_path.exists():
        df = pd.read_excel(xlsx_path)
        print(f"Loaded dataset from: {xlsx_path}")
        return df

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        print(f"Loaded dataset from fallback: {csv_path}")
        return df

    raise FileNotFoundError(
        "Dataset not found. Expected 'india_water_quality_full.xlsx' "
        "or fallback 'india_water_quality_full.csv' in the workspace."
    )


def main() -> None:
    df = load_dataset()

    target_col = "Risk"
    numerical_features = ["pH", "DO", "BOD", "Nitrate", "Coliform", "Conductivity"]
    categorical_features = ["Region", "State", "District_Type"]
    input_features = numerical_features + categorical_features

    # Validate expected columns for production safety.
    required_columns = set(input_features + [target_col])
    missing_cols = sorted(required_columns - set(df.columns))
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    # Keep only expected columns and remove rows with missing target.
    model_df = df[input_features + [target_col]].copy()
    model_df = model_df.dropna(subset=[target_col])

    # Handle any missing values in features.
    for col in numerical_features:
        model_df[col] = pd.to_numeric(model_df[col], errors="coerce")
        model_df[col] = model_df[col].fillna(model_df[col].median())
    for col in categorical_features:
        model_df[col] = model_df[col].astype(str).fillna("Unknown")

    X = model_df[input_features]
    y = model_df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=42,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ("numerical", "passthrough", numerical_features),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", model),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, digits=4)
    cm = confusion_matrix(y_test, y_pred, labels=["Low", "Medium", "High"])

    print("\n=== Model Performance ===")
    print(f"Accuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(report)
    print("Confusion Matrix (rows=true, cols=pred) [Low, Medium, High]:")
    print(cm)

    with open("water_model.pkl", "wb") as f:
        pickle.dump(pipeline, f)

    with open("feature_columns.pkl", "wb") as f:
        pickle.dump(input_features, f)

    print("\nSaved files:")
    print("- water_model.pkl")
    print("- feature_columns.pkl")


if __name__ == "__main__":
    main()
