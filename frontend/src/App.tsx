import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { TeamsPage } from './pages/TeamsPage';
import { TournamentSetupPage } from './pages/TournamentSetupPage';
import { SchedulePage } from './pages/SchedulePage';
import { MatchSetupPage } from './pages/MatchSetupPage';
import { MatchCentrePage } from './pages/MatchCentrePage';
import { StandingsPage } from './pages/StandingsPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<TournamentSetupPage />} />
          <Route path="teams" element={<TeamsPage />} />
          <Route path="schedule" element={<SchedulePage />} />
          <Route path="match/:matchId/setup" element={<MatchSetupPage />} />
          <Route path="match/:matchId" element={<MatchCentrePage />} />
          <Route path="standings" element={<StandingsPage />} />
          <Route path="live" element={<div className="text-white">Live Matches (Coming Soon)</div>} />
          <Route path="playoffs" element={<div className="text-white">Playoffs (Coming Soon)</div>} />
          <Route path="history" element={<div className="text-white">History (Coming Soon)</div>} />
          <Route path="settings" element={<div className="text-white">Settings (Coming Soon)</div>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
