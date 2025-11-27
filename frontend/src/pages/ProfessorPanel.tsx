import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Plus, LogOut, CheckCircle, QrCode, Trash2 } from 'lucide-react';
import apiClient from '../api/client';
import { Ranking } from '../components/Ranking';
import { Html5Qrcode } from 'html5-qrcode';



export const ProfessorPanel: React.FC = () => {
    const { user, logout } = useAuth();
    const [isCreating, setIsCreating] = useState(false);
    const [validatingMissionId, setValidatingMissionId] = useState<number | null>(null);

    const [myMissions, setMyMissions] = useState<any[]>([]);
    const [pendingMissions, setPendingMissions] = useState<any[]>([]);
    const [completedMissions, setCompletedMissions] = useState<any[]>([]);
    const [clans, setClans] = useState<any[]>([]);
    const [formData, setFormData] = useState({
        titulo: '',
        descricao: '',
        pontos: 10,
        moedas: 5,
        categoria: 'diaria',
        tipo: 'individual',
        clan_id: ''
    });
    const html5QrCodeRef = useRef<Html5Qrcode | null>(null);

    useEffect(() => {
        fetchMyMissions();
        fetchPendingMissions();
        fetchCompletedMissions();
        fetchClans();

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

    const fetchPendingMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/pendentes');
            setPendingMissions(response.data);
        } catch (error) {
            console.error('Erro ao buscar missões pendentes', error);
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
            } else {
                delete payload.clan_id;
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
                clan_id: ''
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

            // Check for new token format: schoolquest:token:{token}
            if (qrData.startsWith('schoolquest:token:')) {
                const token = qrData.split(':')[2];
                payload = { qr_token: token };
            }
            // Check for old format: schoolquest:user:{id}:{email}
            else if (qrData.startsWith('schoolquest:user:')) {
                const parts = qrData.split(':');
                const userId = parseInt(parts[2]);
                if (!isNaN(userId)) {
                    payload = { aluno_id: userId };
                }
            } else {
                // Try as raw token if it's a UUID-like string? 
                // Or just assume it's invalid if not prefixed
                alert('Formato de QR Code inválido');
                return;
            }

            if (!payload.aluno_id && !payload.qr_token) {
                alert('Dados do QR Code inválidos');
                return;
            }

            const res = await apiClient.post(`/missoes/${validatingMissionId}/validar_presencial`, payload);

            alert(res.data.message);

            // Close scanner if successful
            setValidatingMissionId(null);
            stopQrScanner();
            fetchCompletedMissions();

        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao validar QR Code');
        }
    };

    const startQrScanner = async () => {
        try {
            if (!html5QrCodeRef.current) {
                html5QrCodeRef.current = new Html5Qrcode("qr-reader");
            }

            await html5QrCodeRef.current.start(
                { facingMode: "environment" },
                {
                    fps: 10,
                    qrbox: { width: 250, height: 250 }
                },
                (decodedText) => {
                    // QR Code detected
                    validateQrCode(decodedText);
                    // Don't stop immediately to allow continuous scanning? No, usually one by one.
                    // stopQrScanner(); // Moved to success callback
                },
                (_) => {
                    // Ignore scanning errors (they happen continuously)
                }
            );
        } catch (err) {
            console.error('Error starting QR scanner:', err);
            alert('Erro ao iniciar câmera. Verifique as permissões.');
        }
    };

    const stopQrScanner = async () => {
        try {
            if (html5QrCodeRef.current?.isScanning) {
                await html5QrCodeRef.current.stop();
            }
        } catch (err) {
            console.error('Error stopping QR scanner:', err);
        }
    };

    if (!user) return null;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            {/* Header */}
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Painel do Professor</h1>
                    <p className="text-gray-400">Gerencie missões e alunos{user?.escola_nome ? ` • ${user.escola_nome}` : ''}</p>
                </div>
                <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                    <LogOut className="w-4 h-4" />
                    Sair
                </button>
            </header>

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
                                    <label className="block text-gray-300 text-sm font-medium mb-2">
                                        Título
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.titulo}
                                        onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Ex: Resolver 10 exercícios de Matemática"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="block text-gray-300 text-sm font-medium mb-2">
                                        Descrição
                                    </label>
                                    <textarea
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
                                                    setTimeout(() => startQrScanner(), 100); // Wait for modal to render
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
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <CheckCircle className="w-6 h-6 text-yellow-400" />
                                Missões Pendentes de Validação
                            </h2>
                        </div>
                        {pendingMissions.length === 0 ? (
                            <p className="text-gray-400">Nenhuma missão pendente de validação.</p>
                        ) : (
                            <div className="space-y-3">
                                {pendingMissions.map((pending) => (
                                    <div key={pending.id} className="bg-gray-700 p-4 rounded-lg border border-yellow-600/30">
                                        <div className="flex justify-between items-start">
                                            <div className="flex-1">
                                                <h3 className="font-bold text-lg">{pending.missao_titulo}</h3>
                                                <p className="text-sm text-gray-300">
                                                    Aluno: {pending.aluno_nome} ({pending.aluno_serie})
                                                </p>
                                                <p className="text-xs text-gray-400">
                                                    Enviada em: {new Date(pending.data_solicitacao).toLocaleDateString()}
                                                </p>
                                            </div>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => handleValidateMission(pending.id, true)}
                                                    className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg font-bold text-sm transition-colors"
                                                >
                                                    Aprovar
                                                </button>
                                                <button
                                                    onClick={() => handleValidateMission(pending.id, false)}
                                                    className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg font-bold text-sm transition-colors"
                                                >
                                                    Rejeitar
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
                            <div className="space-y-3">
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
                                stopQrScanner();
                            }}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white"
                        >
                            <Trash2 className="w-6 h-6 rotate-45" />
                        </button>

                        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                            <QrCode className="w-6 h-6 text-purple-400" />
                            Validar Missão
                        </h2>

                        <p className="text-gray-300 mb-4">
                            Escaneie o QR Code do aluno para validar a missão automaticamente.
                        </p>

                        <div id="qr-reader" className="w-full rounded-lg overflow-hidden bg-black mb-4 min-h-[250px]"></div>

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
        </div>
    );
};
