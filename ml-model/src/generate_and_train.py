import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib
import json
import os

np.random.seed(42)
N = 2000

def generate_dataset(n=N):
    study_hours_per_day     = np.random.normal(6, 2, n).clip(0, 16)
    sleep_hours             = np.random.normal(7, 1.5, n).clip(3, 10)
    break_frequency         = np.random.randint(0, 6, n)
    study_consistency_score = np.random.uniform(0, 10, n)
    days_studied_per_week   = np.random.randint(1, 8, n)
    assignment_load         = np.random.randint(1, 11, n)
    exam_frequency          = np.random.randint(0, 5, n)
    deadline_stress         = np.random.uniform(0, 10, n)
    gpa_pressure            = np.random.uniform(2.0, 4.0, n)
    extracurricular_hours   = np.random.normal(3, 2, n).clip(0, 12)
    mood_score              = np.random.uniform(1, 10, n)
    focus_level             = np.random.uniform(1, 10, n)
    social_interaction_hrs  = np.random.normal(2, 1.5, n).clip(0, 8)
    physical_activity_hrs   = np.random.normal(1.5, 1, n).clip(0, 5)
    screen_time_non_study   = np.random.normal(4, 2, n).clip(0, 14)
    fatigue_level           = np.random.uniform(1, 10, n)
    motivation_score        = np.random.uniform(1, 10, n)
    anxiety_score           = np.random.uniform(1, 10, n)
    concentration_difficulty= np.random.uniform(1, 10, n)
    procrastination_score   = np.random.uniform(1, 10, n)

    burnout_risk_score = (
        (study_hours_per_day > 9).astype(float) * 1.5 +
        (sleep_hours < 6).astype(float) * 2.0 +
        (break_frequency < 2).astype(float) * 1.0 +
        (study_consistency_score < 4).astype(float) * 0.8 +
        (assignment_load > 7).astype(float) * 1.5 +
        (deadline_stress > 7).astype(float) * 1.5 +
        (mood_score < 4).astype(float) * 1.2 +
        (fatigue_level > 7).astype(float) * 2.0 +
        (motivation_score < 4).astype(float) * 1.5 +
        (anxiety_score > 7).astype(float) * 1.8 +
        (concentration_difficulty > 7).astype(float) * 1.2 +
        (physical_activity_hrs < 0.5).astype(float) * 0.5 +
        (screen_time_non_study > 8).astype(float) * 0.8
    )

    burnout_risk_score = (burnout_risk_score - burnout_risk_score.min()) / (burnout_risk_score.max() - burnout_risk_score.min())
    noise = np.random.normal(0, 0.05, n)
    burnout_label = ((burnout_risk_score + noise) > 0.45).astype(int)

    df = pd.DataFrame({
        "study_hours_per_day": study_hours_per_day,
        "sleep_hours": sleep_hours,
        "break_frequency": break_frequency,
        "study_consistency_score": study_consistency_score,
        "days_studied_per_week": days_studied_per_week,
        "assignment_load": assignment_load,
        "exam_frequency": exam_frequency,
        "deadline_stress": deadline_stress,
        "gpa_pressure": gpa_pressure,
        "extracurricular_hours": extracurricular_hours,
        "mood_score": mood_score,
        "focus_level": focus_level,
        "social_interaction_hrs": social_interaction_hrs,
        "physical_activity_hrs": physical_activity_hrs,
        "screen_time_non_study": screen_time_non_study,
        "fatigue_level": fatigue_level,
        "motivation_score": motivation_score,
        "anxiety_score": anxiety_score,
        "concentration_difficulty": concentration_difficulty,
        "procrastination_score": procrastination_score,
        "burnout_risk_score": (burnout_risk_score * 100).round(2),
        "burnout_label": burnout_label
    })
    return df


def train_model(df):
    features = [c for c in df.columns if c not in ["burnout_label", "burnout_risk_score"]]
    X = df[features]
    y = df["burnout_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200, max_depth=12,
        min_samples_split=5, min_samples_leaf=2,
        random_state=42, class_weight="balanced"
    )
    model.fit(X_train_s, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_s))
    print(f"Model Accuracy: {acc:.4f}")

    importances = dict(zip(features, model.feature_importances_.tolist()))
    importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    return model, scaler, features, acc, importances


if __name__ == "__main__":
    print("Generating dataset...")
    df = generate_dataset()
    df.to_csv("dataset.csv", index=False)
    print(f"Dataset: {len(df)} records, burnout rate = {df.burnout_label.mean()*100:.1f}%")

    print("Training Random Forest...")
    model, scaler, features, acc, importances = train_model(df)

    joblib.dump(model,  "burnout_model.pkl")
    joblib.dump(scaler, "scaler.pkl")

    with open("model_meta.json", "w") as f:
        json.dump({"features": features, "accuracy": round(acc, 4), "importances": importances}, f, indent=2)

    print("Saved: burnout_model.pkl, scaler.pkl, model_meta.json")
    print("Done!")