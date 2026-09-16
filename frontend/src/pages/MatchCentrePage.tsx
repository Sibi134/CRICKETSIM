import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { API_URL } from '../services/api';
import { Activity, Trophy, FastForward } from 'lucide-react';
import { Scorecard } from '../components/Scorecard';

export const MatchCentrePage = () => {
  const { matchId } = useParams();
  const [match, setMatch] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchMatch();
  }, [matchId]);

  const fetchMatch = async () => {
    try {
      const response = await fetch(`${API_URL}/matches/${matchId}`);
      const data = await response.json();
      setMatch(data);
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSimulate = async (overs: string) => {
    setIsSimulating(true);
    try {
      await fetch(`${API_URL}/matches/${matchId}/simulate/${overs}`, {
        method: 'POST'
      });
      await fetchMatch();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  if (!match) return <div className="text-white py-10 text-center">Loading match...</div>;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-surface border border-slate-700 rounded-xl overflow-hidden shadow-2xl">
        <div className="bg-slate-800/80 p-4 border-b border-slate-700 flex justify-between items-center">
          <span className="text-slate-400 font-medium text-sm flex items-center">
            <Activity className="mr-2 h-4 w-4 text-primary" /> Match Centre
          </span>
          <span className={`text-xs font-bold px-3 py-1 rounded-full ${
            match.status === 'COMPLETED' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400 animate-pulse'
          }`}>
            {match.status}
          </span>
        </div>

        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center text-center">
            {/* Team 1 */}
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">{match.team1_id}</h2>
              <div className="text-5xl font-mono text-slate-100 font-bold">
                {match.team1_score}<span className="text-3xl text-slate-400">/{match.team1_wickets}</span>
              </div>
              <div className="text-slate-400 mt-2 font-mono">({match.team1_overs.toFixed(1)} Overs)</div>
            </div>

            {/* VS & Info */}
            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="h-12 w-12 rounded-full bg-slate-700 flex items-center justify-center text-slate-300 font-bold text-xl">
                VS
              </div>
              
              {match.status === 'COMPLETED' ? (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-emerald-400 text-sm font-bold flex flex-col items-center">
                  <Trophy className="h-5 w-5 mb-1" />
                  {match.winner} WON
                </div>
              ) : (
                <div className="text-slate-400 text-sm">
                  {match.toss_winner} won toss and chose to {match.toss_decision}
                </div>
              )}
            </div>

            {/* Team 2 */}
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">{match.team2_id}</h2>
              <div className="text-5xl font-mono text-slate-100 font-bold">
                {match.team2_score}<span className="text-3xl text-slate-400">/{match.team2_wickets}</span>
              </div>
              <div className="text-slate-400 mt-2 font-mono">({match.team2_overs.toFixed(1)} Overs)</div>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      {match.status !== 'COMPLETED' && (
        <div className="bg-surface border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Simulation Controls</h3>
          <div className="flex flex-wrap gap-4">
            <button
              disabled={isSimulating}
              onClick={() => handleSimulate('1-over')}
              className="flex-1 min-w-[150px] py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg border border-slate-600 flex justify-center items-center disabled:opacity-50"
            >
              <FastForward className="mr-2 h-4 w-4" /> Simulate 1 Over
            </button>
            <button
              disabled={isSimulating}
              onClick={() => handleSimulate('5-overs')}
              className="flex-1 min-w-[150px] py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg border border-slate-600 flex justify-center items-center disabled:opacity-50"
            >
              <FastForward className="mr-2 h-4 w-4" /> Simulate 5 Overs
            </button>
            <button
              disabled={isSimulating}
              onClick={() => handleSimulate('10-overs')}
              className="flex-1 min-w-[150px] py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg border border-slate-600 flex justify-center items-center disabled:opacity-50"
            >
              <FastForward className="mr-2 h-4 w-4" /> Simulate 10 Overs
            </button>
            <button
              disabled={isSimulating}
              onClick={() => handleSimulate('innings')}
              className="flex-1 min-w-[150px] py-3 bg-primary hover:bg-blue-600 text-white font-medium rounded-lg shadow-lg flex justify-center items-center disabled:opacity-50"
            >
              <FastForward className="mr-2 h-4 w-4" /> Simulate Innings
            </button>
          </div>
        </div>
      )}

      {/* Scorecard */}
      <Scorecard matchId={matchId!} refreshTrigger={refreshTrigger} />
    </div>
  );
};
