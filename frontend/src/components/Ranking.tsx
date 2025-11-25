import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { Trophy, Medal, X } from 'lucide-react';
import { Link } from 'react-router-dom';

interface User {
    id: number;
    nome: string;
    xp: number;
    nivel: number;
    serie?: string;
}

export const Ranking: React.FC = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showAll, setShowAll] = useState(false);
    const [allUsers, setAllUsers] = useState<User[]>([]);

    useEffect(() => {
        fetchRanking();
    }, []);

    const fetchRanking = async () => {
        try {
            const response = await apiClient.get('/ranking');
            setUsers(response.data);
        } catch (error) {
            console.error('Erro ao buscar ranking', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchAllRanking = async () => {
        try {
            const response = await apiClient.get('/ranking?limit=100');
            setAllUsers(response.data);
        } catch (error) {
            console.error('Erro ao buscar ranking completo', error);
        }
    };

    const handleShowAll = () => {
        setShowAll(true);
        if (allUsers.length === 0) {
            fetchAllRanking();
        }
    };

    const getMedalColor = (index: number) => {
        switch (index) {
            case 0: return 'text-yellow-400';
            case 1: return 'text-gray-300';
            case 2: return 'text-amber-600';
            default: return 'text-gray-500';
        }
    };

    return (
        <>
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <div className="p-6 border-b border-gray-700 flex items-center justify-between">
                    <div className="flex items-center">
                        <Trophy className="w-6 h-6 text-yellow-400 mr-2" />
                        <h2 className="text-xl font-bold text-white">Top 10 Aventureiros</h2>
                    </div>
                    <button
                        onClick={handleShowAll}
                        className="text-sm text-primary hover:text-blue-400 underline"
                    >
                        Ver Todos
                    </button>
                </div>

                {isLoading ? (
                    <div className="p-8 text-center text-gray-400">Carregando ranking...</div>
                ) : (
                    <div className="divide-y divide-gray-700">
                        {users.map((user, index) => (
                            <div key={index} className="p-4 flex items-center hover:bg-gray-700/50 transition-colors">
                                <div className={`w-8 h-8 flex items-center justify-center font-bold text-lg mr-4 ${getMedalColor(index)}`}>
                                    {index < 3 ? <Medal className="w-6 h-6" /> : `#${index + 1}`}
                                </div>

                                <div className="flex-1">
                                    <Link to={user.id ? `/profile/${user.id}` : '#'} className={`font-bold text-white hover:text-blue-400 hover:underline ${!user.id ? 'pointer-events-none text-gray-400' : ''}`}>
                                        {user.nome}
                                    </Link>
                                    <p className="text-xs text-gray-400">Nível {user.nivel} • {user.serie}</p>
                                </div>

                                <div className="text-right">
                                    <span className="block font-bold text-yellow-400">{user.xp} XP</span>
                                </div>
                            </div>
                        ))}

                        {users.length === 0 && (
                            <div className="p-8 text-center text-gray-400">Nenhum aventureiro pontuou ainda.</div>
                        )}
                    </div>
                )}
            </div>

            {/* Modal Full Ranking */}
            {showAll && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-gray-700">
                        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <Trophy className="w-6 h-6 text-yellow-400" />
                                Ranking Geral
                            </h2>
                            <button onClick={() => setShowAll(false)} className="text-gray-400 hover:text-white">
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="overflow-y-auto p-6">
                            <table className="w-full text-left">
                                <thead className="text-gray-400 text-sm border-b border-gray-700">
                                    <tr>
                                        <th className="pb-3 pl-4">Posição</th>
                                        <th className="pb-3">Aventureiro</th>
                                        <th className="pb-3 text-right pr-4">XP Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-700">
                                    {allUsers.map((user, index) => (
                                        <tr key={index} className="hover:bg-gray-700/30">
                                            <td className="py-3 pl-4 font-bold text-gray-400">#{index + 1}</td>
                                            <td className="py-3">
                                                <Link to={user.id ? `/profile/${user.id}` : '#'} className={`font-bold hover:text-blue-400 hover:underline ${!user.id ? 'pointer-events-none text-gray-400' : ''}`}>
                                                    {user.nome}
                                                </Link>
                                                <div className="text-xs text-gray-500">{user.serie} • Nível {user.nivel}</div>
                                            </td>
                                            <td className="py-3 text-right pr-4 font-bold text-yellow-400">{user.xp}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
