const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = {
  predict:      (data)  => fetch(`${BASE}/predict`,          { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data) }).then(r=>r.json()),
  getStudents:  ()      => fetch(`${BASE}/students`).then(r=>r.json()),
  getDashboard: ()      => fetch(`${BASE}/dashboard-stats`).then(r=>r.json()),
  getHistory:   (email) => fetch(`${BASE}/prediction-history/${email}`).then(r=>r.json()),
  getStudent:   (id)    => fetch(`${BASE}/students/${id}`).then(r=>r.json()),
};