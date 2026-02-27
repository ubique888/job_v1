import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import QueuePage from "./pages/QueuePage";
import AlertsPage from "./pages/AlertsPage";
import * as api from "./lib/api";
import "./App.css";

function App() {
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const check = () =>
      api
        .getUnreadAlertCount()
        .then((d) => setUnreadCount(d.unread_count))
        .catch(() => {});
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <BrowserRouter>
      <div className="app">
        <nav className="nav">
          <h1 className="logo">Job Autopilot</h1>
          <div className="nav-links">
            <NavLink to="/" end>Search</NavLink>
            <NavLink to="/queue">Queue</NavLink>
            <NavLink to="/alerts">
              Alerts
              {unreadCount > 0 && <span className="nav-alert-badge">{unreadCount}</span>}
            </NavLink>
          </div>
        </nav>
        <main className="main">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/queue" element={<QueuePage />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
