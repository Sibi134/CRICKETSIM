import { useState, useEffect } from 'react';
import { API_URL } from '../services/api';

export const Scorecard = ({ matchId, refreshTrigger }: { matchId: string, refreshTrigger: number }) => {
  const [scorecard, setScorecard] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'SUMMARY' | 'INN1' | 'INN2'>('SUMMARY');

  useEffect(() => {
    fetchScorecard();
  }, [matchId, refreshTrigger]);

  const fetchScorecard = async () => {
    try {
      const response = await fetch(`${API_URL}/matches/${matchId}/scorecard`);
      if (response.ok) {
        const data = await response.json();
        setScorecard(data);
      }
    } catch (err) {
      console.error("Failed to fetch scorecard", err);
    }
  };

  if (!scorecard) return null;

  const renderInnings = (innings: any) => {
    if (!innings) return <div className="text-slate-400 p-8 text-center border border-slate-700 rounded-lg border-dashed">Innings not started yet.</div>;
    
    return (
      <div className="space-y-6">
        {/* Innings Summary */}
        <div className="bg-slate-800/50 p-4 rounded-lg flex flex-wrap justify-between items-center text-sm">
          <div><span className="text-slate-400">Team:</span> <span className="font-bold text-white">{innings.team_name}</span></div>
          <div><span className="text-slate-400">Total:</span> <span className="font-bold text-white text-lg">{innings.total_runs}/{innings.total_wickets}</span> <span className="text-xs">({innings.total_overs} Ov)</span></div>
          <div><span className="text-slate-400">RR:</span> <span className="font-bold text-white">{innings.run_rate}</span></div>
          <div><span className="text-slate-400">Extras:</span> <span className="font-bold text-white">{innings.extras.total}</span> <span className="text-xs">(W {innings.extras.wides}, NB {innings.extras.noballs}, B {innings.extras.byes}, LB {innings.extras.legbyes})</span></div>
        </div>

        {/* Batting Table */}
        <div className="overflow-x-auto rounded-lg border border-slate-700">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="px-4 py-3 font-medium">Batter</th>
                <th className="px-4 py-3 font-medium">Dismissal</th>
                <th className="px-4 py-3 font-medium text-right">R</th>
                <th className="px-4 py-3 font-medium text-right">B</th>
                <th className="px-4 py-3 font-medium text-right">4s</th>
                <th className="px-4 py-3 font-medium text-right">6s</th>
                <th className="px-4 py-3 font-medium text-right">SR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {innings.batting.map((b: any, idx: number) => (
                <tr key={idx} className={b.is_out ? '' : 'bg-primary/5'}>
                  <td className={`px-4 py-3 ${!b.is_out ? 'font-bold text-primary' : ''}`}>{b.name}{!b.is_out && ' *'}</td>
                  <td className="px-4 py-3 text-xs text-slate-400">{b.dismissal}</td>
                  <td className="px-4 py-3 text-right font-bold text-white">{b.runs}</td>
                  <td className="px-4 py-3 text-right">{b.balls}</td>
                  <td className="px-4 py-3 text-right">{b.fours}</td>
                  <td className="px-4 py-3 text-right">{b.sixes}</td>
                  <td className="px-4 py-3 text-right">{b.strike_rate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Bowling Table */}
        <div className="overflow-x-auto rounded-lg border border-slate-700">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-800 text-slate-300">
              <tr>
                <th className="px-4 py-3 font-medium">Bowler</th>
                <th className="px-4 py-3 font-medium text-right">O</th>
                <th className="px-4 py-3 font-medium text-right">M</th>
                <th className="px-4 py-3 font-medium text-right">R</th>
                <th className="px-4 py-3 font-medium text-right">W</th>
                <th className="px-4 py-3 font-medium text-right">Econ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {innings.bowling.map((b: any, idx: number) => (
                <tr key={idx}>
                  <td className="px-4 py-3">{b.name}</td>
                  <td className="px-4 py-3 text-right">{b.overs}</td>
                  <td className="px-4 py-3 text-right">{b.maidens}</td>
                  <td className="px-4 py-3 text-right">{b.runs}</td>
                  <td className="px-4 py-3 text-right font-bold text-white">{b.wickets}</td>
                  <td className="px-4 py-3 text-right">{b.economy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-surface border border-slate-700 rounded-xl overflow-hidden mt-6">
      {/* Tabs */}
      <div className="flex border-b border-slate-700 bg-slate-900/50 overflow-x-auto">
        <button 
          onClick={() => setActiveTab('SUMMARY')} 
          className={`px-6 py-4 text-sm font-bold whitespace-nowrap border-b-2 ${activeTab === 'SUMMARY' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800'}`}
        >
          Match Summary
        </button>
        <button 
          onClick={() => setActiveTab('INN1')} 
          className={`px-6 py-4 text-sm font-bold whitespace-nowrap border-b-2 ${activeTab === 'INN1' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800'}`}
        >
          {scorecard.innings1 ? scorecard.innings1.team_name + ' Innings' : 'Innings 1'}
        </button>
        <button 
          onClick={() => setActiveTab('INN2')} 
          className={`px-6 py-4 text-sm font-bold whitespace-nowrap border-b-2 ${activeTab === 'INN2' ? 'border-primary text-primary bg-primary/5' : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800'}`}
        >
          {scorecard.innings2 ? scorecard.innings2.team_name + ' Innings' : 'Innings 2'}
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'SUMMARY' && (
          <div className="text-center py-10 space-y-6">
            <h3 className="text-2xl font-bold text-white">{scorecard.result_string || "Match in Progress"}</h3>
            
            {scorecard.player_of_match_name && (
              <div className="mt-8 bg-gradient-to-r from-amber-500/10 to-amber-600/5 border border-amber-500/30 rounded-xl p-6 max-w-lg mx-auto inline-block text-center shadow-lg">
                <div className="flex items-center justify-center text-amber-400 font-bold mb-3">
                  <span className="text-2xl mr-2">🏆</span> PLAYER OF THE MATCH
                </div>
                <div className="text-xl font-bold text-white mb-1">{scorecard.player_of_match_name}</div>
                <div className="text-amber-200/80 font-mono text-sm">{scorecard.player_of_match_summary}</div>
              </div>
            )}
            
            <div className="pt-6">
              {scorecard.innings1 && (
                <div className="text-slate-300">
                  <span className="font-bold">{scorecard.innings1.team_name}</span>: {scorecard.innings1.total_runs}/{scorecard.innings1.total_wickets} ({scorecard.innings1.total_overs} Ov)
                </div>
              )}
              {scorecard.innings2 && (
                <div className="text-slate-300">
                  <span className="font-bold">{scorecard.innings2.team_name}</span>: {scorecard.innings2.total_runs}/{scorecard.innings2.total_wickets} ({scorecard.innings2.total_overs} Ov)
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'INN1' && renderInnings(scorecard.innings1)}
        {activeTab === 'INN2' && renderInnings(scorecard.innings2)}
      </div>
    </div>
  );
};
