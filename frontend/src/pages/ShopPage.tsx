import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import { ShoppingBag, Star } from 'lucide-react';

interface Reward {
    id: number;
    nome: string;
    descricao: string;
    custo: number;
    estoque: number;
    imagem_url?: string;
}

export const ShopPage: React.FC = () => {
    const { user } = useAuth();
    const [rewards, setRewards] = useState<Reward[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchRewards();
    }, []);

    const fetchRewards = async () => {
        try {
            const res = await apiClient.get('/shop/');
            setRewards(res.data);
        } catch (error) {
            console.error("Error fetching rewards", error);
            setError('Erro ao carregar loja');
        } finally {
            setLoading(false);
        }
    };

    const handleBuy = async (item: Reward) => {
        if (!user) return;
        if (user.moedas < item.custo) {
            alert('Moedas insuficientes!');
            return;
        }
        if (!confirm(`Comprar "${item.nome}" por ${item.custo} moedas?`)) return;

        try {
            await apiClient.post(`/shop/buy/${item.id}`);
            alert(`Solicitação de compra enviada! Aguarde a aprovação do gestor.`);
            fetchRewards();
            window.location.reload();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro na compra');
        }
    };

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <div className="max-w-6xl mx-auto">
                <header className="mb-8 flex justify-between items-center bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-purple-900/50 rounded-xl">
                            <ShoppingBag className="w-8 h-8 text-purple-400" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">Lojinha da Escola</h1>
                            <p className="text-gray-400">Troque suas moedas por recompensas incríveis!</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-sm text-gray-400">Seu Saldo</p>
                            <p className="text-2xl font-bold text-yellow-400 flex items-center justify-end gap-2">
                                {user?.moedas} <span className="text-sm text-gray-500">Moedas</span>
                            </p>
                        </div>
                    </div>
                </header>

                {loading ? (
                    <div className="text-center py-12">Carregando loja...</div>
                ) : error ? (
                    <div className="text-center py-12 text-red-400">{error}</div>
                ) : rewards.length === 0 ? (
                    <div className="text-center py-12 text-gray-400 bg-gray-800 rounded-xl border border-gray-700 border-dashed">
                        <ShoppingBag className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>A loja está vazia no momento.</p>
                        <p className="text-sm">Volte mais tarde para ver novas recompensas!</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {rewards.map(item => (
                            <div key={item.id} className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col transition-transform hover:-translate-y-1 hover:shadow-xl hover:shadow-purple-900/20 group">
                                <div className="h-48 bg-gray-700 flex items-center justify-center relative overflow-hidden">
                                    {item.imagem_url ? (
                                        <img src={item.imagem_url} alt={item.nome} className="w-full h-full object-cover transition-transform group-hover:scale-110" />
                                    ) : (
                                        <Star className="w-16 h-16 text-gray-600" />
                                    )}
                                    {item.estoque <= 0 && (
                                        <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
                                            <span className="px-4 py-2 bg-red-600 text-white font-bold rounded-lg transform -rotate-12 border-2 border-white">
                                                ESGOTADO
                                            </span>
                                        </div>
                                    )}
                                </div>

                                <div className="p-6 flex-1 flex flex-col">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="text-xl font-bold">{item.nome}</h3>
                                        <span className="px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                                            Restam: {item.estoque}
                                        </span>
                                    </div>

                                    <p className="text-gray-400 text-sm mb-6 flex-1">{item.descricao}</p>

                                    <div className="flex items-center justify-between mt-auto pt-4 border-t border-gray-700">
                                        <span className="text-2xl font-bold text-yellow-400 flex items-center gap-1">
                                            {item.custo} <span className="text-xs text-gray-500 font-normal">Moedas</span>
                                        </span>

                                        <button
                                            onClick={() => handleBuy(item)}
                                            disabled={item.estoque <= 0 || (user?.moedas || 0) < item.custo}
                                            className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2
                                                ${item.estoque <= 0
                                                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                                    : (user?.moedas || 0) < item.custo
                                                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed opacity-50'
                                                        : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-900/50'
                                                }`}
                                        >
                                            {item.estoque <= 0 ? 'Esgotado' : 'Comprar'}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
