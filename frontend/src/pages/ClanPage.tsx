import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Shield, Users, UserPlus, LogOut, Mail, Check, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ClanChat } from '../components/ClanChat';

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
    const [clanMissions, setClanMissions] = useState<any[]>([]);
    const [invites, setInvites] = useState<ClanInvite[]>([]);
    const [loading, setLoading] = useState(true);

    // Forms
    const [newClanName, setNewClanName] = useState('');
    const [newClanDesc, setNewClanDesc] = useState('');

    const [suggestions, setSuggestions] = useState<Clan[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);

    const [missionProgress, setMissionProgress] = useState<any[]>([]);

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
            const clanRes = await apiClient.get('/clans/me');

            if (clanRes.data) {
                setClan(clanRes.data);
                const membersRes = await apiClient.get(`/clans/${clanRes.data.id}/members`);
                setMembers(membersRes.data);

                const missionsRes = await apiClient.get(`/clans/${clanRes.data.id}/missoes`);
                setClanMissions(missionsRes.data);

                // If leader, fetch progress
                if (clanRes.data.lider_id === user?.id) {
                    const progressRes = await apiClient.get(`/clans/${clanRes.data.id}/missoes/progress`);
                    setMissionProgress(progressRes.data);
                }
            } else {
                setClan(null);
                const invitesRes = await apiClient.get('/clans/invites/my');
                setInvites(invitesRes.data);
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
        <div className="min-h-screen bg-[#121214] text-gray-100 p-6 font-sans">
            <div className="max-w-5xl mx-auto">
                {!clan ? (
                    <div className="space-y-12">
                        <header className="text-center mb-12">
                            <h1 className="text-4xl font-light tracking-tight text-white mb-2">Sistema de Clãs</h1>
                            <p className="text-gray-400">Junte-se a um clã ou crie o seu próprio legado.</p>
                        </header>

                        <div className="grid md:grid-cols-2 gap-12">
                            {/* Create Clan */}
                            <div className="bg-[#202024] p-8 rounded-2xl border border-gray-800 shadow-lg">
                                <h2 className="text-2xl font-light mb-6 flex items-center gap-3 text-white">
                                    <UserPlus className="w-6 h-6 text-emerald-500" />
                                    Criar Novo Clã
                                </h2>
                                <form onSubmit={handleCreateClan} className="space-y-5">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-2">Nome do Clã</label>
                                        <input
                                            type="text"
                                            value={newClanName}
                                            onChange={e => setNewClanName(e.target.value)}
                                            className="w-full bg-[#121214] border border-gray-700 rounded-lg p-3 text-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all outline-none"
                                            placeholder="Ex: Os Guardiões"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-2">Lema / Descrição</label>
                                        <input
                                            type="text"
                                            value={newClanDesc}
                                            onChange={e => setNewClanDesc(e.target.value)}
                                            className="w-full bg-[#121214] border border-gray-700 rounded-lg p-3 text-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all outline-none"
                                            placeholder="Ex: Sabedoria e Coragem"
                                            required
                                        />
                                    </div>
                                    <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-3 rounded-lg font-medium transition-colors shadow-lg shadow-emerald-900/20">
                                        Fundar Clã
                                    </button>
                                </form>
                            </div>

                            {/* Invites */}
                            <div className="bg-[#202024] p-8 rounded-2xl border border-gray-800 shadow-lg">
                                <h2 className="text-2xl font-light mb-6 flex items-center gap-3 text-white">
                                    <Mail className="w-6 h-6 text-blue-500" />
                                    Convites
                                </h2>
                                {invites.length === 0 ? (
                                    <div className="text-center py-12 text-gray-500 bg-[#121214] rounded-xl border border-gray-800 border-dashed">
                                        Nenhum convite pendente
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {invites.map(invite => (
                                            <div key={invite.id} className="bg-[#121214] p-4 rounded-xl border border-gray-800 flex justify-between items-center group hover:border-gray-700 transition-colors">
                                                <div>
                                                    <p className="font-medium text-white group-hover:text-blue-400 transition-colors">{invite.clan_nome}</p>
                                                    <p className="text-xs text-gray-500">Convite para se juntar</p>
                                                </div>
                                                <button
                                                    onClick={() => handleAcceptInvite(invite.id)}
                                                    className="bg-blue-600/10 hover:bg-blue-600 text-blue-500 hover:text-white p-2 rounded-full transition-all"
                                                >
                                                    <Check className="w-5 h-5" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Suggestions */}
                        {suggestions.length > 0 && (
                            <div className="mt-12">
                                <h2 className="text-2xl font-light mb-6 flex items-center gap-3 text-white">
                                    <Users className="w-6 h-6 text-purple-500" />
                                    Sugestões de Clãs
                                </h2>
                                <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
                                    {suggestions.map(s => (
                                        <div key={s.id} className="bg-[#202024] p-6 rounded-xl border border-gray-800 hover:border-purple-500/30 transition-all group">
                                            <h3 className="font-medium text-lg text-white group-hover:text-purple-400 transition-colors">{s.nome}</h3>
                                            <p className="text-sm text-gray-400 italic mb-4">"{s.descricao}"</p>
                                            <p className="text-xs text-gray-500">Peça um convite ao líder!</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Clan Header - Minimalist */}
                        <div className="bg-[#202024] rounded-2xl border border-gray-800 overflow-hidden shadow-xl">
                            <div className="h-32 bg-gradient-to-r from-gray-900 via-[#1a1a1e] to-gray-900 relative">
                                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
                            </div>
                            <div className="px-8 pb-8 -mt-12 relative flex justify-between items-end">
                                <div>
                                    <div className="w-24 h-24 bg-[#121214] rounded-2xl border-4 border-[#202024] flex items-center justify-center shadow-lg">
                                        <Shield className="w-12 h-12 text-white" />
                                    </div>
                                    <div className="mt-4">
                                        <h1 className="text-3xl font-bold text-white tracking-tight">{clan.nome}</h1>
                                        <p className="text-gray-400 mt-1">{clan.descricao}</p>
                                    </div>
                                </div>
                                <div className="flex gap-3">
                                    <button
                                        onClick={handleLeaveClan}
                                        className="px-4 py-2 bg-red-500/10 text-red-400 rounded-lg hover:bg-red-500/20 transition-colors text-sm font-medium flex items-center gap-2"
                                    >
                                        <LogOut className="w-4 h-4" /> Sair
                                    </button>
                                    {(user?.papel === 'admin' || user?.papel === 'gestor') && (
                                        <button
                                            onClick={handleDeleteClan}
                                            className="px-4 py-2 bg-red-500/10 text-red-400 rounded-lg hover:bg-red-500/20 transition-colors text-sm font-medium flex items-center gap-2"
                                        >
                                            <Trash2 className="w-4 h-4" /> Excluir
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="grid lg:grid-cols-3 gap-8">
                            <div className="lg:col-span-2 space-y-8">
                                {/* Members List */}
                                <div className="bg-[#202024] rounded-2xl border border-gray-800 p-6">
                                    <div className="flex justify-between items-center mb-6">
                                        <h3 className="text-lg font-medium text-white flex items-center gap-2">
                                            <Users className="w-5 h-5 text-gray-400" />
                                            Membros
                                            <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full">{members.length}</span>
                                        </h3>
                                    </div>
                                    <div className="grid sm:grid-cols-2 gap-4">
                                        {members.map(member => (
                                            <div key={member.id} className="bg-[#121214] p-3 rounded-xl border border-gray-800 flex items-center gap-4 hover:border-gray-700 transition-colors">
                                                <div className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center overflow-hidden">
                                                    {member.user_avatar ? (
                                                        <img src={member.user_avatar} alt="" className="w-full h-full object-cover" />
                                                    ) : (
                                                        <span className="font-medium text-gray-400">{member.user_nome[0]}</span>
                                                    )}
                                                </div>
                                                <div>
                                                    <Link to={member.user_id ? `/profile/${member.user_id}` : '#'} className={`font-medium text-sm hover:text-blue-400 transition-colors ${!member.user_id ? 'pointer-events-none text-gray-400' : 'text-gray-200'}`}>
                                                        {member.user_nome}
                                                    </Link>
                                                    <span className={`block w-fit text-[10px] px-2 py-0.5 rounded-full mt-1 uppercase tracking-wider font-bold ${member.papel === 'lider' ? 'bg-yellow-500/10 text-yellow-500' : 'bg-gray-800 text-gray-500'
                                                        }`}>
                                                        {member.papel}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Clan Missions */}
                                <div className="bg-[#202024] rounded-2xl border border-gray-800 p-6">
                                    <h3 className="text-lg font-medium text-white mb-6 flex items-center gap-2">
                                        <Shield className="w-5 h-5 text-gray-400" />
                                        Missões Ativas
                                    </h3>
                                    {clanMissions.length === 0 ? (
                                        <div className="text-center py-8 text-gray-500 bg-[#121214] rounded-xl border border-gray-800 border-dashed">
                                            Nenhuma missão ativa no momento
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            {clanMissions.map(mission => (
                                                <div key={mission.id} className="bg-[#121214] p-5 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                                                    <div className="flex justify-between items-start mb-2">
                                                        <h4 className="font-medium text-white">{mission.titulo}</h4>
                                                        <span className="text-xs bg-yellow-500/10 text-yellow-500 px-2 py-1 rounded font-medium">
                                                            +{mission.moedas} Moedas
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-400 leading-relaxed">{mission.descricao}</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Leader Progress View */}
                                {clan.lider_id === user?.id && missionProgress.length > 0 && (
                                    <div className="bg-[#202024] rounded-2xl border border-gray-800 p-6">
                                        <h3 className="text-lg font-medium text-white mb-6 flex items-center gap-2">
                                            <Shield className="w-5 h-5 text-emerald-500" />
                                            Progresso das Missões (Líder)
                                        </h3>
                                        <div className="space-y-6">
                                            {missionProgress.map((prog, idx) => (
                                                <div key={idx} className="bg-[#121214] p-5 rounded-xl border border-gray-800">
                                                    <h4 className="font-medium text-white mb-4 border-b border-gray-800 pb-2">{prog.mission.titulo}</h4>

                                                    <div className="grid md:grid-cols-2 gap-6">
                                                        <div>
                                                            <p className="text-xs font-bold text-emerald-500 uppercase tracking-wider mb-3">Completaram ({prog.completed_by.length})</p>
                                                            {prog.completed_by.length === 0 ? (
                                                                <p className="text-xs text-gray-600 italic">Ninguém ainda</p>
                                                            ) : (
                                                                <div className="space-y-2">
                                                                    {prog.completed_by.map((m: any) => (
                                                                        <div key={m.id} className="flex items-center gap-2 text-sm text-gray-300">
                                                                            <Check className="w-3 h-3 text-emerald-500" />
                                                                            {m.user_nome}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-bold text-red-500 uppercase tracking-wider mb-3">Pendentes ({prog.pending_by.length})</p>
                                                            {prog.pending_by.length === 0 ? (
                                                                <p className="text-xs text-gray-600 italic">Todos completaram!</p>
                                                            ) : (
                                                                <div className="space-y-2">
                                                                    {prog.pending_by.map((m: any) => (
                                                                        <div key={m.id} className="flex items-center gap-2 text-sm text-gray-400">
                                                                            <div className="w-1.5 h-1.5 rounded-full bg-red-500/50"></div>
                                                                            {m.user_nome}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="space-y-8">
                                {/* Invite Action (Leader Only) */}
                                {clan.lider_id === user?.id && (
                                    <div className="bg-[#202024] rounded-2xl border border-gray-800 p-6">
                                        <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                                            <UserPlus className="w-5 h-5 text-blue-500" />
                                            Convidar Membro
                                        </h3>
                                        <div className="space-y-4">
                                            <div className="relative">
                                                <input
                                                    type="text"
                                                    placeholder="Buscar aluno..."
                                                    value={searchQuery}
                                                    onChange={e => setSearchQuery(e.target.value)}
                                                    className="w-full bg-[#121214] border border-gray-700 rounded-lg p-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none text-sm"
                                                />
                                            </div>
                                            {searchResults.length > 0 && (
                                                <div className="bg-[#121214] rounded-lg max-h-48 overflow-y-auto border border-gray-700 custom-scrollbar">
                                                    {searchResults.map(u => (
                                                        <div key={u.id} className="p-3 hover:bg-gray-800 flex justify-between items-center border-b border-gray-800 last:border-0 transition-colors">
                                                            <div>
                                                                <p className="font-medium text-sm text-white">{u.nome}</p>
                                                                <p className="text-xs text-gray-500">{u.email}</p>
                                                            </div>
                                                            <button
                                                                onClick={() => handleInvite(u.email)}
                                                                className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-md transition-colors"
                                                            >
                                                                Convidar
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            {searchQuery.length > 2 && searchResults.length === 0 && (
                                                <p className="text-sm text-gray-500 text-center py-2">Nenhum aluno encontrado.</p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Clan Chat */}
                                <div className="bg-[#202024] rounded-2xl border border-gray-800 overflow-hidden">
                                    <div className="p-4 border-b border-gray-800">
                                        <h3 className="text-lg font-medium text-white">Chat do Clã</h3>
                                    </div>
                                    <div className="p-4">
                                        <ClanChat clanId={clan.id} currentUserId={user?.id || 0} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
