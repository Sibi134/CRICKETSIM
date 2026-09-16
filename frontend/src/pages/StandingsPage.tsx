import { useState, useEffect } from 'react';
import { tournamentService, API_URL } from '../services/api';
import { Trophy, TrendingUp, BarChart2 } from 'lucide-react';
import { TournamentStats } from '../components/TournamentStats';

export const StandingsPage = () => {
  const [standings, setStandings] = useState<any[]>([]);
  const [activeTournament, setActiveTournament] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'STANDINGS' | 'STATS'>('STANDINGS');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchStandings();
  }, []);

  const fetchStandings = async () => {
    try {
      const tournaments = await tournamentService.getAll();
      const active = tournaments.find((t: any) => t.status !== 'COMPLETED') || tournaments[0];
      
      if (active) {
        setActiveTournament(active);
        const response = await fetch(`${API_URL}/tournaments/${active.id}/standings`);
        const data = await response.json();
        setStandings(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) return <div className="text-white text-center py-10">Loading standings...</div>;
  if (!activeTournament) return <div className="text-white text-center py-10">No active tournament</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center">
            <Trophy className="mr-3 text-yellow-500 h-6 w-6" /> Tournament Center - {activeTournament.name}
          </h2>
          <p className="text-slate-400 text-sm mt-1">Standings and player statistics</p>
        </div>
        
        <div className="flex space-x-2 bg-slate-800/50 p-1 rounded-lg border border-slate-700">
          <button 
            onClick={() => setActiveTab('STANDINGS')}
            className={`px-4 py-2 rounded-md text-sm font-bold flex items-center ${activeTab === 'STANDINGS' ? 'bg-primary text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'}`}
          >
            <TrendingUp className="w-4 h-4 mr-2" /> Standings
          </button>
          <button 
            onClick={() => setActiveTab('STATS')}
            className={`px-4 py-2 rounded-md text-sm font-bold flex items-center ${activeTab === 'STATS' ? 'bg-primary text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'}`}
          >
            <BarChart2 className="w-4 h-4 mr-2" /> Leaderboards
          </button>
        </div>
      </div>

      {activeTab === 'STANDINGS' && (
        <>
          <div className="bg-surface border border-slate-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs text-slate-400 uppercase bg-slate-800 border-b border-slate-700">
              <tr>
                <th scope="col" className="px-6 py-4 font-bold">Pos</th>
                <th scope="col" className="px-6 py-4 font-bold">Team</th>
                <th scope="col" className="px-6 py-4 font-bold text-center">Pld</th>
                <th scope="col" className="px-6 py-4 font-bold text-center">W</th>
                <th scope="col" className="px-6 py-4 font-bold text-center">L</th>
                <th scope="col" className="px-6 py-4 font-bold text-center">T</th>
                <th scope="col" className="px-6 py-4 font-bold text-center">NR</th>
                <th scope="col" className="px-6 py-4 font-bold text-center text-white">Pts</th>
                <th scope="col" className="px-6 py-4 font-bold text-right">NRR</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((team, index) => (
                <tr 
                  key={team.team_id} 
                  className={`border-b border-slate-700/50 hover:bg-slate-800/50 transition-colors ${
                    index < 4 ? 'bg-emerald-900/10' : ''
                  }`}
                >
                  <td className="px-6 py-4 font-bold text-slate-400">
                    {team.position}
                    {index < 4 && <TrendingUp className="inline-block ml-2 w-3 h-3 text-emerald-500" />}
                  </td>
                  <td className="px-6 py-4 font-bold text-white">{team.team_id}</td>
                  <td className="px-6 py-4 text-center">{team.played}</td>
                  <td className="px-6 py-4 text-center text-green-400 font-medium">{team.won}</td>
                  <td className="px-6 py-4 text-center text-red-400 font-medium">{team.lost}</td>
                  <td className="px-6 py-4 text-center">{team.tied}</td>
                  <td className="px-6 py-4 text-center">{team.nr}</td>
                  <td className="px-6 py-4 text-center font-bold text-lg text-white">{team.points}</td>
                  <td className={`px-6 py-4 text-right font-mono font-medium ${team.nrr >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {team.nrr > 0 ? '+' : ''}{team.nrr.toFixed(3)}
                  </td>
                </tr>
              ))}
              {standings.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-8 text-center text-slate-500">
                    No matches played yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
          <div className="text-xs text-slate-500 flex items-center space-x-2">
            <div className="w-3 h-3 bg-emerald-900/30 rounded-full border border-emerald-500/50"></div>
            <span>Top 4 teams qualify for playoffs</span>
          </div>
        </>
      )}

      {activeTab === 'STATS' && (
        <TournamentStats tournamentId={activeTournament.id} />
      )}
    </div>
  );
};
