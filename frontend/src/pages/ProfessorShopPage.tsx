import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';

interface Reward {
    id: number;
    nome: string;
    descricao: string;
    custo: number;
    estoque: number;
    imagem_url?: string;
    escola_id?: number;
}

const ProfessorShopPage: React.FC = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [rewards, setRewards] = useState<Reward[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newReward, setNewReward] = useState({
        nome: '',
        descricao: '',
        custo: 0,
        estoque: -1,
        imagem_url: ''
    });

    useEffect(() => {
        if (user?.papel !== 'professor') {
            navigate('/');
            return;
        }
        fetchRewards();
    }, [user, navigate]);

    const fetchRewards = async () => {
        try {
            setLoading(true);
            const response = await apiClient.get('/shop/');
            setRewards(response.data);
        } catch (error) {
            console.error('Erro ao carregar recompensas:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateReward = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await apiClient.post('/shop/items', newReward);
            setNewReward({ nome: '', descricao: '', custo: 0, estoque: -1, imagem_url: '' });
            setShowCreateForm(false);
            fetchRewards();
        } catch (error: any) {
            console.error('Erro ao criar recompensa:', error);
            alert('Erro ao criar recompensa: ' + (error.response?.data?.detail || 'Erro desconhecido'));
        }
    };

    const handleDeleteReward = async (id: number) => {
        if (!window.confirm('Tem certeza que deseja excluir esta recompensa?')) return;

        try {
            await apiClient.delete(`/shop/items/${id}`);
            fetchRewards();
        } catch (error: any) {
            alert('Erro ao excluir: ' + (error.response?.data?.detail || 'Erro desconhecido'));
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
                <div className="text-purple-600">Carregando...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
            <div className="max-w-6xl mx-auto">
                {/* Header Discreto */}
                <div className="bg-white rounded-lg shadow-sm p-4 mb-4 flex justify-between items-center">
                    <div>
                        <h1 className="text-xl font-bold text-gray-800">Lojinha do Professor</h1>
                        <p className="text-sm text-gray-500">Gerencie recompensas para seus alunos</p>
                    </div>
                    <button
                        onClick={() => navigate('/professor')}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition text-sm"
                    >
                        ← Voltar
                    </button>
                </div>

                {/* Botão Criar */}
                <div className="mb-4">
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition text-sm"
                    >
                        {showCreateForm ? '✕ Cancelar' : '+ Nova Recompensa'}
                    </button>
                </div>

                {/* Formulário de Criação */}
                {showCreateForm && (
                    <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
                        <h2 className="text-lg font-semibold mb-3 text-gray-800">Criar Nova Recompensa</h2>
                        <form onSubmit={handleCreateReward} className="space-y-3">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                                    <input
                                        type="text"
                                        value={newReward.nome}
                                        onChange={(e) => setNewReward({ ...newReward, nome: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Custo (XP)</label>
                                    <input
                                        type="number"
                                        value={newReward.custo}
                                        onChange={(e) => setNewReward({ ...newReward, custo: parseInt(e.target.value) || 0 })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                        required
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                                <textarea
                                    value={newReward.descricao}
                                    onChange={(e) => setNewReward({ ...newReward, descricao: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                    rows={2}
                                    required
                                />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Estoque (-1 = infinito)</label>
                                    <input
                                        type="number"
                                        value={newReward.estoque}
                                        onChange={(e) => setNewReward({ ...newReward, estoque: parseInt(e.target.value) || -1 })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">URL da Imagem (opcional)</label>
                                    <input
                                        type="text"
                                        value={newReward.imagem_url}
                                        onChange={(e) => setNewReward({ ...newReward, imagem_url: e.target.value })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                                    />
                                </div>
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-purple-500 text-white py-2 rounded-lg hover:bg-purple-600 transition text-sm font-medium"
                            >
                                Criar Recompensa
                            </button>
                        </form>
                    </div>
                )}

                {/* Lista de Recompensas - Visual Compacto */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {rewards.map((reward) => (
                        <div key={reward.id} className="bg-white rounded-lg shadow-sm p-3 hover:shadow-md transition">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="font-semibold text-gray-800 text-sm">{reward.nome}</h3>
                                <button
                                    onClick={() => handleDeleteReward(reward.id)}
                                    className="text-red-500 hover:text-red-700 text-xs"
                                    title="Excluir"
                                >
                                    🗑️
                                </button>
                            </div>
                            <p className="text-xs text-gray-600 mb-2 line-clamp-2">{reward.descricao}</p>
                            <div className="flex justify-between items-center text-xs">
                                <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                    {reward.custo} XP
                                </span>
                                <span className="text-gray-500">
                                    Estoque: {reward.estoque === -1 ? '∞' : reward.estoque}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {rewards.length === 0 && (
                    <div className="bg-white rounded-lg shadow-sm p-8 text-center">
                        <p className="text-gray-500">Nenhuma recompensa cadastrada ainda.</p>
                        <p className="text-sm text-gray-400 mt-2">Clique em "Nova Recompensa" para começar!</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProfessorShopPage;
