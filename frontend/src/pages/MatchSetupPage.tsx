import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API_URL } from '../services/api';
import { Coins, Users, PlayCircle, UserPlus, Check, X, AlertCircle } from 'lucide-react';

export const MatchSetupPage = () => {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const [match, setMatch] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Teams State (Full Data)
  const [team1Data, setTeam1Data] = useState<any>(null);
  const [team2Data, setTeam2Data] = useState<any>(null);
  
  // Squad Selection State
  const [team1XI, setTeam1XI] = useState<string[]>([]);
  const [team2XI, setTeam2XI] = useState<string[]>([]);
  
  const [team1Impact, setTeam1Impact] = useState<string | null>(null);
  const [team2Impact, setTeam2Impact] = useState<string | null>(null);

  const [activeSelectionTeam, setActiveSelectionTeam] = useState<'TEAM1' | 'TEAM2' | null>(null);
  
  useEffect(() => {
    fetchMatchAndSquads();
  }, [matchId]);

  const fetchMatchAndSquads = async () => {
    try {
      const response = await fetch(`${API_URL}/matches/${matchId}`);
      const matchData = await response.json();
      setMatch(matchData);
      
      const t1Res = await fetch(`${API_URL}/teams/${matchData.team1_id}`);
      const t1Data = await t1Res.json();
      setTeam1Data(t1Data);
      
      const t2Res = await fetch(`${API_URL}/teams/${matchData.team2_id}`);
      const t2Data = await t2Res.json();
      setTeam2Data(t2Data);
      
      if (matchData.team1_xi) setTeam1XI(matchData.team1_xi);
      if (matchData.team2_xi) setTeam2XI(matchData.team2_xi);
      if (matchData.team1_impact) setTeam1Impact(matchData.team1_impact);
      if (matchData.team2_impact) setTeam2Impact(matchData.team2_impact);
      
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const conductToss = async () => {
    try {
      await fetch(`${API_URL}/matches/${matchId}/toss`, { method: 'POST' });
      await fetchMatchAndSquads();
    } catch (err) {
      console.error(err);
    }
  };

  const saveXISelection = async () => {
    if (!activeSelectionTeam) return;
    
    const teamId = activeSelectionTeam === 'TEAM1' ? match.team1_id : match.team2_id;
    const xi = activeSelectionTeam === 'TEAM1' ? team1XI : team2XI;
    const impact = activeSelectionTeam === 'TEAM1' ? team1Impact : team2Impact;
    
    if (xi.length !== 11) {
      alert("Please select exactly 11 players for the Playing XI.");
      return;
    }
    
    try {
      await fetch(`${API_URL}/matches/${matchId}/playing-xi?team_id=${teamId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playing_xi: xi })
      });
      
      if (impact) {
        await fetch(`${API_URL}/matches/${matchId}/impact-player?team_id=${teamId}&player_id=${impact}`, {
          method: 'POST'
        });
      }
      
      await fetchMatchAndSquads();
      setActiveSelectionTeam(null);
    } catch (err) {
      console.error(err);
    }
  };

  const togglePlayer = (playerId: string) => {
    if (activeSelectionTeam === 'TEAM1') {
      if (team1XI.includes(playerId)) {
        setTeam1XI(team1XI.filter(id => id !== playerId));
        if (team1Impact === playerId) setTeam1Impact(null);
      } else {
        if (team1XI.length < 11) setTeam1XI([...team1XI, playerId]);
      }
    } else {
      if (team2XI.includes(playerId)) {
        setTeam2XI(team2XI.filter(id => id !== playerId));
        if (team2Impact === playerId) setTeam2Impact(null);
      } else {
        if (team2XI.length < 11) setTeam2XI([...team2XI, playerId]);
      }
    }
  };

  const toggleImpact = (playerId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeSelectionTeam === 'TEAM1') {
      if (team1XI.includes(playerId)) return;
      setTeam1Impact(team1Impact === playerId ? null : playerId);
    } else {
      if (team2XI.includes(playerId)) return;
      setTeam2Impact(team2Impact === playerId ? null : playerId);
    }
  };

  if (isLoading) return <div className="text-white py-10 text-center">Loading match setup...</div>;
  if (!match || !team1Data || !team2Data) return <div className="text-white py-10 text-center">Match or Team data not found</div>;

  const currentTeam = activeSelectionTeam === 'TEAM1' ? team1Data : team2Data;
  const currentSquad = currentTeam?.players || [];
  const currentXI = activeSelectionTeam === 'TEAM1' ? team1XI : team2XI;
  const currentImpact = activeSelectionTeam === 'TEAM1' ? team1Impact : team2Impact;

  // Validation Checks
  const team1UnratedSelected = team1Data.players.some((p: any) => p.ratingStatus !== 'READY' && team1XI.includes(p.id));
  const team2UnratedSelected = team2Data.players.some((p: any) => p.ratingStatus !== 'READY' && team2XI.includes(p.id));
  
  const currentTeamHasUnratedSelected = currentSquad.some((p: any) => p.ratingStatus !== 'READY' && currentXI.includes(p.id));

  const isReadyToStart = match.toss_winner && 
                         match.team1_xi?.length === 11 && 
                         match.team2_xi?.length === 11 &&
                         !team1UnratedSelected &&
                         !team2UnratedSelected;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-white mb-2">Match Setup</h2>
        <div className="flex justify-center items-center space-x-6 text-xl">
          <span className="font-bold text-blue-400">{team1Data.name}</span>
          <span className="text-slate-500 font-medium">VS</span>
          <span className="font-bold text-emerald-400">{team2Data.name}</span>
        </div>
      </div>

      {activeSelectionTeam && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-surface border border-slate-700 rounded-xl w-full max-w-3xl overflow-hidden shadow-2xl h-[80vh] flex flex-col">
            <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800">
              <h3 className="text-lg font-bold text-white uppercase">SELECT PLAYING XI & IMPACT SUB: {currentTeam.name}</h3>
              <button onClick={() => setActiveSelectionTeam(null)} className="text-slate-400 hover:text-white">
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              <div className="flex justify-between items-center px-4 py-3 mb-4 bg-slate-900 rounded-md sticky top-0 z-10 border border-slate-700 shadow-md">
                <span className="text-slate-300 font-medium">Selected XI: <span className={currentXI.length === 11 ? "text-green-400 font-bold" : "text-yellow-400 font-bold"}>{currentXI.length} / 11</span></span>
                <span className="text-slate-300 font-medium">Impact Sub: <span className={currentImpact ? "text-green-400 font-bold" : "text-yellow-400 font-bold"}>{currentImpact ? "1 / 1" : "0 / 1"}</span></span>
              </div>
              
              {currentSquad.map((player: any) => {
                const inXI = currentXI.includes(player.id);
                const isImpact = currentImpact === player.id;
                const isUnrated = player.ratingStatus !== 'READY';
                
                return (
                  <div 
                    key={player.id} 
                    onClick={() => togglePlayer(player.id)}
                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                      inXI ? (isUnrated ? 'bg-red-500/20 border-red-500' : 'bg-primary/20 border-primary') : 
                      isImpact ? 'bg-purple-500/20 border-purple-500' : 
                      'bg-slate-800 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <div>
                      <div className="font-bold text-white flex items-center">
                        {player.name}
                        {inXI && <Check className={`ml-2 h-4 w-4 ${isUnrated ? 'text-red-500' : 'text-primary'}`} />}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center mt-1">
                        {player.role || "Role TBD"}
                        {isUnrated && (
                          <span className="ml-2 flex items-center text-red-400 font-bold">
                            <AlertCircle className="h-3 w-3 mr-1" /> UNRATED
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <button 
                      onClick={(e) => toggleImpact(player.id, e)}
                      disabled={inXI}
                      className={`px-3 py-1 text-xs font-bold rounded-md border transition-colors ${
                        isImpact ? 'bg-purple-600 text-white border-purple-600' : 
                        inXI ? 'bg-slate-700 text-slate-500 border-slate-600 cursor-not-allowed' :
                        'bg-slate-800 text-slate-400 border-slate-600 hover:bg-slate-700'
                      }`}
                    >
                      {isImpact ? 'Impact Sub' : 'Set as Impact'}
                    </button>
                  </div>
                );
              })}
              
              {currentSquad.length === 0 && (
                <div className="text-center text-slate-500 py-10">No players found in squad. Please add players in Teams Page first.</div>
              )}
            </div>
            
            <div className="p-4 border-t border-slate-700 bg-slate-900 flex flex-col sm:flex-row justify-between items-center">
              {currentTeamHasUnratedSelected ? (
                <p className="text-red-400 text-sm font-medium mb-3 sm:mb-0">
                  <AlertCircle className="inline h-4 w-4 mr-1 mb-0.5" />
                  Cannot save: You have selected UNRATED players in your XI.
                </p>
              ) : (
                <p className="text-slate-400 text-sm mb-3 sm:mb-0">Select exactly 11 players for the Starting XI.</p>
              )}
              
              <button
                onClick={saveXISelection}
                disabled={currentXI.length !== 11 || currentTeamHasUnratedSelected}
                className="px-6 py-2 bg-primary hover:bg-blue-600 text-white font-bold rounded-md shadow disabled:opacity-50 w-full sm:w-auto"
              >
                Save Selection
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <div className="bg-surface border border-slate-700 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center"><Users className="mr-2" /> Playing XI Selection</h3>
          <div className="space-y-4">
            <button 
              onClick={() => setActiveSelectionTeam('TEAM1')}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-md text-white border transition-colors ${
                match.team1_xi?.length === 11 ? 'bg-green-500/20 border-green-500 hover:bg-green-500/30' : 'bg-slate-800 border-slate-600 hover:bg-slate-700'
              }`}
            >
              <span className="font-bold">{team1Data.name} XI</span>
              {match.team1_xi?.length === 11 ? <Check className="h-5 w-5 text-green-400" /> : <UserPlus className="h-5 w-5 text-slate-400" />}
            </button>
            
            <button 
              onClick={() => setActiveSelectionTeam('TEAM2')}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-md text-white border transition-colors ${
                match.team2_xi?.length === 11 ? 'bg-green-500/20 border-green-500 hover:bg-green-500/30' : 'bg-slate-800 border-slate-600 hover:bg-slate-700'
              }`}
            >
              <span className="font-bold">{team2Data.name} XI</span>
              {match.team2_xi?.length === 11 ? <Check className="h-5 w-5 text-green-400" /> : <UserPlus className="h-5 w-5 text-slate-400" />}
            </button>
          </div>
        </div>

        <div className="bg-surface border border-slate-700 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center"><Coins className="mr-2" /> Match Toss</h3>
          
          {match.toss_winner ? (
            <div className="text-center py-6 bg-slate-800/50 rounded-lg border border-slate-700">
              <Coins className="mx-auto h-12 w-12 text-yellow-500 mb-3" />
              <p className="text-lg text-white font-bold">{match.toss_winner === team1Data.id ? team1Data.name : team2Data.name} won the toss</p>
              <p className="text-slate-300">and chose to <span className="font-bold text-white">{match.toss_decision}</span> first.</p>
            </div>
          ) : (
            <div className="text-center py-8">
              <button 
                onClick={conductToss}
                className="px-6 py-3 bg-yellow-600 hover:bg-yellow-500 text-white font-bold rounded-full shadow-lg shadow-yellow-900/20 transition-transform active:scale-95"
              >
                Conduct Toss
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="text-center pt-8 border-t border-slate-700">
        <button
          disabled={!isReadyToStart}
          onClick={() => navigate(`/match/${matchId}`)}
          className="px-8 py-4 bg-primary hover:bg-blue-600 text-white font-bold text-lg rounded-xl shadow-xl shadow-blue-900/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto"
        >
          <PlayCircle className="mr-3 h-6 w-6" />
          Start Match Simulation
        </button>
        {!isReadyToStart && (
          <p className="text-red-400 text-sm mt-3 max-w-md mx-auto">
            {(!match.team1_xi || match.team1_xi.length !== 11 || !match.team2_xi || match.team2_xi.length !== 11) ? 
              "Complete Playing XI selection for both teams." : 
              !match.toss_winner ? "Conduct Toss to start." : 
              "Cannot start match with UNRATED players in the Playing XI."
            }
          </p>
        )}
      </div>
    </div>
  );
};
