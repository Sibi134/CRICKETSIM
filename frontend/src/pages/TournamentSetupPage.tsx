import React, { useState, useEffect } from 'react';
import { tournamentService, API_URL } from '../services/api';
import { Trophy, Calendar as CalendarIcon, PlayCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const TournamentSetupPage = () => {
  const [tournaments, setTournaments] = useState<any[]>([]);
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTournaments();
  }, []);

  const fetchTournaments = async () => {
    try {
      const data = await tournamentService.getAll();
      setTournaments(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;
    setIsLoading(true);
    try {
      await tournamentService.create({ name });
      await fetchTournaments();
      setName('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateSchedule = async (id: string) => {
    try {
      await fetch(`${API_URL}/tournaments/${id}/schedule/generate`, {
        method: 'POST'
      });
      await fetchTournaments();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteTournament = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this tournament? This will delete all associated matches and stats.")) {
      return;
    }
    try {
      await fetch(`${API_URL}/tournaments/${id}`, {
        method: 'DELETE'
      });
      await fetchTournaments();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Tournaments</h2>
          <p className="text-slate-400 text-sm mt-1">Manage your cricket tournaments</p>
        </div>
      </div>

      <form onSubmit={handleCreate} className="bg-surface border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-medium text-white mb-4">Create New Tournament</h3>
        <div className="flex gap-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Tournament Name (e.g. IPL 2026)"
            className="flex-1 bg-background border border-slate-700 rounded-md px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          <button
            type="submit"
            disabled={isLoading || !name}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
          >
            <Trophy className="mr-2 h-4 w-4" />
            Create
          </button>
        </div>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tournaments.map((t) => (
          <div key={t.id} className="bg-surface border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition-colors flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start">
                <h3 className="text-xl font-bold text-white">{t.name}</h3>
                <button onClick={() => handleDeleteTournament(t.id)} className="text-slate-500 hover:text-red-400 p-1" title="Delete Tournament">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                </button>
              </div>
              <div className="mt-4 flex justify-between text-sm">
                <span className="text-slate-400">Status</span>
                <span className={`font-medium ${t.status === 'SETUP' ? 'text-yellow-400' : 'text-green-400'}`}>
                  {t.status}
                </span>
              </div>
            </div>
            
            <div className="mt-6">
              {t.status === 'SETUP' ? (
                <button
                  onClick={() => handleGenerateSchedule(t.id)}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-slate-600 shadow-sm text-sm font-medium rounded-md text-white bg-slate-800 hover:bg-slate-700"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  Generate Schedule
                </button>
              ) : (
                <button
                  onClick={() => navigate('/schedule')}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-slate-900 bg-secondary hover:bg-emerald-400"
                >
                  <PlayCircle className="mr-2 h-4 w-4" />
                  View Schedule
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
