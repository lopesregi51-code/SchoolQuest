import React from 'react';
import { Link } from 'react-router-dom';

interface CompletedMission {
    id: number;
    missao_titulo: string;
    aluno_nome: string;
    aluno_id: number;
    aluno_serie?: string;
    data_validacao: string;
}

interface CompletedMissionsListProps {
    missions: CompletedMission[];
}

export const CompletedMissionsList: React.FC<CompletedMissionsListProps> = ({ missions }) => {
    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-2xl font-bold mb-4">Missões Concluídas</h2>
            {missions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                    Nenhuma missão concluída ainda.
                </p>
            ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
                    {missions.map((mission) => (
                        <div
                            key={mission.id}
                            className="bg-gray-700/30 p-3 rounded-lg border border-gray-600/50"
                        >
                            <p className="font-semibold text-sm text-green-400">✓ {mission.missao_titulo}</p>
                            <Link
                                to={`/profile/${mission.aluno_id}`}
                                className="text-xs text-primary hover:underline"
                            >
                                {mission.aluno_nome}
                            </Link>
                            <p className="text-xs text-gray-500">
                                Concluída em {new Date(mission.data_validacao).toLocaleString('pt-BR')}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
