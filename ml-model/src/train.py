import pandas as pd
import numpy as np
import json, os, warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection   import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing     import StandardScaler, LabelEncoder
from sklearn.ensemble          import RandomForestClassifier
from sklearn.pipeline          import Pipeline
from sklearn.compose           import ColumnTransformer
from sklearn.preprocessing     import FunctionTransformer
from sklearn.metrics           import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score
)
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# ── Paths ──────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE, "dataset", "raw_synthetic.csv")
MODEL_OUT  = os.path.join(BASE, "models", "burnout_model.joblib")
REPORT_DIR = os.path.join(BASE, "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ── All 14 input features (from spec) ─────────────────────────────────────
ALL_FEATURES = [
    "age", "weight", "gender", "edu_level",
    "study_hours", "sleep_hours",
    "overwhelmed_freq", "motivation_level", "mental_exhaustion",
    "concentration_diff", "exam_anxiety", "schedule_balance",
    "procrastination", "symptom_score",
]

# Features to scale with StandardScaler (spec: age and weight)
# WHY only age and weight? The vibe scales (1–5) and hours are already
# in bounded ranges. Scaling them would remove interpretability.
# Age (15–30) and weight (45–120) have different units and larger ranges.
SCALE_FEATURES    = ["age", "weight"]
PASSTHROUGH_FEATURES = [f for f in ALL_FEATURES if f not in SCALE_FEATURES]

TARGET = "burnout_risk"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Load Data
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("STEP 1 — Load Dataset")
print("=" * 65)

df = pd.read_csv(DATA_PATH)
print(f"  Shape  : {df.shape}")
print(f"  Nulls  : {df.isnull().sum().sum()}")
print(f"\n  Class Distribution:")
vc = df[TARGET].value_counts()
for label in ["Low", "Medium", "High"]:
    count = vc.get(label, 0)
    print(f"    {label:<8}: {count:>5}  ({count/len(df)*100:.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Encode Target Label
#
# WHY encode? Scikit-learn needs numeric labels.
# Low=0, Medium=1, High=2 (alphabetical — LabelEncoder default)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 2 — Encode Target + Prepare Features")
print("=" * 65)

le = LabelEncoder()
y = le.fit_transform(df[TARGET])
X = df[ALL_FEATURES]

# Save label encoding for backend
label_map = {str(i): label for i, label in enumerate(le.classes_)}
print(f"  Label encoding: {label_map}")
print(f"  Features: {ALL_FEATURES}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Train / Test Split (80/20, stratified)
#
# WHY stratify? Class imbalance exists (mostly Medium).
# Without stratify, test set could have 0 High samples.
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 3 — Train / Test Split  (80 / 20, stratified)")
print("=" * 65)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"  Train: {len(X_train)}  |  Test: {len(X_test)}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Build Preprocessing + Model Pipeline
#
# WHY ColumnTransformer?
#   Applies StandardScaler only to age and weight (as per spec),
#   passes all other features through unchanged.
#   Keeping it in a Pipeline ensures the same scaler is applied at
#   inference time — no data leakage, no manual scaling needed later.
#
# WHY class_weight='balanced'?
#   We have ~95% Medium, ~3% Low, ~2% High.
#   Without weighting, the model learns to always predict Medium
#   and gets 95% accuracy — but completely misses High/Low.
#   'balanced' auto-weights each class inversely to its frequency.
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 4 — Build Pipeline (Preprocessor + RandomForest)")
print("=" * 65)

preprocessor = ColumnTransformer(
    transformers=[
        ("scale",       StandardScaler(),               SCALE_FEATURES),
        ("passthrough", "passthrough",  PASSTHROUGH_FEATURES),
    ],
    remainder="drop"
)

# Spec: n_estimators=100
# Added: class_weight='balanced' to handle imbalanced classes
model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier",   RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",    # handles class imbalance (Low/High rare)
        random_state=42,
        n_jobs=-1,
    )),
])

print(f"  Preprocessor: StandardScaler on {SCALE_FEATURES}")
print(f"  Passthrough : {PASSTHROUGH_FEATURES}")
print(f"  Classifier  : RandomForestClassifier(n_estimators=100, class_weight='balanced')")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Cross-Validation (5-fold)
#
# WHY cross-validate before final training?
#   A single train/test split can be lucky or unlucky.
#   5-fold CV gives a reliable estimate of true model performance
#   by training on 5 different splits and averaging.
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 5 — 5-Fold Stratified Cross-Validation")
print("=" * 65)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train, y_train, cv=cv,
                             scoring="accuracy", n_jobs=-1)

