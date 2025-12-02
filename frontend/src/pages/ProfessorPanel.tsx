import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Plus, LogOut, CheckCircle, QrCode, Trash2, MessageSquare, ShoppingBag, XCircle } from 'lucide-react';
import apiClient from '../api/client';
import { Ranking } from '../components/Ranking';
import { Html5Qrcode } from 'html5-qrcode';
import { ThemeSwitcher } from '../components/ThemeSwitcher';
import { Link } from 'react-router-dom';



export const ProfessorPanel: React.FC = () => {
    const { user, logout } = useAuth();
    const [isCreating, setIsCreating] = useState(false);
    const [validatingMissionId, setValidatingMissionId] = useState<number | null>(null);

    const [myMissions, setMyMissions] = useState<any[]>([]);
    const [pendingMissions, setPendingMissions] = useState<any[]>([]);
    const [completedMissions, setCompletedMissions] = useState<any[]>([]);
    const [clans, setClans] = useState<any[]>([]);
    const [turmas, setTurmas] = useState<any[]>([]);
    const [filterText, setFilterText] = useState('');
    const [formData, setFormData] = useState({
        titulo: '',
        descricao: '',
        pontos: 10,
        moedas: 5,
        categoria: 'diaria',
        tipo: 'individual',
        clan_id: '',
        turma_id: ''
    });
    const html5QrCodeRef = useRef<Html5Qrcode | null>(null);

    // Shop State
    const [rewards, setRewards] = useState<any[]>([]);
    const [newReward, setNewReward] = useState({ nome: '', descricao: '', custo: 0, estoque: 1, imagem_url: '' });
    const [showShopManager, setShowShopManager] = useState(false);
    const [pendingPurchases, setPendingPurchases] = useState<any[]>([]);
    const [showApprovals, setShowApprovals] = useState(false);

    useEffect(() => {
        fetchMyMissions();
        fetchPendingMissions();
        fetchCompletedMissions();
        fetchClans();
        fetchTurmas();
        fetchRewards();
        fetchPendingPurchases();

        return () => {
            if (html5QrCodeRef.current?.isScanning) {
                html5QrCodeRef.current.stop().catch(console.error);
            }
        };
    }, []);

    const fetchClans = async () => {
        try {
            const response = await apiClient.get('/clans/');
            setClans(response.data);
        } catch (error) {
            console.error('Erro ao buscar clãs', error);
        }
    };

    const fetchTurmas = async () => {
        try {
            console.log('Fetching turmas...');
            const response = await apiClient.get('/missoes/turmas');
            console.log('Turmas response:', response.data);

            if (Array.isArray(response.data)) {
                setTurmas(response.data);
                console.log('Turmas state updated with', response.data.length, 'items');
            } else {
                console.error('Invalid turmas response format:', response.data);
                setTurmas([]);
            }
        } catch (error) {
            console.error('Erro ao buscar turmas', error);
            setTurmas([]);
        }
    };

    const fetchPendingMissions = async () => {
        try {
            console.log('Fetching pending missions...');
            const response = await apiClient.get('/missoes/pendentes');
            console.log('Pending missions response:', response.data);
            setPendingMissions(response.data);
            if (response.data.length === 0) {
                console.log('No pending missions found');
            }
        } catch (error: any) {
            console.error('Erro ao buscar missões pendentes:', error);
            console.error('Error details:', error.response?.data);
        }
    };

    const fetchCompletedMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/professor/concluidas');
            setCompletedMissions(response.data);
        } catch (error) {
            console.error('Erro ao buscar missões concluídas', error);
        }
    };

    const handleValidateMission = async (submissaoId: number, aprovado: boolean) => {
        try {
            await apiClient.post(`/missoes/validar/${submissaoId}?aprovado=${aprovado}`);
            alert(aprovado ? 'Missão aprovada!' : 'Missão rejeitada!');
            fetchPendingMissions();
            fetchCompletedMissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao validar missão');
        }
    };

    // Shop Management Functions
    const fetchRewards = async () => {
        try {
            const res = await apiClient.get('/shop/');
            setRewards(res.data);
        } catch (error) {
            console.error("Error fetching rewards", error);
        }
    };

    const fetchPendingPurchases = async () => {
        try {
            const res = await apiClient.get('/loja/compras/pendentes');
            setPendingPurchases(res.data);
        } catch (error) {
            console.error("Error fetching pending purchases", error);
        }
    };

    const handleCreateReward = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await apiClient.post('/shop/items', newReward);
            alert('Recompensa criada!');
            setNewReward({ nome: '', descricao: '', custo: 0, estoque: 1, imagem_url: '' });
            fetchRewards();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao criar recompensa');
        }
    };

    const handleDeleteReward = async (id: number) => {
        if (!confirm('Deletar recompensa?')) return;
        try {
            await apiClient.delete(`/shop/items/${id}`);
            fetchRewards();
        } catch (error) {
            alert('Erro ao deletar');
        }
    };

    const handleApprovePurchase = async (id: number) => {
        try {
            await apiClient.post(`/loja/compras/${id}/aprovar`);
            alert('Compra aprovada!');
            fetchPendingPurchases();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao aprovar');
        }
    };

    const handleRejectPurchase = async (id: number) => {
        if (!confirm('Rejeitar esta compra e devolver as moedas?')) return;
        try {
            await apiClient.post(`/loja/compras/${id}/rejeitar`);
            alert('Compra rejeitada!');
            fetchPendingPurchases();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao rejeitar');
        }
    };



    const fetchMyMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/');
            // Filter missions created by me
            const my = response.data.filter((m: any) => m.criador_id === user?.id);
            setMyMissions(my);
        } catch (error) {
            console.error('Erro ao buscar minhas missões', error);
        }
    };

    const handleDeleteMission = async (id: number) => {
        if (!confirm('Tem certeza que deseja excluir esta missão?')) return;
        try {
            await apiClient.delete(`/missoes/${id}`);
            alert('Missão excluída!');
            fetchMyMissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao excluir missão');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload: any = { ...formData };
            if (payload.tipo === 'clan' && payload.clan_id) {
                payload.clan_id = parseInt(payload.clan_id);
                delete payload.turma_id;
            } else if (payload.tipo === 'turma' && payload.turma_id) {
                payload.turma_id = parseInt(payload.turma_id);
                delete payload.clan_id;
            } else {
                delete payload.clan_id;
                delete payload.turma_id;
            }

            await apiClient.post('/missoes/', payload);
            alert('Missão criada com sucesso!');
            setFormData({
                titulo: '',
                descricao: '',
                pontos: 10,
                moedas: 5,
                categoria: 'diaria',
                tipo: 'individual',
                clan_id: '',
                turma_id: ''
            });
            setIsCreating(false);
            fetchMyMissions(); // Refresh list after creation
        } catch (error) {
            alert('Erro ao criar missão');
        }
    };

    const validateQrCode = async (qrData: string) => {
        if (!validatingMissionId) return;

        try {
            let payload: any = {};

            // Check for URL format: https://domain/qr/USER_ID/TOKEN
            if (qrData.includes('/qr/')) {
                const parts = qrData.split('/qr/')[1]?.split('/');
                if (parts && parts.length >= 2) {
                    const userId = parseInt(parts[0]);
                    const token = parts[1];
                    if (!isNaN(userId) && token) {
                        payload = { aluno_id: userId, qr_token: token };
                    }
                }
            }
            // Check for token format: schoolquest:token:{token}
            else if (qrData.startsWith('schoolquest:token:')) {
                const token = qrData.split(':')[2];
                payload = { qr_token: token };
            }
            // Check for user format: schoolquest:user:{id}:{token}
            else if (qrData.startsWith('schoolquest:user:')) {
                const parts = qrData.split(':');
                const userId = parseInt(parts[2]);
                const token = parts[3];
                if (!isNaN(userId) && token) {
                    payload = { aluno_id: userId, qr_token: token };
                }
            } else {
                alert('Formato de QR Code inválido');
                return;
            }

            if (!payload.qr_token && !payload.aluno_id) {
                alert('Dados do QR Code inválidos');
                return;
            }

            const res = await apiClient.post(`/missoes/${validatingMissionId}/validar_presencial`, payload);

            alert(res.data.message);

            // Close scanner if successful
            setValidatingMissionId(null);
            fetchCompletedMissions();

        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao validar QR Code');
        }
    };

    // Scanner logic moved to QrScanner component

    if (!user) return null;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            {/* Header */}
            <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold">Painel do Professor</h1>
                    <p className="text-gray-400">Gerencie missões e alunos{user?.escola_nome ? ` • ${user.escola_nome}` : ''}</p>
                </div>
                <div className="flex items-center gap-3">
                    <Link
                        to="/mural"
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
                    >
                        <MessageSquare className="w-4 h-4" />
                        Mural
                    </Link>
                    <button
                        onClick={() => setShowShopManager(!showShopManager)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors"
                    >
                        <ShoppingBag className="w-4 h-4" />
                        Gerenciar Loja
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

            {/* Shop Manager Section */}
            {showShopManager && (
                <div className="mb-8 animate-fade-in">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <ShoppingBag className="w-6 h-6 text-purple-400" />
                            Gerenciar Loja
                        </h2>
                        <button
                            onClick={() => setShowApprovals(!showApprovals)}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg font-bold transition-colors relative"
                        >
                            <CheckCircle className="w-5 h-5" />
                            Aprovações
                            {pendingPurchases.length > 0 && (
                                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                    {pendingPurchases.length}
                                </span>
                            )}
                        </button>
                    </div>

                    {/* Approvals Section */}
                    {showApprovals && (
                        <div className="bg-gray-700/30 p-4 rounded-xl border border-gray-600 mb-6 animate-fade-in">
                            <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-green-400">
                                <CheckCircle className="w-5 h-5" />
                                Aprovações Pendentes
                            </h3>

                            {pendingPurchases.length === 0 ? (
                                <p className="text-gray-400 text-sm">Nenhuma compra pendente.</p>
                            ) : (
                                <div className="grid gap-3">
                                    {pendingPurchases.map(p => (
                                        <div key={p.id} className="bg-gray-700 p-3 rounded-lg flex justify-between items-center border border-gray-600">
                                            <div>
                                                <p className="font-bold">{p.item_nome || p.reward_nome}</p>
                                                <p className="text-xs text-gray-300">Aluno: <span className="text-white font-bold">{p.user_nome}</span></p>
                                                <p className="text-xs text-gray-400">Custo: {p.custo_pago} moedas • {new Date(p.data_compra).toLocaleDateString()}</p>
                                            </div>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => handleApprovePurchase(p.id)}
                                                    className="px-3 py-1 bg-green-600 hover:bg-green-500 rounded text-xs font-bold flex items-center gap-1"
                                                >
                                                    <CheckCircle className="w-3 h-3" /> Aprovar
                                                </button>
                                                <button
                                                    onClick={() => handleRejectPurchase(p.id)}
                                                    className="px-3 py-1 bg-red-600 hover:bg-red-500 rounded text-xs font-bold flex items-center gap-1"
                                                >
                                                    <XCircle className="w-3 h-3" /> Rejeitar
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Form */}
                        <div className="bg-gray-700/50 p-4 rounded-lg h-fit">
                            <h3 className="font-bold mb-3">Nova Recompensa</h3>
                            <form onSubmit={handleCreateReward} className="space-y-3">
                                <input
                                    type="text"
                                    placeholder="Nome do Item"
                                    value={newReward.nome}
                                    onChange={e => setNewReward({ ...newReward, nome: e.target.value })}
                                    className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    required
                                />
                                <textarea
                                    placeholder="Descrição"
                                    value={newReward.descricao}
                                    onChange={e => setNewReward({ ...newReward, descricao: e.target.value })}
                                    className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    required
                                />
                                <div className="grid grid-cols-2 gap-2">
                                    <input
                                        type="number"
                                        placeholder="Custo (Moedas)"
                                        value={newReward.custo}
                                        onChange={e => setNewReward({ ...newReward, custo: parseInt(e.target.value) })}
                                        className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                        required
                                    />
                                    <input
                                        type="number"
                                        placeholder="Estoque"
                                        value={newReward.estoque}
                                        onChange={e => setNewReward({ ...newReward, estoque: parseInt(e.target.value) })}
                                        className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                        required
                                    />
                                </div>
                                <div>
                                    <input
                                        type="text"
                                        placeholder="URL da Imagem (Opcional)"
                                        value={newReward.imagem_url || ''}
                                        onChange={e => setNewReward({ ...newReward, imagem_url: e.target.value })}
                                        className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    />
                                </div>
                                <button type="submit" className="w-full bg-green-600 hover:bg-green-500 py-2 rounded font-bold">
                                    Adicionar Item
                                </button>
                            </form>
                        </div>

                        {/* List */}
                        <div className="md:col-span-2 grid sm:grid-cols-2 gap-4">
                            {rewards.map(item => (
                                <div key={item.id} className="bg-gray-700 p-3 rounded-lg flex justify-between items-start border border-gray-600">
                                    <div>
                                        <h4 className="font-bold">{item.nome}</h4>
                                        <p className="text-xs text-gray-400 mb-1">{item.descricao}</p>
                                        <div className="flex gap-2 text-xs font-mono">
                                            <span className="text-yellow-400">{item.custo} Moedas</span>
                                            <span className="text-blue-300">Estoque: {item.estoque}</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteReward(item.id)}
                                        className="text-red-400 hover:text-red-300 p-1"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Create Mission */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <BookOpen className="w-6 h-6 text-primary" />
                                Criar Nova Missão
                            </h2>
                            {!isCreating && (
                                <button
                                    onClick={() => setIsCreating(true)}
                                    className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-blue-600 rounded-lg transition-colors"
                                >
                                    <Plus className="w-4 h-4" />
                                    Nova Missão
                                </button>
                            )}
                        </div>

                        {isCreating && (
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label htmlFor="mission-title" className="block text-gray-300 text-sm font-medium mb-2">
                                        Título da Missão
                                    </label>
                                    <input
                                        id="mission-title"
                                        name="titulo"
                                        type="text"
                                        value={formData.titulo}
                                        onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Ex: Resolver 10 exercícios de Matemática"
                                        required
                                    />
                                </div>

                                <div>
                                    <label htmlFor="mission-description" className="block text-gray-300 text-sm font-medium mb-2">
                                        Descrição
                                    </label>
                                    <textarea
                                        id="mission-description"
                                        name="descricao"
                                        value={formData.descricao}
                                        onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Descreva os objetivos da missão..."
                                        rows={3}
                                        required
                                    />
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Pontos XP
                                        </label>
                                        <input
                                            type="number"
                                            value={formData.pontos}
                                            onChange={(e) => setFormData({ ...formData, pontos: parseInt(e.target.value) })}
                                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                            min="1"
                                            required
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Moedas
                                        </label>
                                        <input
                                            type="number"
                                            value={formData.moedas}
                                            onChange={(e) => setFormData({ ...formData, moedas: parseInt(e.target.value) })}
                                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                            min="1"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Categoria
                                        </label>
                                        <select
                                            value={formData.categoria}
                                            onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                        >
                                            <option value="diaria">Diária</option>
                                            <option value="semanal">Semanal</option>
                                            <option value="especial">Especial</option>
                                            <option value="escolar">Escolar</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Tipo de Missão
                                        </label>
                                        <select
                                            value={formData.tipo}
                                            onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                        >
                                            <option value="individual">Individual (Aluno)</option>
                                            <option value="clan">Clã (Coletiva)</option>
                                            <option value="turma">Turma (Série)</option>
                                        </select>
                                    </div>
                                </div>

                                {formData.tipo === 'clan' && (
                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Selecione o Clã
                                        </label>
                                        <select
                                            value={formData.clan_id}
                                            onChange={(e) => setFormData({ ...formData, clan_id: e.target.value })}
                                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                            required
                                        >
                                            <option value="">Selecione um clã...</option>
                                            {clans.map(clan => (
                                                <option key={clan.id} value={clan.id}>{clan.nome}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}

                                {formData.tipo === 'turma' && (
                                    <div>
                                        <label className="block text-gray-300 text-sm font-medium mb-2">
                                            Selecione a Turma
                                        </label>
                                        <select
                                            value={formData.turma_id}
                                            onChange={(e) => setFormData({ ...formData, turma_id: e.target.value })}
                                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                            required
                                        >
                                            <option value="">Selecione uma turma...</option>
                                            {turmas.length === 0 ? (
                                                <option value="" disabled>Nenhuma turma encontrada</option>
                                            ) : (
                                                turmas.map(turma => (
                                                    <option key={turma.id} value={turma.id}>{turma.nome}</option>
                                                ))
                                            )}
                                        </select>
                                    </div>
                                )}

                                <div className="flex gap-3">
                                    <button
                                        type="submit"
                                        className="px-6 py-3 bg-primary hover:bg-blue-600 text-white font-bold rounded-lg transition-colors"
                                    >
                                        Criar Missão
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setIsCreating(false)}
                                        className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-bold rounded-lg transition-colors"
                                    >
                                        Cancelar
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>

                    {/* My Missions */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <BookOpen className="w-6 h-6 text-blue-400" />
                                Minhas Missões Ativas
                            </h2>
                        </div>

                        {myMissions.length === 0 ? (
                            <p className="text-gray-400">Você ainda não criou nenhuma missão.</p>
                        ) : (
                            <div className="space-y-3">
                                {myMissions.map((mission) => (
                                    <div key={mission.id} className="bg-gray-700 p-4 rounded-lg border border-gray-600 flex justify-between items-center">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="font-bold text-lg">{mission.titulo}</h3>
                                                {mission.tipo === 'clan' && (
                                                    <span className="px-2 py-0.5 bg-purple-900 text-purple-200 text-xs rounded border border-purple-500/30">
                                                        Clã
                                                    </span>
                                                )}
                                                {mission.tipo === 'turma' && (
                                                    <span className="px-2 py-0.5 bg-indigo-900 text-indigo-200 text-xs rounded border border-indigo-500/30">
                                                        Turma
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-300">{mission.descricao}</p>
                                            <div className="flex gap-2 mt-1 text-xs">
                                                <span className="text-yellow-400">{mission.pontos} XP</span>
                                                <span className="text-green-400">{mission.moedas} Moedas</span>
                                                <span className="bg-blue-900 px-2 rounded text-blue-200">{mission.categoria}</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">

                                            <button
                                                onClick={() => handleDeleteMission(mission.id)}
                                                className="p-2 text-red-400 hover:bg-red-900/30 rounded-lg transition-colors"
                                                title="Excluir Missão"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                            <button
                                                onClick={() => {
                                                    setValidatingMissionId(mission.id);
                                                }}
                                                className="p-2 text-purple-400 hover:bg-purple-900/30 rounded-lg transition-colors"
                                                title="Validar Presencialmente (QR)"
                                            >
                                                <QrCode className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>



                    {/* Pending Missions */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <CheckCircle className="w-6 h-6 text-yellow-400" />
                                Missões Pendentes de Validação
                            </h2>
                            <div className="w-full md:w-64">
                                <input
                                    type="text"
                                    placeholder="Filtrar por aluno, missão..."
                                    value={filterText}
                                    onChange={(e) => setFilterText(e.target.value)}
                                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                />
                            </div>
                        </div>
                        {pendingMissions.length === 0 ? (
                            <p className="text-gray-400">Nenhuma missão pendente de validação.</p>
                        ) : (
                            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                                {pendingMissions
                                    .filter(pending =>
                                        pending.aluno_nome.toLowerCase().includes(filterText.toLowerCase()) ||
                                        pending.missao_titulo.toLowerCase().includes(filterText.toLowerCase()) ||
                                        (pending.aluno_serie && pending.aluno_serie.toLowerCase().includes(filterText.toLowerCase()))
                                    )
                                    .map((pending) => (
                                        <div key={pending.id} className="bg-gray-700 p-3 rounded-lg border border-yellow-600/30">
                                            <div className="flex justify-between items-start gap-3">
                                                <div className="flex-1 min-w-0">
                                                    <h3 className="font-bold text-base truncate">{pending.missao_titulo}</h3>
                                                    <div className="text-xs text-gray-300">
                                                        <Link to={`/profile/${pending.aluno_id}`} className="hover:text-blue-400 hover:underline font-bold transition-colors">
                                                            {pending.aluno_nome}
                                                        </Link>
                                                        <span className="text-gray-400"> • {pending.aluno_serie}</span>
                                                    </div>
                                                    <p className="text-xs text-gray-400">
                                                        {new Date(pending.data_solicitacao).toLocaleDateString()}
                                                    </p>
                                                </div>
                                                <div className="flex gap-1.5 flex-shrink-0">
                                                    <button
                                                        onClick={() => handleValidateMission(pending.id, true)}
                                                        className="px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-xs font-bold transition-colors"
                                                        title="Aprovar"
                                                    >
                                                        ✓
                                                    </button>
                                                    <button
                                                        onClick={() => handleValidateMission(pending.id, false)}
                                                        className="px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded text-xs font-bold transition-colors"
                                                        title="Rejeitar"
                                                    >
                                                        ✕
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                            </div>
                        )}
                    </div>

                    {/* Completed Missions */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <CheckCircle className="w-6 h-6 text-green-400" />
                                Missões Concluídas
                            </h2>
                        </div>
                        {completedMissions.length === 0 ? (
                            <p className="text-gray-400">Nenhuma missão concluída ainda.</p>
                        ) : (
                            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                                {completedMissions.map((completion) => (
                                    <div key={completion.id} className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                                        <div>
                                            <h3 className="font-bold text-lg">{completion.missao_titulo}</h3>
                                            <p className="text-sm text-gray-300">
                                                Aluno: {completion.aluno_nome} ({completion.aluno_serie})
                                            </p>
                                            <p className="text-xs text-gray-400">
                                                Concluída em: {new Date(completion.data_validacao).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <Ranking />
                </div>
            </div>

            {/* QR Code Scanner Modal */}
            {validatingMissionId && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-2xl p-6 w-full max-w-md border border-gray-700 relative">
                        <button
                            onClick={() => {
                                setValidatingMissionId(null);
                            }}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white z-10"
                        >
                            <Trash2 className="w-6 h-6 rotate-45" />
                        </button>

                        <h2 className="text-2xl font-bold mb-4 text-center">Escanear QR Code</h2>

                        <div className="overflow-hidden rounded-xl bg-black relative mb-4">
                            <div id="qr-reader" className="w-full"></div>
                            <QrScanner
                                onScan={validateQrCode}
                                onError={(err) => console.log(err)}
                            />
                        </div>

                        <p className="text-center text-gray-400 mt-4 text-sm mb-4">
                            Aponte a câmera para o QR Code do aluno
                        </p>

                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="Ou cole o código do QR aqui..."
                                className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                id="qrInputModal"
                            />
                            <button
                                onClick={async () => {
                                    const input = document.getElementById('qrInputModal') as HTMLInputElement;
                                    if (!input.value) return;
                                    await validateQrCode(input.value);
                                    input.value = '';
                                }}
                                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg transition-colors"
                            >
                                Validar
                            </button>
                        </div>
                    </div>
                </div>
            )}
            <ThemeSwitcher />
        </div>
    );
};

// Internal component for handling QR Scanner lifecycle
const QrScanner: React.FC<{ onScan: (data: string) => void, onError: (err: any) => void }> = ({ onScan, onError }) => {
    useEffect(() => {
        const html5QrCode = new Html5Qrcode("qr-reader");

        const startScanner = async () => {
            try {
                await html5QrCode.start(
                    { facingMode: "environment" },
                    {
                        fps: 10,
                        qrbox: { width: 250, height: 250 }
                    },
                    (decodedText) => {
                        onScan(decodedText);
                    },
                    (_) => {
                        // ignore errors during scanning
                    }
                );
            } catch (err) {
                onError(err);
                console.error("Error starting scanner", err);
            }
        };

        startScanner();

        return () => {
            if (html5QrCode.isScanning) {
                html5QrCode.stop().catch(console.error);
            }
            html5QrCode.clear();
        };
    }, [onScan, onError]);

    return null;
};
