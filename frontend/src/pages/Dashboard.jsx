import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from "recharts";
import { api } from "../utils/api";

const RISK_COLORS = {
  critical: "#ff5e7a",
  high:     "#ff9f43",
  moderate: "#ffd166",
  low:      "#2dd4a0"
};

const TOOLTIP_STYLE = {
  background: "#1a1d25",
  border: "1px solid #252830",
  borderRadius: 10,
  color: "#e8eaf0",
  fontSize: 13
};

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getDashboard(), api.getStudents()])
      .then(([s, st]) => { setStats(s); setStudents(st.students || []); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /> Loading dashboard…</div>;

  if (!stats || stats.total_students === 0) {
    return (
      <div>
        <div className="page-header">
          <h1>Dashboard</h1>
          <p>Analytics & insights across all assessed students</p>
        </div>
        <div className="empty">
          <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>📊</div>
          <p>No students assessed yet.<br />Go to <strong>Assess Student</strong> to get started.</p>
        </div>
      </div>
    );
  }

  const pieData = [
    { name: "Critical", value: stats.risk_distribution.critical, color: RISK_COLORS.critical },
    { name: "High",     value: stats.risk_distribution.high,     color: RISK_COLORS.high },
    { name: "Moderate", value: stats.risk_distribution.moderate, color: RISK_COLORS.moderate },
    { name: "Low",      value: stats.risk_distribution.low,      color: RISK_COLORS.low },
  ].filter(d => d.value > 0);

  const importances = stats.feature_importances
    ? Object.entries(stats.feature_importances).slice(0, 10).map(([k,v]) => ({
        name: k.replace(/_/g," "), value: +(v*100).toFixed(1)
      }))
    : [];

  const radarData = [
    { axis: "Sleep",      value: ((stats.averages.sleep / 9) * 10).toFixed(1) },
    { axis: "Motivation", value: stats.averages.motivation.toFixed(1) },
    { axis: "Focus",      value: ((10 - stats.averages.anxiety) ).toFixed(1) },
    { axis: "Consistency",value: 6 },
    { axis: "Activity",   value: 5 },
  ];

  const recentStudents = students.slice(0, 5);

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Real-time burnout analytics — {stats.total_students} students assessed</p>
      </div>

      {/* Stat Cards */}
      <div className="stat-grid">
        {[
          { icon:"👥", value: stats.total_students,              label:"Total Assessed",         accent:"#6c63ff" },
          { icon:"🔥", value: `${stats.burnout_rate}%`,          label:"Burnout Rate",           accent:"#ff5e7a" },
          { icon:"🚨", value: stats.risk_distribution.critical,  label:"Critical Risk Students", accent:"#ff5e7a" },
          { icon:"⚠️", value: stats.risk_distribution.high,      label:"High Risk Students",     accent:"#ff9f43" },
          { icon:"🎯", value: `${(stats.model_accuracy*100).toFixed(1)}%`, label:"Model Accuracy", accent:"#2dd4a0" },
          { icon:"😴", value: `${stats.averages.sleep}h`,        label:"Avg Sleep / Night",      accent:"#6c63ff" },
        ].map((s,i) => (
          <div key={i} className="stat-card" style={{"--card-accent":s.accent}}>
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-value" style={{color:s.accent}}>{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="charts-grid">
        {/* Pie chart */}
        <div className="card">
          <div className="card-title">Risk Distribution</div>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={95}
                   dataKey="value" paddingAngle={3}>
                {pieData.map((entry,i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [v, "Students"]} />
              <Legend formatter={(v) => <span style={{color:"#8b90a0",fontSize:13}}>{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Radar */}
        <div className="card">
          <div className="card-title">Average Wellbeing Profile</div>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#252830" />
              <PolarAngleAxis dataKey="axis" tick={{ fill:"#8b90a0", fontSize:12 }} />
              <PolarRadiusAxis angle={30} domain={[0,10]} tick={{ fill:"#565c70", fontSize:10 }} />
              <Radar dataKey="value" stroke="#6c63ff" fill="#6c63ff" fillOpacity={0.25} strokeWidth={2} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Feature importances */}
        <div className="card" style={{gridColumn:"1 / -1"}}>
          <div className="card-title">Top Feature Importances (Random Forest)</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={importances} layout="vertical" margin={{left:20}}>
              <XAxis type="number" tick={{ fill:"#565c70", fontSize:11 }} tickFormatter={v=>`${v}%`} />
              <YAxis type="category" dataKey="name" tick={{ fill:"#8b90a0", fontSize:11 }} width={160} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v)=>[`${v}%`,"Importance"]} />
              <Bar dataKey="value" fill="#6c63ff" radius={[0,4,4,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent */}
      <div className="card" style={{marginTop:"1.25rem"}}>
        <div className="card-title">Recent Assessments</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Student</th><th>Sleep</th><th>Study Hrs</th>
                <th>Anxiety</th><th>Burnout Prob</th><th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {recentStudents.map(s => (
                <tr key={s._id}>
                  <td>
                    <div style={{fontWeight:600,color:"var(--text)"}}>{s.name}</div>
                    <div style={{fontSize:".75rem"}}>{s.email}</div>
                  </td>
                  <td>{s.sleep_hours?.toFixed(1)}h</td>
                  <td>{s.study_hours_per_day?.toFixed(1)}h</td>
                  <td>
                    <span style={{color: s.anxiety_score > 6 ? "var(--red)" : "var(--text2)"}}>
                      {s.anxiety_score?.toFixed(1)}/10
                    </span>
                  </td>
                  <td>
                    <div style={{display:"flex",alignItems:"center",gap:".5rem"}}>
                      <div className="progress-bar" style={{width:80,height:6,display:"inline-block"}}>
                        <div className="progress-fill" style={{
                          width:`${s.burnout_probability}%`,
                          background: s.burnout_probability > 75 ? "var(--red)" :
                                      s.burnout_probability > 55 ? "var(--orange)" :
                                      s.burnout_probability > 35 ? "var(--yellow)" : "var(--green)"
                        }} />
                      </div>
                      <span style={{fontSize:".8rem",color:"var(--text2)"}}>{s.burnout_probability?.toFixed(1)}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge badge-${s.risk_level?.toLowerCase()}`}>
                      {s.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}