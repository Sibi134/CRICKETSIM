import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api';

const api = axios.create({
  baseURL: API_URL,
});

export const teamService = {
  importTeam: async (data: any) => {
    const response = await api.post('/teams/import', data);
    return response.data;
  },
  getTeams: async () => {
    const response = await api.get('/teams');
    return response.data;
  },
  deleteTeam: async (id: string) => {
    await api.delete(`/teams/${id}`);
  },
  pasteSquad: async (teamId: string, playerNames: string[], replace: boolean = false) => {
    const response = await api.post(`/teams/${teamId}/squad/paste`, { player_names: playerNames, replace });
    return response.data;
  },
  updatePlayer: async (teamId: string, playerId: string, playerData: any) => {
    const response = await api.put(`/teams/${teamId}/players/${playerId}`, playerData);
    return response.data;
  },
  addPlayer: async (teamId: string, playerData: any) => {
    const response = await api.post(`/teams/${teamId}/players`, playerData);
    return response.data;
  },
  deletePlayer: async (teamId: string, playerId: string) => {
    await api.delete(`/teams/${teamId}/players/${playerId}`);
  }
};

export const tournamentService = {
  create: async (data: any) => {
    const response = await api.post('/tournaments', data);
    return response.data;
  },
  getAll: async () => {
    const response = await api.get('/tournaments');
    return response.data;
  }
};

export default api;
