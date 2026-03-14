import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Predict from "./pages/Predict.jsx";
import Students from "./pages/Students.jsx";
import "./App.css";

function Nav() {
  return (
    <nav className="nav">
      <div className="nav-brand">
        <span className="nav-icon">⚡</span>
        <span className="nav-title">BurnoutAI</span>
      </div>
      <div className="nav-links">
        <NavLink to="/"         className={({isActive})=>"nav-link"+(isActive?" active":"")}>Dashboard</NavLink>
        <NavLink to="/predict"  className={({isActive})=>"nav-link"+(isActive?" active":"")}>Assess Student</NavLink>
        <NavLink to="/students" className={({isActive})=>"nav-link"+(isActive?" active":"")}>All Students</NavLink>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Nav />
        <main className="main">
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/predict"  element={<Predict />} />
            <Route path="/students" element={<Students />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}