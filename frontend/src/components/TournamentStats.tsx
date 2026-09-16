import { useState, useEffect } from 'react';
import { API_URL } from '../services/api';

export const TournamentStats = ({ tournamentId }: { tournamentId: string }) => {
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'AWARDS' | 'BATTING' | 'BOWLING' | 'FIELDING'>('AWARDS');

  useEffect(() => {
    fetchStats();
  }, [tournamentId]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/tournaments/${tournamentId}/stats`);
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error(err);
    }
  };

  if (!stats) return <div className="text-slate-500 py-4">Loading stats...</div>;

  const topBatter = stats.batting?.[0];
  const topBowler = stats.bowling?.[0];

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex border-b border-slate-700 overflow-x-auto">
        {['AWARDS', 'BATTING', 'BOWLING', 'FIELDING'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab as any)} 
            className={`px-6 py-4 text-sm font-bold whitespace-nowrap border-b-2 ${activeTab === tab ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800'}`}
          >
            {tab === 'AWARDS' ? '🏆 AWARDS' : tab.charAt(0) + tab.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-slate-700 rounded-xl overflow-hidden p-6">
        {activeTab === 'AWARDS' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-r from-orange-500/10 to-orange-600/5 border border-orange-500/30 rounded-xl p-6 text-center shadow-lg">
              <div className="flex items-center justify-center text-orange-400 font-bold mb-3">
                <span className="text-2xl mr-2">🟠</span> ORANGE CAP
              </div>
              {topBatter ? (
                <>
                  <div className="text-2xl font-bold text-white">{topBatter.name}</div>
                  <div className="text-slate-400">{topBatter.team_name}</div>
                  <div className="text-orange-300 text-3xl font-bold mt-4">{topBatter.runs} <span className="text-sm font-normal">Runs</span></div>
                  <div className="text-sm text-slate-400 mt-2">Avg: {topBatter.average || 0} | SR: {topBatter.strike_rate}</div>
                </>
              ) : (
                <div className="text-slate-500 mt-4">No data yet</div>
              )}
            </div>

            <div className="bg-gradient-to-r from-purple-500/10 to-purple-600/5 border border-purple-500/30 rounded-xl p-6 text-center shadow-lg">
              <div className="flex items-center justify-center text-purple-400 font-bold mb-3">
                <span className="text-2xl mr-2">🟣</span> PURPLE CAP
              </div>
              {topBowler ? (
                <>
                  <div className="text-2xl font-bold text-white">{topBowler.name}</div>
                  <div className="text-slate-400">{topBowler.team_name}</div>
                  <div className="text-purple-300 text-3xl font-bold mt-4">{topBowler.wickets} <span className="text-sm font-normal">Wickets</span></div>
                  <div className="text-sm text-slate-400 mt-2">Econ: {topBowler.economy} | Best: {topBowler.best_bowling}</div>
                </>
              ) : (
                <div className="text-slate-500 mt-4">No data yet</div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'BATTING' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs text-slate-400 uppercase bg-slate-800 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 font-bold">Player</th>
                  <th className="px-4 py-3 font-bold">Team</th>
                  <th className="px-4 py-3 font-bold text-right">Mat</th>
                  <th className="px-4 py-3 font-bold text-right">Inn</th>
                  <th className="px-4 py-3 font-bold text-right text-orange-400">Runs</th>
                  <th className="px-4 py-3 font-bold text-right">HS</th>
                  <th className="px-4 py-3 font-bold text-right">Avg</th>
                  <th className="px-4 py-3 font-bold text-right">SR</th>
                  <th className="px-4 py-3 font-bold text-right">100/50</th>
                  <th className="px-4 py-3 font-bold text-right">4s</th>
                  <th className="px-4 py-3 font-bold text-right">6s</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {stats.batting.map((b: any, idx: number) => (
                  <tr key={b.player_id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-bold text-white">
                      {idx === 0 && <span className="mr-2 text-orange-500">🟠</span>}
                      {b.name}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{b.team_name}</td>
                    <td className="px-4 py-3 text-right">{b.matches}</td>
                    <td className="px-4 py-3 text-right">{b.innings}</td>
                    <td className="px-4 py-3 text-right font-bold text-orange-400">{b.runs}</td>
                    <td className="px-4 py-3 text-right">{b.highest_score}</td>
                    <td className="px-4 py-3 text-right">{b.average || '-'}</td>
                    <td className="px-4 py-3 text-right">{b.strike_rate}</td>
                    <td className="px-4 py-3 text-right">0/0</td> {/* Placeholder for milestones if we compute them later */}
                    <td className="px-4 py-3 text-right">{b.fours}</td>
                    <td className="px-4 py-3 text-right">{b.sixes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'BOWLING' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs text-slate-400 uppercase bg-slate-800 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 font-bold">Player</th>
                  <th className="px-4 py-3 font-bold">Team</th>
                  <th className="px-4 py-3 font-bold text-right">Mat</th>
                  <th className="px-4 py-3 font-bold text-right">Inn</th>
                  <th className="px-4 py-3 font-bold text-right">Overs</th>
                  <th className="px-4 py-3 font-bold text-right text-purple-400">Wickets</th>
                  <th className="px-4 py-3 font-bold text-right">Best</th>
                  <th className="px-4 py-3 font-bold text-right">Econ</th>
                  <th className="px-4 py-3 font-bold text-right">Maidens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {stats.bowling.map((b: any, idx: number) => (
                  <tr key={b.player_id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-bold text-white">
                      {idx === 0 && <span className="mr-2 text-purple-500">🟣</span>}
                      {b.name}
                    </td>
                    <td className="px-4 py-3 text-slate-400">{b.team_name}</td>
                    <td className="px-4 py-3 text-right">{b.matches}</td>
                    <td className="px-4 py-3 text-right">{b.innings}</td>
                    <td className="px-4 py-3 text-right">{b.overs}</td>
                    <td className="px-4 py-3 text-right font-bold text-purple-400">{b.wickets}</td>
                    <td className="px-4 py-3 text-right">{b.best_bowling}</td>
                    <td className="px-4 py-3 text-right">{b.economy}</td>
                    <td className="px-4 py-3 text-right">{b.maidens}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'FIELDING' && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="text-xs text-slate-400 uppercase bg-slate-800 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 font-bold">Player</th>
                  <th className="px-4 py-3 font-bold">Team</th>
                  <th className="px-4 py-3 font-bold text-right">Mat</th>
                  <th className="px-4 py-3 font-bold text-right text-emerald-400">Catches</th>
                  <th className="px-4 py-3 font-bold text-right text-emerald-400">Run Outs</th>
                  <th className="px-4 py-3 font-bold text-right text-emerald-400">Stumpings</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {stats.fielding.map((b: any) => (
                  <tr key={b.player_id} className="hover:bg-slate-800/50">
                    <td className="px-4 py-3 font-bold text-white">{b.name}</td>
                    <td className="px-4 py-3 text-slate-400">{b.team_name}</td>
                    <td className="px-4 py-3 text-right">{b.matches}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">{b.catches}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">{b.run_outs}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-400">{b.stumpings}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
