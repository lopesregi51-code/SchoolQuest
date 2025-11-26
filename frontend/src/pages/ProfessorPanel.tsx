import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { BookOpen, Plus, LogOut, CheckCircle, QrCode, Trash2 } from 'lucide-react';
import apiClient from '../api/client';
import { Ranking } from '../components/Ranking';
import { Html5Qrcode } from 'html5-qrcode';



export const ProfessorPanel: React.FC = () => {
    const { user, logout } = useAuth();
    const [isCreating, setIsCreating] = useState(false);

    const [myMissions, setMyMissions] = useState<any[]>([]);

    const [completedMissions, setCompletedMissions] = useState<any[]>([]);
    const [formData, setFormData] = useState({
        titulo: '',
        descricao: '',
        pontos: 10,
        moedas: 5,
        categoria: 'diaria'
    });
    const html5QrCodeRef = useRef<Html5Qrcode | null>(null);



    const fetchCompletedMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/professor/concluidas');
            setCompletedMissions(response.data);
        } catch (error) {
            console.error('Erro ao buscar missões concluídas', error);
        }
    };

    const handleAssignMission = async (missionId: number) => {
        const email = prompt("Digite o email do aluno para atribuir esta missão:");
        if (!email) return;

        try {
            // First find the user by email (we need an endpoint for this or search)
            // For MVP, let's assume we have a search endpoint or we can try to find locally if we had the list.
            // Since we don't have a direct 'get user by email' for professors easily exposed without search,
            // let's use the search endpoint I noticed in main.py: /users/search?q=...

            const searchRes = await apiClient.get(`/users/search?q=${email}`);
            const students = searchRes.data;
            const student = students.find((s: any) => s.email === email);

            if (!student) {
                alert('Aluno não encontrado com este email.');
                return;
            }

            await apiClient.post('/missoes/atribuir', {
                missao_id: missionId,
                aluno_id: student.id
            });
            alert(`Missão atribuída para ${student.nome}!`);
            alert(`Missão atribuída para ${student.nome}!`);
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao atribuir missão');
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
            await apiClient.post('/missoes/', formData);
            alert('Missão criada com sucesso!');
            setFormData({
                titulo: '',
                descricao: '',
                pontos: 10,
                moedas: 5,
                categoria: 'diaria'
            });
            setIsCreating(false);
            fetchMyMissions(); // Refresh list after creation
        } catch (error) {
            alert('Erro ao criar missão');
        }
    };

    const validateQrCode = async (qrData: string) => {
        try {
            const res = await apiClient.post('/users/validate_qrcode', { qr_data: qrData });
            const student = res.data;
            alert(`Aluno Encontrado:\nNome: ${student.nome}\nSérie: ${student.serie}\nNível: ${student.nivel}\nXP: ${student.xp}`);
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
                    stopQrScanner();

                    // Hide scanner and show manual input
                    const scanner = document.getElementById('qr-scanner');
                    const manualInput = document.getElementById('manual-qr-section');
                    if (scanner && manualInput) {
                        scanner.classList.add('hidden');
                        manualInput.classList.remove('hidden');
                    }
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

    useEffect(() => {

        fetchMyMissions();

        fetchCompletedMissions();

        // Cleanup scanner on unmount
        return () => {
            if (html5QrCodeRef.current?.isScanning) {
                html5QrCodeRef.current.stop().catch(console.error);
            }
        };
    }, []);

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

                                <div className="grid md:grid-cols-3 gap-4">
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
                                </div>

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
                                            <h3 className="font-bold text-lg">{mission.titulo}</h3>
                                            <p className="text-sm text-gray-300">{mission.descricao}</p>
                                            <div className="flex gap-2 mt-1 text-xs">
                                                <span className="text-yellow-400">{mission.pontos} XP</span>
                                                <span className="text-green-400">{mission.moedas} Moedas</span>
                                                <span className="bg-blue-900 px-2 rounded text-blue-200">{mission.categoria}</span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleAssignMission(mission.id)}
                                                className="px-3 py-1 bg-purple-600 hover:bg-purple-500 rounded text-sm transition-colors"
                                                title="Atribuir a Aluno"
                                            >
                                                Atribuir
                                            </button>
                                            <button
                                                onClick={() => handleDeleteMission(mission.id)}
                                                className="p-2 text-red-400 hover:bg-red-900/30 rounded-lg transition-colors"
                                                title="Excluir Missão"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
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

                    {/* QR Scanner / Validation */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-2xl font-bold flex items-center gap-2">
                                <QrCode className="w-6 h-6 text-purple-400" />
                                Validar via QR Code
                            </h2>
                        </div>

                        <div className="space-y-4">
                            {/* Camera Scanner */}
                            <div>
                                <button
                                    onClick={() => {
                                        const scanner = document.getElementById('qr-scanner');
                                        const manualInput = document.getElementById('manual-qr-section');
                                        if (scanner && manualInput) {
                                            const isHidden = scanner.classList.contains('hidden');
                                            if (isHidden) {
                                                scanner.classList.remove('hidden');
                                                manualInput.classList.add('hidden');
                                                startQrScanner();
                                            } else {
                                                scanner.classList.add('hidden');
                                                manualInput.classList.remove('hidden');
                                                stopQrScanner();
                                            }
                                        }
                                    }}
                                    className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-500 text-white font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                                >
                                    <QrCode className="w-5 h-5" />
                                    Escanear com Câmera
                                </button>
                            </div>

                            {/* QR Scanner Container */}
                            <div id="qr-scanner" className="hidden">
                                <div id="qr-reader" className="w-full rounded-lg overflow-hidden"></div>
                                <button
                                    onClick={() => {
                                        const scanner = document.getElementById('qr-scanner');
                                        const manualInput = document.getElementById('manual-qr-section');
                                        if (scanner && manualInput) {
                                            scanner.classList.add('hidden');
                                            manualInput.classList.remove('hidden');
                                            stopQrScanner();
                                        }
                                    }}
                                    className="mt-2 w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
                                >
                                    Fechar Câmera
                                </button>
                            </div>

                            {/* Manual Input */}
                            <div id="manual-qr-section" className="space-y-2">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        placeholder="Ou cole o código do QR aqui (ex: schoolquest:user:1:...)"
                                        className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                        id="qrInput"
                                    />
                                    <button
                                        onClick={async () => {
                                            const input = document.getElementById('qrInput') as HTMLInputElement;
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
                    </div>


                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <Ranking />
                </div>
            </div>
        </div>
    );
};
