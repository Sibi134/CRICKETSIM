import { useState, useEffect } from 'react';
import { tournamentService, teamService, API_URL } from '../services/api';
import { Calendar } from 'lucide-react';
import { Link } from 'react-router-dom';

export const SchedulePage = () => {
  const [matches, setMatches] = useState<any[]>([]);
  const [teamsMap, setTeamsMap] = useState<Record<string, string>>({});
  const [activeTournament, setActiveTournament] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSchedule();
  }, []);

  const fetchSchedule = async () => {
    try {
      const allTeams = await teamService.getTeams();
      const map: Record<string, string> = {};
      allTeams.forEach((t: any) => map[t.id] = t.name);
      setTeamsMap(map);

      const tournaments = await tournamentService.getAll();
      const active = tournaments.find((t: any) => t.status !== 'COMPLETED') || tournaments[0];
      
      if (active) {
        setActiveTournament(active);
        const response = await fetch(`${API_URL}/matches/tournament/${active.id}`);
        const data = await response.json();
        setMatches(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) return <div className="text-white text-center py-10">Loading schedule...</div>;

  if (!activeTournament) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-slate-700 rounded-xl">
        <Calendar className="mx-auto h-12 w-12 text-slate-500" />
        <h3 className="mt-2 text-sm font-medium text-white">No active tournament</h3>
        <p className="mt-1 text-sm text-slate-400">Create a tournament and generate a schedule first.</p>
        <div className="mt-6">
          <Link to="/" className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-blue-600">
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Schedule - {activeTournament.name}</h2>
        <p className="text-slate-400 text-sm mt-1">League stage matches</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {matches.map((match) => (
          <div key={match.id} className="bg-surface border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors">
            <div className="flex justify-between items-center mb-4">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Match {match.match_number}</span>
              <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                match.status === 'UPCOMING' ? 'bg-blue-500/10 text-blue-400' :
                match.status === 'LIVE' ? 'bg-red-500/10 text-red-400' :
                'bg-green-500/10 text-green-400'
              }`}>
                {match.status}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-lg font-bold text-white">{teamsMap[match.team1_id] || match.team1_id}</span>
                {match.status === 'COMPLETED' && <span className="text-slate-300 font-mono">{match.team1_score}/{match.team1_wickets}</span>}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-lg font-bold text-white">{teamsMap[match.team2_id] || match.team2_id}</span>
                {match.status === 'COMPLETED' && <span className="text-slate-300 font-mono">{match.team2_score}/{match.team2_wickets}</span>}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-700 flex justify-between items-center">
              <span className="text-xs text-slate-400">{new Date(match.scheduled_date).toLocaleDateString()}</span>
              {match.status !== 'COMPLETED' ? (
                <Link to={`/match/${match.id}/setup`} className="text-sm text-primary hover:text-blue-400 font-medium">
                  Match Setup →
                </Link>
              ) : (
                <Link to={`/match/${match.id}`} className="text-sm text-secondary hover:text-emerald-400 font-medium">
                  View Scorecard →
                </Link>
              )}
            </div>
          </div>
        ))}
        {matches.length === 0 && (
          <div className="col-span-full py-10 text-center text-slate-400">
            No matches scheduled for this tournament yet.
          </div>
        )}
      </div>
    </div>
  );

};