print(f"  CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"  Per fold   : {[f'{s:.4f}' for s in cv_scores]}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Train Final Model + Evaluate on Test Set
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 6 — Train Final Model + Evaluate")
print("=" * 65)

model.fit(X_train, y_train)
y_pred = model.predict(X_test)

test_acc = accuracy_score(y_test, y_pred)
test_f1  = f1_score(y_test, y_pred, average="weighted")

print(f"\n  Test Accuracy : {test_acc:.4f}  (target > 0.85)")
print(f"  Test F1 (wt.) : {test_f1:.4f}")

# Accuracy target check
acc_icon = "✅" if test_acc > 0.85 else "⚠️  Below target — see notes below"
print(f"\n  Accuracy target > 85%: {acc_icon}")

print(f"\n  Classification Report:")
print(classification_report(
    y_test, y_pred,
    target_names=le.classes_,
    digits=4
))

print("  Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
cm_df = pd.DataFrame(cm,
    index=[f"Actual {c}" for c in le.classes_],
    columns=[f"Pred {c}" for c in le.classes_]
)
print(cm_df.to_string())

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Feature Importance
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 7 — Feature Importances")
print("=" * 65)

# Get feature names after ColumnTransformer
rf       = model.named_steps["classifier"]
feat_names = SCALE_FEATURES + PASSTHROUGH_FEATURES
importances = pd.Series(rf.feature_importances_, index=feat_names)
importances = importances.sort_values(ascending=False)

print(f"\n  {'Feature':<25} {'Importance':>10}")
print("  " + "-" * 37)
for feat, imp in importances.items():
    bar = "█" * int(imp * 100)
    print(f"  {feat:<25} {imp:>10.4f}  {bar}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Save Evaluation Plots
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(17, 5))
fig.patch.set_facecolor("#0f172a")
BG, GRID, TEXT = "#0f172a", "#1e293b", "#e2e8f0"

for ax in axes:
    ax.set_facecolor(GRID)
    for s in ["top","right"]: ax.spines[s].set_visible(False)
    for s in ["bottom","left"]: ax.spines[s].set_color("#334155")
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.yaxis.label.set_color(TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)

# Confusion matrix
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[0],
            xticklabels=le.classes_, yticklabels=le.classes_,
            annot_kws={"color": "white", "size": 12})
axes[0].set_title("Confusion Matrix", fontweight="bold")
axes[0].set_xlabel("Predicted"); axes[0].set_ylabel("Actual")

# Feature importance
colors = ["#f472b6" if i < 5 else "#38bdf8" for i in range(len(importances))]
axes[1].barh(importances.index[::-1], importances.values[::-1], color=colors[::-1])
axes[1].set_title("Feature Importances (Random Forest)", fontweight="bold")
axes[1].set_xlabel("Importance")
axes[1].tick_params(axis="y", labelsize=8, colors=TEXT)

# Class distribution
class_counts = pd.Series(y_train).value_counts().sort_index()
bar_colors = ["#34d399", "#fb923c", "#f472b6"]
axes[2].bar(le.classes_, class_counts.values, color=bar_colors, width=0.5)
for i, (cls, cnt) in enumerate(zip(le.classes_, class_counts.values)):
    axes[2].text(i, cnt + 10, str(cnt), ha="center", color=TEXT, fontweight="bold")
axes[2].set_title("Training Class Distribution", fontweight="bold")
axes[2].set_ylabel("Count")

fig.suptitle(
    f"SkillNova Burnout Predictor — RandomForest  |  "
    f"Acc: {test_acc:.3f}  F1: {test_f1:.3f}",
    color="white", fontsize=13, fontweight="bold"
)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_DIR, "training_report.png"),
            dpi=130, bbox_inches="tight", facecolor=BG)
print(f"\n  Saved → reports/training_report.png")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Export Model
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 9 — Export Model")
print("=" * 65)

# Save model
joblib.dump(model, MODEL_OUT)
print(f"  Saved → models/burnout_model.joblib")

# Save label encoder + metadata for backend
meta = {
    "label_encoder"    : label_map,
    "features"         : ALL_FEATURES,
    "scale_features"   : SCALE_FEATURES,
    "model_type"       : "RandomForestClassifier",
    "n_estimators"     : 100,
    "class_weight"     : "balanced",
    "test_accuracy"    : round(test_acc, 4),
    "test_f1_weighted" : round(test_f1,  4),
    "cv_accuracy_mean" : round(cv_scores.mean(), 4),
    "cv_accuracy_std"  : round(cv_scores.std(), 4),
}
meta_path = os.path.join(BASE, "models", "model_metadata.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"  Saved → models/model_metadata.json")

# ── Verify model loads and predicts correctly ──────────────────────────────
print("\n  Verification check:")
loaded = joblib.load(MODEL_OUT)
sample = pd.DataFrame([{
    "age": 22, "weight": 68, "gender": 1, "edu_level": 2,
    "study_hours": 12, "sleep_hours": 4.5,
    "overwhelmed_freq": 5, "motivation_level": 1,
    "mental_exhaustion": 5, "concentration_diff": 4,
    "exam_anxiety": 5, "schedule_balance": 1,
    "procrastination": 5, "symptom_score": 6,
}])
pred_encoded = loaded.predict(sample)[0]
pred_label   = le.inverse_transform([pred_encoded])[0]
pred_proba   = loaded.predict_proba(sample)[0]
proba_dict   = {le.classes_[i]: round(float(p), 4) for i, p in enumerate(pred_proba)}
print(f"    Sample (overworked, sleep-deprived) → Predicted: {pred_label}")
print(f"    Probabilities: {proba_dict}")

print(f"\n{'='*65}")
print(f"  TRAINING COMPLETE")
print(f"  Model     : RandomForestClassifier (n_estimators=100)")
print(f"  Accuracy  : {test_acc:.4f}")
print(f"  F1 Score  : {test_f1:.4f}")
print(f"  CV Acc    : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"  Saved     : models/burnout_model.joblib")
print(f"{'='*65}")