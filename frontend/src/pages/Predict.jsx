import React, { useState } from "react";
import { api } from "../utils/api";

const STEPS = [
  { id: "basic", label: "Basic Info", icon: "👤" },
  { id: "study", label: "Study Habits", icon: "📚" },
  { id: "pressure", label: "Academic Pressure", icon: "🎓" },
  { id: "wellness", label: "Mental Wellness", icon: "🧠" },
  { id: "symptoms", label: "Self-Assessment", icon: "💬" },
];

const DEFAULTS = {
  name: "",
  email: "",
  age: 20,
  study_hours_per_day: 6,
  sleep_hours: 7,
  break_frequency: 3,
  study_consistency_score: 5,
  days_studied_per_week: 5,
  assignment_load: 5,
  exam_frequency: 2,
  deadline_stress: 5,
  gpa_pressure: 3.0,
  extracurricular_hours: 2,
  mood_score: 5,
  focus_level: 5,
  social_interaction_hrs: 2,
  physical_activity_hrs: 1.5,
  screen_time_non_study: 4,
  fatigue_level: 5,
  motivation_score: 5,
  anxiety_score: 5,
  concentration_difficulty: 5,
  procrastination_score: 5,
};

function RangeField({
  label,
  name,
  value,
  min,
  max,
  step = 0.1,
  hint,
  onChange,
}) {
  const pct = ((value - min) / (max - min)) * 100;
  const color =
    name.includes("anxiety") ||
    name.includes("fatigue") ||
    name.includes("stress") ||
    name.includes("procrastination") ||
    name.includes("concentration")
      ? value > 6.5
        ? "var(--red)"
        : value > 4
          ? "var(--orange)"
          : "var(--green)"
      : name.includes("sleep") ||
          name.includes("motivation") ||
          name.includes("mood") ||
          name.includes("focus")
        ? value < 5
          ? "var(--red)"
          : value < 7
            ? "var(--orange)"
            : "var(--green)"
        : "var(--accent)";

  return (
    <div className="form-group">
      <div className="form-label">
        {label} {hint && <span>({hint})</span>}
        <span style={{ marginLeft: "auto", color }} className="range-value">
          {value}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) =>
          onChange(
            name,
            step < 1 ? parseFloat(e.target.value) : parseInt(e.target.value),
          )
        }
        style={{ "--pct": `${pct}%` }}
      />
    </div>
  );
}

