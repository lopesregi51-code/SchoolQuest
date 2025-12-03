import React, { useState } from 'react';
import { CheckCircle, XCircle, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PendingMission {
    id: number;
    missao_titulo: string;
    aluno_nome: string;
    aluno_id: number;
    aluno_serie?: string;
    data_solicitacao: string;
}

interface PendingMissionsListProps {
    missions: PendingMission[];
    onApprove: (id: number) => void;
    onReject: (id: number) => void;
}

export const PendingMissionsList: React.FC<PendingMissionsListProps> = ({
    missions,
    onApprove,
    onReject
}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredMissions = missions.filter(mission =>
        mission.missao_titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mission.aluno_nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (mission.aluno_serie && mission.aluno_serie.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-2xl font-bold mb-4">Missões Pendentes de Validação</h2>

            {missions.length > 0 && (
                <div className="mb-4 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Buscar por missão, aluno ou sala..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-primary text-white placeholder-gray-400"
                    />
                </div>
            )}

            {missions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                    Nenhuma missão pendente de validação.
                </p>
            ) : filteredMissions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                    Nenhuma missão encontrada com "{searchTerm}"
                </p>
            ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
                    {filteredMissions.map((mission) => (
                        <div
                            key={mission.id}
                            className="bg-gray-700/50 p-3 rounded-lg border border-gray-600 flex justify-between items-center gap-3"
                        >
                            <div className="flex-1 min-w-0">
                                <p className="font-semibold text-sm truncate">{mission.missao_titulo}</p>
                                <Link
                                    to={`/profile/${mission.aluno_id}`}
                                    className="text-xs text-primary hover:underline"
                                >
                                    {mission.aluno_nome}
                                </Link>
                                <p className="text-xs text-gray-400">
                                    {new Date(mission.data_solicitacao).toLocaleString('pt-BR')}
                                </p>
                            </div>
                            <div className="flex gap-1 flex-shrink-0">
                                <button
                                    onClick={() => onApprove(mission.id)}
                                    className="p-1.5 bg-green-600 hover:bg-green-500 rounded text-white"
                                    title="Aprovar"
                                >
                                    <CheckCircle className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => onReject(mission.id)}
                                    className="p-1.5 bg-red-600 hover:bg-red-500 rounded text-white"
                                    title="Rejeitar"
                                >
                                    <XCircle className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
