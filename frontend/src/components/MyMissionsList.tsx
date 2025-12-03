import React, { useState } from 'react';
import { QrCode, Trash2, Search, StopCircle } from 'lucide-react';

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
    onCloseMission: (id: number) => void;
}

export const MyMissionsList: React.FC<MyMissionsListProps> = ({
    missions,
    onDelete,
    onOpenQrScanner,
    onCloseMission
}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredMissions = missions.filter(mission =>
        mission.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mission.descricao.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mission.categoria.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-2xl font-bold mb-4">Minhas Missões Ativas</h2>

            {missions.length > 0 && (
                <div className="mb-4 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Buscar por título, descrição ou categoria..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-primary text-white placeholder-gray-400"
                    />
                </div>
            )}

            {missions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                    Nenhuma missão criada ainda. Crie sua primeira missão acima!
                </p>
            ) : filteredMissions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                    Nenhuma missão encontrada com "{searchTerm}"
                </p>
            ) : (
                <div className="space-y-3">
                    {filteredMissions.map((mission) => (
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
                                        onClick={() => onCloseMission(mission.id)}
                                        className="p-2 bg-yellow-600 hover:bg-yellow-500 rounded-lg transition-colors"
                                        title="Encerrar missão (ninguém mais poderá ver)"
                                    >
                                        <StopCircle className="w-5 h-5" />
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
