import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Target, LogOut, Star, User, Users, Image, QrCode } from 'lucide-react';
import apiClient from '../api/client';
import { Ranking } from '../components/Ranking';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config/api';
import { ThemeSwitcher } from '../components/ThemeSwitcher';

interface Mission {
    id: number;
    titulo: string;
    descricao: string;
    pontos: number;
    moedas: number;
    categoria: string;
    status: 'disponivel' | 'pendente' | 'aprovada';
}

export const StudentDashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [missions, setMissions] = useState<Mission[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'disponivel' | 'pendente' | 'aprovada'>('disponivel');
    const [showQrModal, setShowQrModal] = useState(false);

    const [receivedMissions, setReceivedMissions] = useState<any[]>([]);

    useEffect(() => {
        fetchMissions();
        fetchReceivedMissions();
    }, []);

    const fetchReceivedMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/recebidas');
            setReceivedMissions(response.data);
        } catch (error) {
            console.error('Failed to fetch received missions:', error);
        }
    };

    const handleAcceptMission = async (id: number) => {
        try {
            await apiClient.post(`/missoes/atribuidas/${id}/aceitar`);
            alert('Missão aceita! Ela agora está disponível para realização.');
            fetchReceivedMissions();
            fetchMissions();
        } catch (error) {
            alert('Erro ao aceitar missão');
        }
    };

    const handleRejectMission = async (id: number) => {
        if (!confirm('Tem certeza que deseja recusar esta missão?')) return;
        try {
            await apiClient.post(`/missoes/atribuidas/${id}/recusar`);
            alert('Missão recusada.');
            fetchReceivedMissions();
        } catch (error) {
            alert('Erro ao recusar missão');
        }
    };

    const fetchMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/');
            setMissions(response.data);
        } catch (error) {
            console.error('Failed to fetch missions:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const completeMission = async (missionId: number) => {
        try {
            await apiClient.post(`/missoes/${missionId}/completar`);
            alert('Missão enviada para validação!');
            fetchMissions(); // Refresh to update status
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao completar missão');
        }
    };

    if (!user) return null;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            {/* Header */}
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Olá, {user.nome}! 👋</h1>
                    <p className="text-gray-400">{user.serie} • Nível {user.nivel}{user.escola_nome ? ` • ${user.escola_nome}` : ''}</p>
                </div>
                <div className="flex items-center gap-4">


                    <button
                        onClick={() => setShowQrModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors"
                    >
                        <QrCode className="w-4 h-4" />
                        Meu QR
                    </button>
                    <button
                        onClick={() => navigate('/profile')}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    >
                        <User className="w-4 h-4" />
                        Meu Perfil
                    </button>
                    <button
                        onClick={logout}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                        Sair
                    </button>
                </div>
            </header>

            {showQrModal && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setShowQrModal(false)}>
                    <div className="bg-white rounded-2xl p-8 w-full max-w-sm text-center relative" onClick={e => e.stopPropagation()}>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">Seu QR Code</h2>
                        <p className="text-gray-500 mb-6">Apresente este código ao professor para validar missões.</p>

                        <div className="flex justify-center mb-6">
                            {user.qr_token ? (
                                <img
                                    src={`https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=schoolquest:token:${user.qr_token}`}
                                    alt="QR Code"
                                    className="w-64 h-64"
                                />
                            ) : (
                                <div className="w-64 h-64 bg-gray-200 flex items-center justify-center text-gray-500">
                                    QR Token não encontrado
                                </div>
                            )}
                        </div>

                        <p className="text-xs text-gray-400 font-mono break-all mb-6">
                            {user.qr_token || 'Sem token'}
                        </p>

                        <button
                            onClick={() => setShowQrModal(false)}
                            className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl transition-colors"
                        >
                            Fechar
                        </button>
                    </div>
                </div>
            )}

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                    {/* Stats & Actions Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                        {/* Moedas Card */}
                        <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 flex items-center gap-4">
                            <div className="p-3 bg-yellow-500/20 rounded-xl">
                                <Star className="w-8 h-8 text-yellow-400" />
                            </div>
                            <div>
                                <p className="text-gray-400 text-sm">Moedas</p>
                                <p className="text-2xl font-bold">{user.moedas}</p>
                            </div>
                        </div>

                        {/* Quick Actions Card */}
                        <div className="grid grid-cols-3 gap-4">
                            <button
                                onClick={() => navigate('/clans')}
                                className="p-4 bg-purple-900/30 border border-purple-500/30 rounded-xl hover:bg-purple-900/50 transition-all flex flex-col items-center justify-center gap-2 group"
                            >
                                <Users className="w-6 h-6 text-purple-400 group-hover:scale-110 transition-transform" />
                                <span className="font-bold text-purple-200 text-sm">Meu Clã</span>
                            </button>

                            <button
                                onClick={() => navigate('/mural')}
                                className="p-4 bg-pink-900/30 border border-pink-500/30 rounded-xl hover:bg-pink-900/50 transition-all flex flex-col items-center justify-center gap-2 group"
                            >
                                <Image className="w-6 h-6 text-pink-400 group-hover:scale-110 transition-transform" />
                                <span className="font-bold text-pink-200 text-sm">Mural</span>
                            </button>



                            <button
                                onClick={() => navigate('/shop')}
                                className="p-4 bg-yellow-900/30 border border-yellow-500/30 rounded-xl hover:bg-yellow-900/50 transition-all flex flex-col items-center justify-center gap-2 group"
                            >
                                <Target className="w-6 h-6 text-yellow-400 group-hover:scale-110 transition-transform" />
                                <span className="font-bold text-yellow-200 text-sm">Lojinha</span>
                            </button>
                        </div>
                    </div>

                    {/* Inbox / Received Missions */}
                    {receivedMissions.length > 0 && (
                        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 mb-8">
                            <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                                </span>
                                Missões Recebidas
                            </h2>
                            <div className="grid gap-4">
                                {receivedMissions.map((mission) => (
                                    <div key={mission.id} className="bg-gray-700/50 p-4 rounded-xl border border-purple-500/30 flex justify-between items-center">
                                        <div>
                                            <h3 className="font-bold text-lg">{mission.missao?.titulo}</h3>
                                            <p className="text-sm text-gray-300">Atribuída por Professor</p>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleAcceptMission(mission.id)}
                                                className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg font-bold text-sm"
                                            >
                                                Aceitar
                                            </button>
                                            <button
                                                onClick={() => handleRejectMission(mission.id)}
                                                className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg font-bold text-sm"
                                            >
                                                Recusar
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Missions Section */}
                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                        <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <Target className="w-6 h-6 text-primary" />
                                Missões
                            </h2>

                            {/* Tabs */}
                            <div className="flex bg-gray-700 rounded-lg p-1">
                                <button
                                    onClick={() => setActiveTab('disponivel')}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'disponivel'
                                        ? 'bg-blue-600 text-white shadow'
                                        : 'text-gray-300 hover:text-white'
                                        }`}
                                >
                                    Disponíveis
                                </button>
                                <button
                                    onClick={() => setActiveTab('pendente')}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'pendente'
                                        ? 'bg-yellow-600 text-white shadow'
                                        : 'text-gray-300 hover:text-white'
                                        }`}
                                >
                                    Em Análise
                                </button>
                                <button
                                    onClick={() => setActiveTab('aprovada')}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'aprovada'
                                        ? 'bg-green-600 text-white shadow'
                                        : 'text-gray-300 hover:text-white'
                                        }`}
                                >
                                    Concluídas
                                </button>
                            </div>
                        </div>

                        {isLoading ? (
                            <p className="text-center text-gray-400 py-8">Carregando missões...</p>
                        ) : missions.filter(m => m.status === activeTab).length === 0 ? (
                            <div className="text-center py-12 text-gray-400 bg-gray-900/50 rounded-xl border border-gray-700 border-dashed">
                                <p>Nenhuma missão {
                                    activeTab === 'disponivel' ? 'disponível' :
                                        activeTab === 'pendente' ? 'em análise' : 'concluída'
                                } no momento.</p>
                            </div>
                        ) : (
                            <div className="grid md:grid-cols-1 gap-4">
                                {missions.filter(m => m.status === activeTab).map((mission) => (
                                    <div
                                        key={mission.id}
                                        className={`bg-gray-700/50 p-4 rounded-xl border transition-all hover:bg-gray-700 ${activeTab === 'disponivel' ? 'border-gray-600 hover:border-primary' :
                                            activeTab === 'pendente' ? 'border-yellow-500/30' :
                                                'border-green-500/30'
                                            }`}
                                    >
                                        <div className="flex justify-between items-start mb-2">
                                            <div>
                                                <h3 className="font-bold text-lg mb-1">{mission.titulo}</h3>
                                                <span className="px-2 py-0.5 bg-blue-900/50 text-blue-200 text-xs rounded-full border border-blue-500/30">
                                                    {mission.categoria}
                                                </span>
                                            </div>
                                            <div className="flex gap-2 text-sm font-mono">
                                                <span className="text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded">+{mission.pontos} XP</span>
                                                <span className="text-green-400 bg-green-400/10 px-2 py-1 rounded">+{mission.moedas} 🪙</span>
                                            </div>
                                        </div>

                                        <p className="text-gray-300 text-sm mb-4">{mission.descricao}</p>

                                        <div className="flex justify-end">
                                            {activeTab === 'disponivel' && (
                                                <button
                                                    onClick={() => completeMission(mission.id)}
                                                    className="px-6 py-2 bg-primary hover:bg-blue-600 rounded-lg text-sm font-bold transition-colors shadow-lg shadow-blue-600/20"
                                                >
                                                    Completar Missão
                                                </button>
                                            )}

                                            {activeTab === 'pendente' && (
                                                <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-bold rounded-full border border-yellow-500/50 flex items-center gap-2">
                                                    <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
                                                    Aguardando Validação
                                                </span>
                                            )}

                                            {activeTab === 'aprovada' && (
                                                <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded-full border border-green-500/50 flex items-center gap-2">
                                                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                                    Aprovada
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                </div>

                {/* Sidebar */}
                <div className="space-y-8">
                    {/* Perfil */}
                    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 text-center">
                        <div className="w-24 h-24 bg-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center text-3xl font-bold border-4 border-gray-700 overflow-hidden">
                            {user?.avatar_url ? (
                                <img
                                    src={user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`}
                                    alt="Avatar"
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                        e.currentTarget.style.display = 'none';
                                        e.currentTarget.parentElement!.innerText = user.nome.charAt(0);
                                    }}
                                />
                            ) : (
                                user?.nome.charAt(0)
                            )}
                        </div>
                        <h2 className="text-xl font-bold mb-1">{user?.nome}</h2>
                        <p className="text-purple-400 mb-1">Nível {user?.nivel} • Mago Iniciante</p>
                        {user?.serie && (
                            <p className="text-gray-400 text-sm mb-4">{user.serie}</p>
                        )}

                        <div className="bg-gray-700/50 rounded-lg p-3 mb-2">
                            <div className="flex justify-between text-sm mb-1">
                                <span>XP Atual</span>
                                <span className="font-bold text-yellow-400">{user?.xp} / {user?.nivel * 1000}</span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                                <div
                                    className="bg-yellow-400 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${(user?.xp || 0) % 1000 / 10}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>

                    {/* Ranking */}
                    <Ranking />
                </div>
            </div>

            <ThemeSwitcher />
        </div >
    );
};
