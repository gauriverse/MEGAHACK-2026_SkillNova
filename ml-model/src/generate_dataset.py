import pandas as pd
import numpy as np
import os
 
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(BASE, "dataset", "raw_synthetic.csv")
 
np.random.seed(42)
N = 5000
 
print("=" * 60)
print("STEP 1 — Generating Synthetic Dataset (N=5000)")
print("=" * 60)
 
# ── Demographics ───────────────────────────────────────────────────────────
age       = np.random.randint(15, 31, N)
weight    = np.random.uniform(45, 120, N).round(1)
gender    = np.random.choice([0, 1, 2], N, p=[0.45, 0.50, 0.05])
edu_level = np.random.choice([1, 2, 3, 4], N, p=[0.25, 0.45, 0.20, 0.10])
 
# ── Behavioral Features ────────────────────────────────────────────────────
# Study hours: mix of low and high to create realistic extremes
# WHY two groups? Some students under-study (1-5), some overwork (7-14)
study_low  = np.random.normal(4.5, 1.5, N // 2)
study_high = np.random.normal(8.5, 2.5, N // 2)
study_hours = np.clip(np.concatenate([study_low, study_high]), 1, 14).round(1)
np.random.shuffle(study_hours)
 
# Sleep hours: mix of healthy and deprived sleepers
# WHY two groups? Sleep deprivation is a key burnout driver
sleep_ok   = np.random.normal(7.5, 1.0, N // 2)
sleep_poor = np.random.normal(4.8, 1.2, N // 2)
sleep_hours = np.clip(np.concatenate([sleep_ok, sleep_poor]), 3, 10).round(1)
np.random.shuffle(sleep_hours)
 
# ── Vibe Scales 1–5 (Likert-style survey responses) ───────────────────────
# WHY normal + clip + round? Realistic bell-curve distribution
# around middle values, clipped to valid range, rounded to integers
def vibe(mean, std=1.2):
    return np.clip(np.round(np.random.normal(mean, std, N)), 1, 5).astype(int)
 
overwhelmed_freq   = vibe(3.3)   # slightly above middle — common complaint
motivation_level   = vibe(2.9)   # slightly below — students often feel unmotivated
mental_exhaustion  = vibe(3.4)   # higher — key burnout symptom
concentration_diff = vibe(3.0)
exam_anxiety       = vibe(3.2)   # above middle — exams cause stress
schedule_balance   = vibe(2.7)   # below middle — most feel schedule is chaotic
procrastination    = vibe(3.5)   # above middle — very common
 
# ── Symptom Score (0–7) ────────────────────────────────────────────────────
# Higher exhaustion + overwhelm = more physical/mental symptoms checked
symptom_base = (
    (mental_exhaustion / 5) * 3.0 +
    (overwhelmed_freq  / 5) * 2.0 +
    np.random.uniform(0, 2, N)
)
symptom_score = np.clip(np.round(symptom_base), 0, 7).astype(int)
 
# ── Target Label: burnout_risk ─────────────────────────────────────────────
# Spec rules applied in priority order (High > Medium > Low):
#
#   LOW    = sleep_hours > 7  AND motivation_level >= 4    (good baseline)
#   MEDIUM = schedule_balance < 3 OR exam_anxiety >= 4     (warning signs)
#   HIGH   = study_hours > 10 AND sleep_hours < 5
#            AND mental_exhaustion >= 4                    (crisis state)
#
# Priority: HIGH overrides MEDIUM overrides LOW
labels = np.full(N, "Medium", dtype=object)
 
low_mask    = (sleep_hours > 7)    & (motivation_level >= 4)
medium_mask = (schedule_balance < 3) | (exam_anxiety >= 4)
high_mask   = (study_hours > 10)   & (sleep_hours < 5) & (mental_exhaustion >= 4)
 
labels[low_mask]    = "Low"
labels[medium_mask] = "Medium"
labels[high_mask]   = "High"   # applied last — highest priority
 
# ── Build DataFrame ────────────────────────────────────────────────────────
df = pd.DataFrame({
    "age"               : age,
    "weight"            : weight,
    "gender"            : gender,
    "edu_level"         : edu_level,
    "study_hours"       : study_hours,
    "sleep_hours"       : sleep_hours,
    "overwhelmed_freq"  : overwhelmed_freq,
    "motivation_level"  : motivation_level,
    "mental_exhaustion" : mental_exhaustion,
    "concentration_diff": concentration_diff,
    "exam_anxiety"      : exam_anxiety,
    "schedule_balance"  : schedule_balance,
    "procrastination"   : procrastination,
    "symptom_score"     : symptom_score,
    "burnout_risk"      : labels,
})
 
# ── Summary ────────────────────────────────────────────────────────────────
print(f"\n  Shape : {df.shape}  |  Nulls: {df.isnull().sum().sum()}")
print(f"\n  Burnout Risk Distribution:")
vc = df["burnout_risk"].value_counts()
for label in ["Low", "Medium", "High"]:
    count = vc.get(label, 0)
    print(f"    {label:<8}: {count:>5}  ({count/N*100:.1f}%)")
 
print(f"\n  Key feature stats:")
for col in ["study_hours", "sleep_hours", "mental_exhaustion",
            "exam_anxiety", "schedule_balance", "symptom_score"]:
    print(f"    {col:<22}: "
          f"min={df[col].min():.1f}  "
          f"max={df[col].max():.1f}  "
          f"mean={df[col].mean():.2f}")
 
df.to_csv(OUT, index=False)
print(f"\n  Saved → dataset/raw_synthetic.csv")
print("✅ Dataset generation complete!")