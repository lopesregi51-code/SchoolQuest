import React from 'react';
import { QrCode, Trash2 } from 'lucide-react';

interface Mission {
    id: number;
    titulo: string;
    descricao: string;
    pontos: number;
    moedas: number;
    categoria: string;
}

interface MyMissionsListProps {
    missions: Mission[];
    onDelete: (id: number) => void;
    onOpenQrScanner: (id: number) => void;
}

export const MyMissionsList: React.FC<MyMissionsListProps> = ({
    missions,
    onDelete,
    onOpenQrScanner
}) => {
    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-2xl font-bold mb-4">Minhas Missões Ativas</h2>
            {missions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                    Nenhuma missão criada ainda. Crie sua primeira missão acima!
                </p>
            ) : (
                <div className="space-y-3">
                    {missions.map((mission) => (
                        <div
                            key={mission.id}
                            className="bg-gray-700/50 p-4 rounded-lg border border-gray-600 hover:border-primary transition-colors"
                        >
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    <h3 className="font-bold text-lg">{mission.titulo}</h3>
                                    <p className="text-gray-400 text-sm mt-1">{mission.descricao}</p>
                                    <div className="flex gap-3 mt-2 text-sm">
                                        <span className="text-yellow-400">⭐ {mission.pontos} XP</span>
                                        <span className="text-green-400">💰 {mission.moedas} moedas</span>
                                        <span className="text-blue-400 capitalize">{mission.categoria}</span>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => onOpenQrScanner(mission.id)}
                                        className="p-2 bg-primary hover:bg-blue-600 rounded-lg transition-colors"
                                        title="Validar com QR Code"
                                    >
                                        <QrCode className="w-5 h-5" />
                                    </button>
                                    <button
                                        onClick={() => onDelete(mission.id)}
                                        className="p-2 bg-red-600 hover:bg-red-500 rounded-lg transition-colors"
                                        title="Excluir missão"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
