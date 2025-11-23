import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Shield, Users, UserPlus, LogOut, Mail, Check, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

interface Clan {
    id: number;
    nome: string;
    descricao: string;
    lider_id: number;
}

interface ClanMember {
    id: number;
    user_id: number;
    user_nome: string;
    papel: string;
    user_avatar?: string;
}

interface ClanInvite {
    id: number;
    clan_id: number;
    clan_nome: string;
    status: string;
}

export const ClanPage: React.FC = () => {
    const { user } = useAuth();
    const [clan, setClan] = useState<Clan | null>(null);
    const [members, setMembers] = useState<ClanMember[]>([]);
    const [invites, setInvites] = useState<ClanInvite[]>([]);
    const [loading, setLoading] = useState(true);

    // Forms
    const [newClanName, setNewClanName] = useState('');
    const [newClanDesc, setNewClanDesc] = useState('');

    const [suggestions, setSuggestions] = useState<Clan[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);

    useEffect(() => {
        fetchClanData();
    }, []);

    useEffect(() => {
        if (searchQuery.length > 2) {
            const delayDebounceFn = setTimeout(() => {
                searchUsers();
            }, 500);
            return () => clearTimeout(delayDebounceFn);
        } else {
            setSearchResults([]);
        }
    }, [searchQuery]);

    const fetchClanData = async () => {
        try {
            setLoading(true);
            // Check if user has a clan
            const clanRes = await apiClient.get('/clans/me');

            if (clanRes.data) {
                setClan(clanRes.data);
                // Fetch members
                const membersRes = await apiClient.get(`/clans/${clanRes.data.id}/members`);
                setMembers(membersRes.data);
            } else {
                setClan(null);
                // Fetch invites
                const invitesRes = await apiClient.get('/clans/invites/my');
                setInvites(invitesRes.data);
                // Fetch suggestions
                const suggestionsRes = await apiClient.get('/clans/suggestions');
                setSuggestions(suggestionsRes.data);
            }
        } catch (error) {
            console.error("Error fetching clan data", error);
        } finally {
            setLoading(false);
        }
    };

    const searchUsers = async () => {
        try {
            const res = await apiClient.get('/users/search', { params: { q: searchQuery } });
            setSearchResults(res.data);
        } catch (error) {
            console.error("Error searching users", error);
        }
    };

    const handleCreateClan = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user?.escola_id) {
            alert('Você precisa estar vinculado a uma escola para criar um clã.');
            return;
        }
        try {
            await apiClient.post('/clans/', { nome: newClanName, descricao: newClanDesc });
            alert('Clã criado com sucesso!');
            fetchClanData();
        } catch (error: any) {
            console.error("Error creating clan", error);
            alert(error.response?.data?.detail || 'Erro ao criar clã. Verifique se o nome já existe.');
        }
    };

    const handleInvite = async (email: string) => {
        try {
            await apiClient.post('/clans/invite', null, { params: { email } });
            alert(`Convite enviado para ${email}!`);
            setSearchQuery('');
            setSearchResults([]);
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao enviar convite');
        }
    };

    const handleAcceptInvite = async (inviteId: number) => {
        try {
            await apiClient.post(`/clans/invites/${inviteId}/accept`);
            alert('Você entrou no clã!');
            fetchClanData();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao aceitar convite');
        }
    };

    const handleLeaveClan = async () => {
        if (!confirm('Tem certeza que deseja sair do clã?')) return;
        try {
            await apiClient.post('/clans/leave');
            alert('Você saiu do clã.');
            fetchClanData();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao sair do clã');
        }
    };

    const handleDeleteClan = async () => {
        if (!clan) return;
        if (!confirm(`Tem certeza que deseja excluir o clã "${clan.nome}"? Esta ação não pode ser desfeita.`)) return;

        try {
            await apiClient.delete(`/clans/${clan.id}`);
            alert('Clã excluído com sucesso.');
            setClan(null);
            fetchClanData();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao excluir clã');
        }
    };

    if (loading) return <div className="p-8 text-white">Carregando...</div>;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <div className="max-w-4xl mx-auto">
                <header className="mb-8 flex items-center gap-3">
                    <Shield className="w-10 h-10 text-primary" />
                    <h1 className="text-3xl font-bold">Sistema de Clãs</h1>
                </header>

                {!clan ? (
                    <div className="space-y-8">
                        <div className="grid md:grid-cols-2 gap-8">
                            {/* Create Clan */}
                            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                    <UserPlus className="w-6 h-6 text-green-400" />
                                    Criar Novo Clã
                                </h2>
                                <form onSubmit={handleCreateClan} className="space-y-4">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">Nome do Clã</label>
                                        <input
                                            type="text"
                                            value={newClanName}
                                            onChange={e => setNewClanName(e.target.value)}
                                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">Lema / Descrição</label>
                                        <input
                                            type="text"
                                            value={newClanDesc}
                                            onChange={e => setNewClanDesc(e.target.value)}
                                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                            required
                                        />
                                    </div>
                                    <button type="submit" className="w-full bg-green-600 hover:bg-green-700 py-2 rounded-lg font-bold">
                                        Fundar Clã
                                    </button>
                                </form>
                            </div>

                            {/* Invites */}
                            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                    <Mail className="w-6 h-6 text-blue-400" />
                                    Convites Recebidos
                                </h2>
                                {invites.length === 0 ? (
                                    <p className="text-gray-400">Nenhum convite pendente.</p>
                                ) : (
                                    <div className="space-y-3">
                                        {invites.map(invite => (
                                            <div key={invite.id} className="bg-gray-700 p-3 rounded-lg flex justify-between items-center">
                                                <div>
                                                    <p className="font-bold">{invite.clan_nome}</p>
                                                    <p className="text-xs text-gray-400">Convite para se juntar</p>
                                                </div>
                                                <button
                                                    onClick={() => handleAcceptInvite(invite.id)}
                                                    className="bg-blue-600 hover:bg-blue-500 p-2 rounded-full"
                                                >
                                                    <Check className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Suggestions */}
                        {suggestions.length > 0 && (
                            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                    <Users className="w-6 h-6 text-purple-400" />
                                    Sugestões de Clãs
                                </h2>
                                <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
                                    {suggestions.map(s => (
                                        <div key={s.id} className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                                            <h3 className="font-bold text-lg">{s.nome}</h3>
                                            <p className="text-sm text-gray-400 italic mb-2">"{s.descricao}"</p>
                                            <p className="text-xs text-gray-500">Peça um convite ao líder!</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="space-y-6">
                        {/* Clan Header */}
                        <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 text-center relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-primary to-secondary"></div>
                            <h2 className="text-4xl font-bold mb-2">{clan.nome}</h2>
                            <p className="text-gray-400 italic">"{clan.descricao}"</p>

                            <div className="mt-6 flex justify-center gap-4">
                                <button
                                    onClick={handleLeaveClan}
                                    className="flex items-center gap-2 px-4 py-2 bg-red-900/50 text-red-200 rounded-lg hover:bg-red-900 transition-colors"
                                >
                                    <LogOut className="w-4 h-4" /> Sair do Clã
                                </button>
                                {(user?.papel === 'admin' || user?.papel === 'gestor') && (
                                    <button
                                        onClick={handleDeleteClan}
                                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" /> Excluir Clã
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="grid md:grid-cols-3 gap-6">
                            {/* Members List */}
                            <div className="md:col-span-2 bg-gray-800 p-6 rounded-xl border border-gray-700">
                                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                    <Users className="w-5 h-5 text-purple-400" />
                                    Membros ({members.length})
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {members.map(member => (
                                        <div key={member.id} className="bg-gray-700/50 p-3 rounded-lg flex items-center gap-3">
                                            <div className="w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center">
                                                {member.user_avatar ? (
                                                    <img src={member.user_avatar} alt="" className="w-full h-full rounded-full object-cover" />
                                                ) : (
                                                    <span className="font-bold text-gray-400">{member.user_nome[0]}</span>
                                                )}
                                            </div>
                                            <div>
                                                <Link to={`/profile/${member.user_id}`} className="font-bold hover:text-blue-400 hover:underline">
                                                    {member.user_nome}
                                                </Link>
                                                <span className={`block w-fit text-xs px-2 py-0.5 rounded-full mt-1 ${member.papel === 'lider' ? 'bg-yellow-900 text-yellow-200' : 'bg-gray-600 text-gray-300'
                                                    }`}>
                                                    {member.papel.toUpperCase()}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Invite Action (Leader Only) */}
                            {clan.lider_id === user?.id && (
                                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 h-fit">
                                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                        <UserPlus className="w-5 h-5 text-blue-400" />
                                        Convidar Membro
                                    </h3>
                                    <div className="space-y-3">
                                        <input
                                            type="text"
                                            placeholder="Buscar aluno (nome ou email)..."
                                            value={searchQuery}
                                            onChange={e => setSearchQuery(e.target.value)}
                                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                        />
                                        {searchResults.length > 0 && (
                                            <div className="bg-gray-700 rounded-lg max-h-48 overflow-y-auto border border-gray-600">
                                                {searchResults.map(u => (
                                                    <div key={u.id} className="p-2 hover:bg-gray-600 flex justify-between items-center border-b border-gray-600 last:border-0">
                                                        <div>
                                                            <p className="font-bold text-sm">{u.nome}</p>
                                                            <p className="text-xs text-gray-400">{u.email}</p>
                                                        </div>
                                                        <button
                                                            onClick={() => handleInvite(u.email)}
                                                            className="text-xs bg-blue-600 px-2 py-1 rounded hover:bg-blue-500"
                                                        >
                                                            Convidar
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        {searchQuery.length > 2 && searchResults.length === 0 && (
                                            <p className="text-sm text-gray-500 text-center">Nenhum aluno encontrado.</p>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
