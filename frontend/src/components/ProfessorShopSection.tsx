import React, { useState, useEffect } from 'react';
import { ShoppingBag, Plus, Trash2, X } from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';

interface Reward {
    id: number;
    nome: string;
    descricao: string;
    custo: number;
    estoque: number;
    imagem_url?: string;
    escola_id?: number;
}

interface ProfessorShopModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ProfessorShopModal: React.FC<ProfessorShopModalProps> = ({ isOpen, onClose }) => {
    const { user } = useAuth();
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
        if (isOpen) {
            fetchRewards();
        }
    }, [isOpen]);

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

    const canDelete = user?.papel === 'gestor' || user?.papel === 'admin';

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div
                className="bg-gray-800 rounded-2xl border border-gray-700 w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-700">
                    <h2 className="text-2xl font-bold flex items-center gap-2">
                        <ShoppingBag className="w-6 h-6 text-purple-400" />
                        Lojinha
                    </h2>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setShowCreateForm(!showCreateForm)}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors font-medium"
                        >
                            {showCreateForm ? (
                                <>✕ Cancelar</>
                            ) : (
                                <>
                                    <Plus className="w-4 h-4" />
                                    Nova Recompensa
                                </>
                            )}
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                            title="Fechar"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {/* Create Form */}
                    {showCreateForm && (
                        <div className="bg-gray-700/50 rounded-xl p-4 mb-6 border border-gray-600">
                            <h3 className="text-lg font-semibold mb-4">Criar Nova Recompensa</h3>
                            <form onSubmit={handleCreateReward} className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">
                                            Nome
                                        </label>
                                        <input
                                            type="text"
                                            value={newReward.nome}
                                            onChange={(e) => setNewReward({ ...newReward, nome: e.target.value })}
                                            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white"
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">
                                            Custo (Moedas)
                                        </label>
                                        <input
                                            type="number"
                                            value={newReward.custo}
                                            onChange={(e) => setNewReward({ ...newReward, custo: parseInt(e.target.value) || 0 })}
                                            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white"
                                            required
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Descrição
                                    </label>
                                    <textarea
                                        value={newReward.descricao}
                                        onChange={(e) => setNewReward({ ...newReward, descricao: e.target.value })}
                                        className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white"
                                        rows={2}
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">
                                            Estoque (-1 = infinito)
                                        </label>
                                        <input
                                            type="number"
                                            value={newReward.estoque}
                                            onChange={(e) => setNewReward({ ...newReward, estoque: parseInt(e.target.value) || -1 })}
                                            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-2">
                                            URL da Imagem (opcional)
                                        </label>
                                        <input
                                            type="text"
                                            value={newReward.imagem_url}
                                            onChange={(e) => setNewReward({ ...newReward, imagem_url: e.target.value })}
                                            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white"
                                        />
                                    </div>
                                </div>
                                <button
                                    type="submit"
                                    className="w-full bg-purple-600 hover:bg-purple-500 text-white py-2 rounded-lg transition-colors font-medium"
                                >
                                    Criar Recompensa
                                </button>
                            </form>
                        </div>
                    )}

                    {/* Rewards List */}
                    {loading ? (
                        <p className="text-center text-gray-400 py-8">Carregando recompensas...</p>
                    ) : rewards.length === 0 ? (
                        <div className="text-center py-12 text-gray-400 bg-gray-900/50 rounded-xl border border-gray-700 border-dashed">
                            <p>Nenhuma recompensa cadastrada ainda.</p>
                            <p className="text-sm text-gray-500 mt-2">Clique em "Nova Recompensa" para começar!</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {rewards.map((reward) => (
                                <div
                                    key={reward.id}
                                    className="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:border-purple-500/50 transition-all"
                                >
                                    <div className="flex justify-between items-start mb-3">
                                        <h3 className="font-semibold text-white text-base flex-1">{reward.nome}</h3>
                                        {canDelete && (
                                            <button
                                                onClick={() => handleDeleteReward(reward.id)}
                                                className="ml-2 p-1.5 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded transition-colors"
                                                title="Excluir recompensa"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                    <p className="text-sm text-gray-300 mb-3 line-clamp-2">{reward.descricao}</p>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded font-medium">
                                            {reward.custo} 🪙
                                        </span>
                                        <span className="text-gray-400">
                                            Estoque: {reward.estoque === -1 ? '∞' : reward.estoque}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
