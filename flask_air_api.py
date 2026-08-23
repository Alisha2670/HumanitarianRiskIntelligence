import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from app_air_predictor import predict_with_explanation

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent


@app.get("/")
def home():
    return render_template("air_index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "air-quality-api"}), 200


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "error": "Invalid JSON body. Send a JSON object with location and condition fields."
                }
            ),
            400,
        )

    required_location_fields = ["Region", "State", "District_Type"]
    missing = [field for field in required_location_fields if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        (
            quality_label,
            class_probabilities,
            estimated_features,
            health_advisory,
        ) = predict_with_explanation(payload)
    except Exception as exc:  # pragma: no cover - defensive API error handling
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    response = {
        "predicted_air_quality": quality_label,
        "class_probabilities": class_probabilities,
        "estimated_scientific_features": estimated_features,
        "health_advisory": health_advisory,
        "input_used": payload,
    }
    return jsonify(response), 200


if __name__ == "__main__":
    model_path = BASE_DIR / "air_model.pkl"
    feature_path = BASE_DIR / "air_feature_columns.pkl"
    if not model_path.exists() or not feature_path.exists():
        print("Startup error: required files not found in project folder:")
        print(f"- {model_path}")
        print(f"- {feature_path}")
        raise SystemExit(1)

    host = os.getenv("AIR_API_HOST", "127.0.0.1")
    port = int(os.getenv("AIR_API_PORT", "5001"))
    print(f"Starting air-quality API at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
