import React, { useEffect, useState } from "react";
import { api } from "../utils/api";

export default function Students() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState("");
  const [filter, setFilter]     = useState("all");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    api.getStudents().then(d => setStudents(d.students || [])).finally(()=>setLoading(false));
  }, []);

  const filtered = students.filter(s => {
    const matchName  = s.name?.toLowerCase().includes(search.toLowerCase()) || s.email?.toLowerCase().includes(search.toLowerCase());
    const matchRisk  = filter==="all" || s.risk_level?.toLowerCase()===filter;
    return matchName && matchRisk;
  });

  if (loading) return <div className="loading"><div className="spinner"/>Loading students…</div>;

  if (!students.length) return (
    <div>
      <div className="page-header"><h1>All Students</h1><p>Manage and review student burnout assessments</p></div>
      <div className="empty">
        <div style={{fontSize:"3rem",marginBottom:"1rem"}}>👥</div>
        <p>No students assessed yet.<br/>Go to <strong>Assess Student</strong> to add the first one.</p>
      </div>
    </div>
  );

  return (
    <div>
      <div className="page-header">
        <h1>All Students</h1>
        <p>{students.length} students assessed — filter and review burnout profiles</p>
      </div>

      {/* Controls */}
      <div style={{display:"flex",gap:"1rem",marginBottom:"1.25rem",flexWrap:"wrap"}}>
        <input className="form-input" style={{maxWidth:300}}
               placeholder="🔍 Search by name or email…"
               value={search} onChange={e=>setSearch(e.target.value)} />
        <div style={{display:"flex",gap:".5rem"}}>
          {["all","critical","high","moderate","low"].map(f=>(
            <button key={f} className={`step-tab ${filter===f?"active":""}`}
                    onClick={()=>setFilter(f)} style={{textTransform:"capitalize"}}>
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className={selected ? "grid-2" : ""}>
        {/* Table */}
        <div className="card" style={{padding:0,overflow:"hidden"}}>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Sleep</th>
                  <th>Study</th>
                  <th>Anxiety</th>
                  <th>Motivation</th>
                  <th>Burnout %</th>
                  <th>Risk</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(s => (
                  <tr key={s._id} style={{cursor:"pointer"}}
                      onClick={()=>setSelected(selected?._id===s._id ? null : s)}>
                    <td>
                      <div style={{fontWeight:600,color:"var(--text)"}}>{s.name}</div>
                      <div style={{fontSize:".75rem",color:"var(--text3)"}}>{s.email}</div>
                    </td>
                    <td style={{color: s.sleep_hours < 6 ? "var(--red)" : s.sleep_hours < 7 ? "var(--orange)" : "var(--green)"}}>
                      {s.sleep_hours?.toFixed(1)}h
                    </td>
                    <td>{s.study_hours_per_day?.toFixed(1)}h</td>
                    <td style={{color: s.anxiety_score > 7 ? "var(--red)" : s.anxiety_score > 5 ? "var(--orange)" : "var(--green)"}}>
                      {s.anxiety_score?.toFixed(1)}
                    </td>
                    <td style={{color: s.motivation_score < 4 ? "var(--red)" : s.motivation_score < 6 ? "var(--orange)" : "var(--green)"}}>
                      {s.motivation_score?.toFixed(1)}
                    </td>
                    <td>
                      <div style={{display:"flex",alignItems:"center",gap:".4rem"}}>
                        <div style={{width:50,height:5,background:"var(--bg3)",borderRadius:3,overflow:"hidden"}}>
                          <div style={{height:"100%",width:`${s.burnout_probability}%`,borderRadius:3,
                            background: s.burnout_probability>75?"var(--red)":s.burnout_probability>55?"var(--orange)":s.burnout_probability>35?"var(--yellow)":"var(--green)"
                          }}/>
                        </div>
                        <span style={{fontSize:".8rem"}}>{s.burnout_probability?.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge badge-${s.risk_level?.toLowerCase()}`}>{s.risk_level}</span>
                    </td>
                    <td style={{color:"var(--text3)",fontSize:".8rem"}}>
                      {selected?._id===s._id ? "▲" : "▼"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length===0 && <div className="empty" style={{padding:"2rem"}}>No students match your filters.</div>}
          </div>
        </div>

        {/* Detail Panel */}
        {selected && (
          <div className="card" style={{alignSelf:"start",animation:"slideUp .3s ease"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",marginBottom:"1rem"}}>
              <div>
                <div style={{fontFamily:"'Syne',sans-serif",fontWeight:800,fontSize:"1.1rem"}}>{selected.name}</div>
                <div style={{fontSize:".8125rem",color:"var(--text3)"}}>{selected.email} · Age {selected.age}</div>
              </div>
              <span className={`badge badge-${selected.risk_level?.toLowerCase()}`} style={{fontSize:".8rem"}}>
                {selected.risk_level}
              </span>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:".75rem",marginBottom:"1.25rem"}}>
              {[
                {l:"Burnout Prob",    v:`${selected.burnout_probability?.toFixed(1)}%`, hi: selected.burnout_probability>60 },
                {l:"Sleep",          v:`${selected.sleep_hours?.toFixed(1)}h`,           hi: selected.sleep_hours<6 },
                {l:"Study Hrs/Day",  v:`${selected.study_hours_per_day?.toFixed(1)}h`,   hi: selected.study_hours_per_day>9 },
                {l:"Anxiety",        v:`${selected.anxiety_score?.toFixed(1)}/10`,        hi: selected.anxiety_score>6 },
                {l:"Motivation",     v:`${selected.motivation_score?.toFixed(1)}/10`,     hi: selected.motivation_score<4 },
                {l:"Fatigue",        v:`${selected.fatigue_level?.toFixed(1)}/10`,        hi: selected.fatigue_level>7 },
              ].map((m,i)=>(
                <div key={i} style={{background:"var(--bg3)",borderRadius:10,padding:".75rem 1rem"}}>
                  <div style={{fontSize:".75rem",color:"var(--text3)",marginBottom:".2rem"}}>{m.l}</div>
                  <div style={{fontWeight:700,color:m.hi?"var(--red)":"var(--text)"}}>{m.v}</div>
                </div>
              ))}
            </div>

            <div style={{fontSize:".8125rem",color:"var(--text3)",fontWeight:600,marginBottom:".6rem",textTransform:"uppercase",letterSpacing:".07em"}}>
              Top Recommendations
            </div>
            <div className="rec-list">
              {selected.recommendations?.slice(0,3).map((r,i)=>(
                <div key={i} className="rec-card" style={{padding:".75rem"}}>
                  <div className="rec-icon" style={{fontSize:"1.2rem"}}>{r.icon}</div>
                  <div>
                    <div className="rec-title" style={{fontSize:".875rem"}}>{r.title}</div>
                    <div className="rec-action" style={{fontSize:".8rem"}}>→ {r.action}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}