function ResultPanel({ result }) {
  const rl = result.risk_level?.toLowerCase();
  const recs_high =
    result.recommendations?.filter((r) => r.priority === "high") || [];
  const recs_medium =
    result.recommendations?.filter((r) => r.priority === "medium") || [];
  const recs_low =
    result.recommendations?.filter((r) => r.priority === "low") || [];

  return (
    <div className="result-panel">
      <div className={`risk-meter ${rl}`}>
        <div
          style={{
            fontSize: ".75rem",
            letterSpacing: ".12em",
            textTransform: "uppercase",
            color: "var(--text3)",
            marginBottom: ".75rem",
          }}
        >
          BURNOUT PROBABILITY
        </div>
        <div className={`risk-pct ${rl}`}>
          {result.burnout_probability?.toFixed(1)}%
        </div>
        <div className="risk-label" style={{ marginTop: ".75rem" }}>
          <span
            className={`badge badge-${rl}`}
            style={{ fontSize: ".875rem", padding: ".35rem .9rem" }}
          >
            {result.risk_level} Risk
          </span>
        </div>
        {result.burnout_predicted && (
          <div
            style={{
              marginTop: "1rem",
              padding: ".6rem 1.2rem",
              background: "var(--red-dim)",
              border: "1px solid #ff5e7a30",
              borderRadius: 8,
              fontSize: ".8375rem",
              color: "var(--red)",
              fontWeight: 500,
            }}
          >
            ⚠️ Burnout detected — immediate action recommended
          </div>
        )}
      </div>

      <div className="section-header">
        <h2>Personalized Recommendations</h2>
        <span className="tag">{result.recommendations?.length} insights</span>
      </div>

      {[
        { label: "🔴 High Priority", items: recs_high },
        { label: "🟡 Medium Priority", items: recs_medium },
        { label: "🟢 Low Priority", items: recs_low },
      ]
        .filter((g) => g.items.length > 0)
        .map((group, gi) => (
          <div key={gi} style={{ marginBottom: "1.25rem" }}>
            <div
              style={{
                fontSize: ".8125rem",
                color: "var(--text3)",
                marginBottom: ".5rem",
                fontWeight: 600,
              }}
            >
              {group.label}
            </div>
            <div className="rec-list">
              {group.items.map((r, i) => (
                <div key={i} className="rec-card">
                  <div className={`priority-dot priority-${r.priority}`} />
                  <div className="rec-icon">{r.icon}</div>
                  <div className="rec-body">
                    <div className="rec-title">{r.title}</div>
                    <div className="rec-desc">{r.description}</div>
                    <div className="rec-action">→ {r.action}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}

export default function Predict() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(DEFAULTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const setStr = (e) => set(e.target.name, e.target.value);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.predict({ ...form, age: parseInt(form.age) });
      if (res.detail) throw new Error(JSON.stringify(res.detail));
      setResult(res);
      setStep(5);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setForm(DEFAULTS);
    setResult(null);
    setStep(0);
    setError(null);
  };

  return (
    <div>
      <div className="page-header">
        <h1>Student Assessment</h1>
        <p>
          Complete the 5-section survey to predict burnout risk and receive AI
          recommendations
        </p>
      </div>

      {/* Step Tabs */}
      <div className="step-tabs">
        {STEPS.map((s, i) => (
          <button
            key={i}
            className={`step-tab ${step === i ? "active" : ""} ${step > i ? "done" : ""}`}
            onClick={() => (i < step || step === 5 ? setStep(i) : null)}
            style={{ cursor: i <= step || step === 5 ? "pointer" : "default" }}
          >
            <span className="step-num">{step > i ? "✓" : i + 1}</span>
            {s.icon} {s.label}
          </button>
        ))}
        <button
          className={`step-tab ${step === 5 ? "active" : ""}`}
          style={{ opacity: result ? 1 : 0.4 }}
        >
          📊 Results
        </button>
      </div>

      {step === 5 && result ? (
        <div>
          <ResultPanel result={result} />
          <button
            className="btn btn-ghost"
            style={{ marginTop: "1rem" }}
            onClick={reset}
          >
            ← Assess Another Student
          </button>
        </div>
      ) : (
        <div className="card">
          {/* Step 0: Basic */}
          {step === 0 && (
            <>
              <div className="section-header">
                <h2>👤 Basic Information</h2>
              </div>
              <div className="form-grid">
                <div className="form-group" style={{ gridColumn: "1/-1" }}>
                  <label className="form-label">Full Name</label>
                  <input
                    className="form-input"
                    name="name"
                    value={form.name}
                    onChange={setStr}
                    placeholder="e.g. Priya Sharma"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    className="form-input"
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={setStr}
                    placeholder="student@university.edu"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Age</label>
                  <input
                    className="form-input"
                    name="age"
                    type="number"
                    min={15}
                    max={35}
                    value={form.age}
                    onChange={(e) => set("age", parseInt(e.target.value))}
                  />
                </div>
              </div>
            </>
          )}

          {/* Step 1: Study Habits */}
          {step === 1 && (
            <>
              <div className="section-header">
                <h2>📚 Study Habits</h2>
              </div>
              <div className="form-grid">
                <RangeField
                  label="Study Hours / Day"
                  name="study_hours_per_day"
                  value={form.study_hours_per_day}
                  min={0}
                  max={16}
                  step={0.5}
                  hint="hrs"
                  onChange={set}
                />
                <RangeField
                  label="Sleep Hours / Night"
                  name="sleep_hours"
                  value={form.sleep_hours}
                  min={2}
                  max={12}
                  step={0.5}
                  hint="hrs"
                  onChange={set}
                />
                <RangeField
                  label="Break Frequency / Session"
                  name="break_frequency"
                  value={form.break_frequency}
                  min={0}
                  max={10}
                  step={1}
                  hint="breaks"
                  onChange={set}
                />
                <RangeField
                  label="Study Consistency Score"
                  name="study_consistency_score"
                  value={form.study_consistency_score}
                  min={0}
                  max={10}
                  step={0.5}
                  hint="0=random,10=very regular"
                  onChange={set}
                />
                <RangeField
                  label="Days Studied / Week"
                  name="days_studied_per_week"
                  value={form.days_studied_per_week}
                  min={0}
                  max={7}
                  step={1}
                  hint="days"
                  onChange={set}
                />
                <RangeField
                  label="Extracurricular Hours / Day"
                  name="extracurricular_hours"
                  value={form.extracurricular_hours}
                  min={0}
                  max={12}
                  step={0.5}
                  hint="hrs"
                  onChange={set}
                />
              </div>
            </>
          )}

          {/* Step 2: Academic Pressure */}
          {step === 2 && (
            <>
              <div className="section-header">
                <h2>🎓 Academic Pressure</h2>
              </div>
              <div className="form-grid">
                <RangeField
                  label="Assignment Load"
                  name="assignment_load"
                  value={form.assignment_load}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=light,10=heavy"
                  onChange={set}
                />
                <RangeField
                  label="Exam Frequency"
                  name="exam_frequency"
                  value={form.exam_frequency}
                  min={0}
                  max={10}
                  step={1}
                  hint="exams/month"
                  onChange={set}
                />
                <RangeField
                  label="Deadline Stress"
                  name="deadline_stress"
                  value={form.deadline_stress}
                  min={0}
                  max={10}
                  step={0.5}
                  hint="1=low,10=extreme"
                  onChange={set}
                />
                <RangeField
                  label="GPA Pressure"
                  name="gpa_pressure"
                  value={form.gpa_pressure}
                  min={0}
                  max={4}
                  step={0.1}
                  hint="0-4.0 scale"
                  onChange={set}
                />
              </div>
            </>
          )}

          {/* Step 3: Wellness */}
          {step === 3 && (
            <>
              <div className="section-header">
                <h2>🧠 Mental & Physical Wellness</h2>
              </div>
              <div className="form-grid">
                <RangeField
                  label="Mood Score"
                  name="mood_score"
                  value={form.mood_score}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=very low,10=excellent"
                  onChange={set}
                />
                <RangeField
                  label="Focus Level"
                  name="focus_level"
                  value={form.focus_level}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=scattered,10=laser"
                  onChange={set}
                />
                <RangeField
                  label="Social Interaction Hours"
                  name="social_interaction_hrs"
                  value={form.social_interaction_hrs}
                  min={0}
                  max={12}
                  step={0.5}
                  hint="hrs/day"
                  onChange={set}
                />
                <RangeField
                  label="Physical Activity Hours"
                  name="physical_activity_hrs"
                  value={form.physical_activity_hrs}
                  min={0}
                  max={8}
                  step={0.5}
                  hint="hrs/day"
                  onChange={set}
                />
                <RangeField
                  label="Screen Time (Non-Study)"
                  name="screen_time_non_study"
                  value={form.screen_time_non_study}
                  min={0}
                  max={14}
                  step={0.5}
                  hint="hrs/day"
                  onChange={set}
                />
              </div>
            </>
          )}

          {/* Step 4: Symptoms */}
          {step === 4 && (
            <>
              <div className="section-header">
                <h2>💬 Self-Assessment</h2>
              </div>
              <div
                style={{
                  padding: ".75rem 1rem",
                  background: "var(--accent-dim)",
                  borderRadius: 10,
                  marginBottom: "1.25rem",
                  fontSize: ".8375rem",
                  color: "var(--accent2)",
                }}
              >
                Rate honestly — this drives the accuracy of your burnout
                prediction.
              </div>
              <div className="form-grid">
                <RangeField
                  label="Fatigue Level"
                  name="fatigue_level"
                  value={form.fatigue_level}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=energetic,10=exhausted"
                  onChange={set}
                />
                <RangeField
                  label="Motivation Score"
                  name="motivation_score"
                  value={form.motivation_score}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=none,10=highly motivated"
                  onChange={set}
                />
                <RangeField
                  label="Anxiety Score"
                  name="anxiety_score"
                  value={form.anxiety_score}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=calm,10=severely anxious"
                  onChange={set}
                />
                <RangeField
                  label="Concentration Difficulty"
                  name="concentration_difficulty"
                  value={form.concentration_difficulty}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=easy,10=very hard"
                  onChange={set}
                />
                <RangeField
                  label="Procrastination Score"
                  name="procrastination_score"
                  value={form.procrastination_score}
                  min={1}
                  max={10}
                  step={0.5}
                  hint="1=none,10=severe"
                  onChange={set}
                />
              </div>
            </>
          )}

          {/* Navigation */}
          {error && (
            <div
              style={{
                marginTop: "1rem",
                padding: ".75rem 1rem",
                background: "var(--red-dim)",
                borderRadius: 10,
                color: "var(--red)",
                fontSize: ".875rem",
              }}
            >
              ⚠️ {error}
            </div>
          )}

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginTop: "1.75rem",
            }}
          >
            <button
              className="btn btn-ghost"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
            >
              ← Back
            </button>
            {step < 4 ? (
              <button
                className="btn btn-primary"
                onClick={() => {
                  if (step === 0 && (!form.name || !form.email)) {
                    setError("Name and email are required");
                    return;
                  }
                  setError(null);
                  setStep((s) => s + 1);
                }}
              >
                Next →
              </button>
            ) : (
              <button
                className="btn btn-primary btn-lg"
                onClick={submit}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div
                      className="spinner"
                      style={{ width: 16, height: 16, borderWidth: 2 }}
                    />
                    Analyzing…
                  </>
                ) : (
                  "🔍 Predict Burnout Risk"
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
