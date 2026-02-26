import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import QueuePage from "./pages/QueuePage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="nav">
          <h1 className="logo">Job Autopilot</h1>
          <div className="nav-links">
            <NavLink to="/" end>Search</NavLink>
            <NavLink to="/queue">Queue</NavLink>
          </div>
        </nav>
        <main className="main">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/queue" element={<QueuePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
