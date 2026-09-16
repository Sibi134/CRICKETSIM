import { useState, useEffect } from 'react';
import { Shield, Plus, X, Edit, Check, AlertCircle } from 'lucide-react';
import { teamService } from '../services/api';

export const TeamsPage = () => {
  const [teams, setTeams] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading] = useState(false);
  
  // Modals state
  const [pasteModalTeam, setPasteModalTeam] = useState<any | null>(null);
  const [viewSquadTeam, setViewSquadTeam] = useState<any | null>(null);
  const [editPlayer, setEditPlayer] = useState<any | null>(null);
  
  const [pastedNames, setPastedNames] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      const data = await teamService.getTeams();
      setTeams(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handlePasteSubmit = async () => {
    if (!pasteModalTeam || !pastedNames.trim()) return;
    
    const isReplace = pasteModalTeam.players && pasteModalTeam.players.length > 0;
    if (isReplace) {
      if (!window.confirm(`Are you sure you want to replace the entire ${pasteModalTeam.name} squad? All existing players will be deleted.`)) {
        return;
      }
    }
    
    setIsSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const namesArray = pastedNames.split('\n').filter(n => n.trim() !== '');
      await teamService.pasteSquad(pasteModalTeam.id, namesArray, isReplace);
      await fetchTeams(); 
      setSuccess(`${pasteModalTeam.name} squad ${isReplace ? 'replaced' : 'saved'} successfully — ${namesArray.length} players.`);
      setPasteModalTeam(null);
      setPastedNames('');
    } catch (err: any) {
      setError(err.message || 'Unable to save squad.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdatePlayer = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = {
        ...editPlayer,
        ratings: editPlayer.ratings ? {
          batting: Number(editPlayer.ratings.batting),
          power: Number(editPlayer.ratings.power),
          consistency: Number(editPlayer.ratings.consistency),
          running: Number(editPlayer.ratings.running),
          fielding: Number(editPlayer.ratings.fielding),
          bowling: Number(editPlayer.ratings.bowling),
          pace: Number(editPlayer.ratings.pace),
          spin: Number(editPlayer.ratings.spin),
          deathBowling: Number(editPlayer.ratings.deathBowling)
        } : null
      };
      
      if (editPlayer.id) {
        await teamService.updatePlayer(viewSquadTeam.id, editPlayer.id, payload);
      } else {
        await teamService.addPlayer(viewSquadTeam.id, payload);
      }
      
      // Fetch teams once and update all states
      const data = await teamService.getTeams();
      setTeams(data);
      
      const refetchedTeam = data.find((t: any) => t.id === viewSquadTeam.id);
      setViewSquadTeam(refetchedTeam);
      
      setEditPlayer(null);
    } catch (err: any) {
      alert("Error saving player: " + (err.message || 'Unable to update player.'));
      setError(err.message || 'Unable to update player.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeletePlayer = async (teamId: string, playerId: string) => {
    if (!window.confirm("Are you sure you want to delete this player?")) return;
    try {
      await teamService.deletePlayer(teamId, playerId);
      const data = await teamService.getTeams();
      setTeams(data);
      const refetchedTeam = data.find((t: any) => t.id === teamId);
      setViewSquadTeam(refetchedTeam);
    } catch (err: any) {
      alert("Error deleting player: " + (err.message || 'Unable to delete player.'));
    }
  };

  const openPlayerEditor = (player: any) => {
    // Populate default ratings if they are null
    const playerToEdit = { ...player };
    if (!playerToEdit.ratings) {
      playerToEdit.ratings = {
        batting: 50, power: 50, consistency: 50, running: 50, fielding: 50,
        bowling: 50, pace: 50, spin: 50, deathBowling: 50
      };
    }
    setEditPlayer(playerToEdit);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">IPL Teams</h2>
          <p className="text-slate-400 text-sm mt-1">Manage 10 IPL franchises and setup squads</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-start">
          <X className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0 cursor-pointer" onClick={() => setError(null)} />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}
      
      {success && (
        <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4 flex items-start">
          <Check className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0 cursor-pointer" onClick={() => setSuccess(null)} />
          <p className="text-sm text-green-500">{success}</p>
        </div>
      )}

      {/* PASTE SQUAD MODAL */}
      {pasteModalTeam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-slate-700 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800">
              <h3 className="text-lg font-bold text-white">Add Squad to {pasteModalTeam.name}</h3>
              <button onClick={() => setPasteModalTeam(null)} className="text-slate-400 hover:text-white" disabled={isSubmitting}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-sm text-slate-400 mb-4">
                Paste a list of player names (one per line). Names with (C) or (WK) will be detected automatically. Players will be automatically rated based on their role and marked as READY.
              </p>
              <textarea
                className="w-full h-48 bg-slate-900 border border-slate-700 rounded-lg p-3 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                placeholder="1. MS Dhoni (C) (WK)&#10;2. Ruturaj Gaikwad&#10;3. Ravindra Jadeja"
                value={pastedNames}
                onChange={(e) => setPastedNames(e.target.value)}
                disabled={isSubmitting}
              />
              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setPasteModalTeam(null)}
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  onClick={handlePasteSubmit}
                  disabled={isSubmitting || !pastedNames.trim()}
                  className="px-4 py-2 bg-primary hover:bg-blue-600 text-white text-sm font-medium rounded-md shadow disabled:opacity-50 flex items-center"
                >
                  {isSubmitting ? 'Saving...' : 'Save Squad'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW SQUAD MODAL */}
      {viewSquadTeam && !editPlayer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-slate-700 rounded-xl w-full max-w-3xl overflow-hidden shadow-2xl h-[80vh] flex flex-col">
            <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800">
              <h3 className="text-lg font-bold text-white uppercase">{viewSquadTeam.name} - Squad ({viewSquadTeam.players.length} Players)</h3>
              <div className="flex gap-4">
                <button 
                  onClick={() => openPlayerEditor({ name: '', role: 'Batter', ratings: { batting: 50, power: 50, consistency: 50, running: 50, fielding: 50, bowling: 50, pace: 50, spin: 50, deathBowling: 50 } })} 
                  className="px-3 py-1 bg-primary hover:bg-blue-600 text-white rounded text-sm font-medium flex items-center"
                >
                  <Plus className="h-4 w-4 mr-1" /> Add Player
                </button>
                <button onClick={() => setViewSquadTeam(null)} className="text-slate-400 hover:text-white">
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {viewSquadTeam.players.map((player: any, idx: number) => {
                const tags = [];
                if (player.isCaptain) tags.push("C");
                if (player.isViceCaptain) tags.push("VC");
                if (player.role === "Wicketkeeper Batter") tags.push("WK");
                
                return (
                  <div key={player.id} className="flex items-center justify-between p-3 rounded-lg border bg-slate-800 border-slate-700 hover:bg-slate-700 transition-colors">
                    <div className="flex items-center">
                      <span className="text-slate-500 w-6 font-mono text-sm">{idx + 1}.</span>
                      <div>
                        <div className="font-bold text-white flex items-center">
                          {player.name}
                          {tags.length > 0 && <span className="ml-2 text-xs font-semibold text-primary">— {tags.join(", ")}</span>}
                        </div>
                        <div className="text-xs text-slate-400">
                          {player.role || "Unknown Role"} • {player.ratingStatus === 'READY' ? <span className="text-green-400">READY</span> : <span className="text-red-400 font-bold">UNRATED</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => openPlayerEditor(player)}
                        className="p-2 text-slate-400 hover:text-white bg-slate-900 rounded-md border border-slate-700 hover:border-slate-500"
                        title="Edit Player"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button 
                        onClick={() => handleDeletePlayer(viewSquadTeam.id, player.id)}
                        className="p-2 text-red-400 hover:text-red-300 bg-slate-900 rounded-md border border-slate-700 hover:border-slate-500"
                        title="Delete Player"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* EDIT PLAYER MODAL */}
      {editPlayer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm p-4">
          <div className="bg-surface border border-slate-700 rounded-xl w-full max-w-2xl overflow-hidden shadow-2xl h-[90vh] flex flex-col">
            <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800">
              <h3 className="text-lg font-bold text-white">Edit Player: {editPlayer.name}</h3>
              <button onClick={() => setEditPlayer(null)} className="text-slate-400 hover:text-white" disabled={isSubmitting}>
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <form onSubmit={handleUpdatePlayer} className="flex-1 overflow-y-auto p-6 space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Name</label>
                  <input required type="text" className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-white" value={editPlayer.name} onChange={e => setEditPlayer({...editPlayer, name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Role</label>
                  <select className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-white" value={editPlayer.role || ''} onChange={e => setEditPlayer({...editPlayer, role: e.target.value})}>
                    <option value="">Select Role...</option>
                    <option value="Batter">Batter</option>
                    <option value="Wicketkeeper Batter">Wicketkeeper Batter</option>
                    <option value="All-rounder">All-rounder</option>
                    <option value="Spin Bowler">Spin Bowler</option>
                    <option value="Fast Bowler">Fast Bowler</option>
                  </select>
                </div>
                
                <div className="col-span-2 flex items-center space-x-6 mt-2">
                  <label className="flex items-center space-x-2 text-sm text-white">
                    <input type="checkbox" checked={editPlayer.isCaptain || false} onChange={e => setEditPlayer({...editPlayer, isCaptain: e.target.checked})} className="rounded bg-slate-900 border-slate-700 text-primary" />
                    <span>Captain</span>
                  </label>
                  <label className="flex items-center space-x-2 text-sm text-white">
                    <input type="checkbox" checked={editPlayer.isViceCaptain || false} onChange={e => setEditPlayer({...editPlayer, isViceCaptain: e.target.checked})} className="rounded bg-slate-900 border-slate-700 text-primary" />
                    <span>Vice Captain</span>
                  </label>
                  <label className="flex items-center space-x-2 text-sm text-white">
                    <input type="checkbox" checked={editPlayer.isOverseas || false} onChange={e => setEditPlayer({...editPlayer, isOverseas: e.target.checked})} className="rounded bg-slate-900 border-slate-700 text-primary" />
                    <span>Overseas Player</span>
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-700">
                <h4 className="text-sm font-bold text-white uppercase mb-4">Player Ratings (0-100)</h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {Object.keys(editPlayer.ratings).map((stat) => (
                    <div key={stat}>
                      <label className="block text-xs font-medium text-slate-400 mb-1 capitalize">{stat}</label>
                      <input 
                        type="number" min="0" max="100" required
                        className="w-full bg-slate-900 border border-slate-700 rounded-md p-2 text-white text-sm" 
                        value={editPlayer.ratings[stat]} 
                        onChange={e => setEditPlayer({
                          ...editPlayer, 
                          ratings: { ...editPlayer.ratings, [stat]: e.target.value }
                        })} 
                      />
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="pt-6">
                <button type="submit" disabled={isSubmitting} className="w-full py-3 bg-primary hover:bg-blue-600 text-white font-bold rounded-lg disabled:opacity-50">
                  {isSubmitting ? 'Saving...' : 'Save Player & Mark READY'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TEAM CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {teams.map((team) => {
          const squadSize = team.players?.length || 0;
          const captain = team.players?.find((p: any) => p.isCaptain);
          const unratedCount = team.players?.filter((p: any) => p.ratingStatus !== 'READY').length || 0;
          const status = squadSize === 0 ? "NO SQUAD" : (unratedCount > 0 ? "INCOMPLETE" : "READY");
          
          return (
            <div key={team.id} className="bg-surface border border-slate-700 rounded-xl overflow-hidden hover:border-slate-600 transition-colors flex flex-col h-full">
              <div 
                className="h-20 w-full" 
                style={{ background: `linear-gradient(135deg, ${team.primary_color} 0%, ${team.secondary_color} 100%)` }}
              />
              <div className="p-5 flex-1 flex flex-col">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white">{team.name}</h3>
                  <div className="flex justify-between items-center mt-2">
                    <p className="text-sm font-medium text-slate-300">{squadSize} Players</p>
                    <span className={`text-xs font-bold px-2 py-1 rounded-md ${
                      status === 'READY' ? 'bg-green-500/20 text-green-400' : 
                      status === 'INCOMPLETE' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-700 text-slate-400'
                    }`}>
                      {status}
                    </span>
                  </div>
                  
                  {squadSize > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-700 space-y-1 text-sm">
                      {captain && <p className="text-slate-400">Captain: <span className="text-white font-medium">{captain.name}</span></p>}
                      {status === 'INCOMPLETE' && (
                        <div className="flex items-center text-yellow-400 text-xs mt-2">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          {unratedCount} players need ratings
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="mt-5 space-y-2">
                  {squadSize === 0 ? (
                    <button
                      onClick={() => setPasteModalTeam(team)}
                      className="w-full flex items-center justify-center px-4 py-2 border border-slate-600 rounded-md shadow-sm text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 focus:outline-none"
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Add Squad (Paste Names)
                    </button>
                  ) : (
                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => setViewSquadTeam(team)}
                        className="w-full flex items-center justify-center px-4 py-2 border border-slate-600 rounded-md shadow-sm text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 focus:outline-none"
                      >
                        View / Edit Squad
                      </button>
                      <button
                        onClick={() => setPasteModalTeam(team)}
                        className="w-full flex items-center justify-center px-4 py-2 border border-slate-700 rounded-md text-sm font-medium text-slate-400 bg-transparent hover:text-white hover:bg-slate-800 focus:outline-none"
                      >
                        Replace Squad (Paste)
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        
        {teams.length === 0 && !isLoading && (
          <div className="col-span-full py-12 text-center border-2 border-dashed border-slate-700 rounded-xl">
            <Shield className="mx-auto h-12 w-12 text-slate-500" />
            <h3 className="mt-2 text-sm font-medium text-white">No teams found</h3>
            <p className="mt-1 text-sm text-slate-400">Please seed the IPL teams from the backend.</p>
          </div>
        )}
      </div>
    </div>
  );
};
