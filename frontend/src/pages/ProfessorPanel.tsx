import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Ranking } from '../components/Ranking';
import { ProfessorHeader } from '../components/ProfessorHeader';
import { MissionCreationForm } from '../components/MissionCreationForm';
import { MyMissionsList } from '../components/MyMissionsList';
import { PendingMissionsList } from '../components/PendingMissionsList';
import { CompletedMissionsList } from '../components/CompletedMissionsList';
import { QrCodeScanner } from '../components/QrCodeScanner';
import { ProfessorShopModal } from '../components/ProfessorShopSection';

export const ProfessorPanel: React.FC = () => {
    const { user, logout } = useAuth();
    const [isCreating, setIsCreating] = useState(false);
    const [validatingMissionId, setValidatingMissionId] = useState<number | null>(null);
    const [showShopModal, setShowShopModal] = useState(false);

    const [myMissions, setMyMissions] = useState<any[]>([]);
    const [pendingMissions, setPendingMissions] = useState<any[]>([]);
    const [completedMissions, setCompletedMissions] = useState<any[]>([]);
    const [clans, setClans] = useState<any[]>([]);
    const [turmas, setTurmas] = useState<any[]>([]);
    const [formData, setFormData] = useState({
        titulo: '',
        descricao: '',
        pontos: 10,
        moedas: 5,
        categoria: 'diaria',
        tipo: 'individual',
        clan_id: '',
        turma_id: ''
    });

    useEffect(() => {
        fetchMyMissions();
        fetchPendingMissions();
        fetchCompletedMissions();
        fetchClans();
        fetchTurmas();
    }, []);

    const fetchMyMissions = async () => {
        try {
            const response = await apiClient.get('/missoes/');
            const my = response.data.filter((m: any) => m.criador_id === user?.id);
            setMyMissions(my);
        } catch (error) {
            console.error('Erro ao buscar minhas missões', error);
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

    const fetchClans = async () => {
        try {
            const response = await apiClient.get('/clans/');
            setClans(response.data);
        } catch (error) {
            console.error('Erro ao buscar clãs', error);
        }
    };

    const fetchTurmas = async () => {
        try {
            const response = await apiClient.get('/missoes/turmas');
            if (Array.isArray(response.data)) {
                setTurmas(response.data);
            }
        } catch (error) {
            console.error('Erro ao buscar turmas', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload: any = {
                titulo: formData.titulo,
                descricao: formData.descricao,
                pontos: formData.pontos,
                moedas: formData.moedas,
                categoria: formData.categoria,
                tipo: formData.tipo
            };

            if (formData.tipo === 'clan' && formData.clan_id) {
                payload.clan_id = parseInt(formData.clan_id);
            }

            if (formData.turma_id) {
                payload.turma_id = parseInt(formData.turma_id);
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
                clan_id: '',
                turma_id: ''
            });
            setIsCreating(false);
            fetchMyMissions();
        } catch (error) {
            alert('Erro ao criar missão');
        }
    };

    const handleDeleteMission = async (id: number) => {
        if (!confirm('Tem certeza que deseja excluir esta missão?')) return;
        try {
            await apiClient.request({ method: 'DELETE', url: `/missoes/${id}` });
            alert('Missão excluída!');
            fetchMyMissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao excluir missão');
        }
    };

    const handleApproveMission = async (id: number) => {
        try {
            await apiClient.post(`/missoes/validar/${id}`, null, {
                params: { aprovado: true }
            });
            alert('Missão aprovada!');
            fetchPendingMissions();
            fetchCompletedMissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao aprovar missão');
        }
    };

    const handleRejectMission = async (id: number) => {
        if (!confirm('Tem certeza que deseja rejeitar esta missão?')) return;
        try {
            await apiClient.post(`/missoes/validar/${id}`, null, {
                params: { aprovado: false }
            });
            alert('Missão rejeitada!');
            fetchPendingMissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao rejeitar missão');
        }
    };

    const validateQrCode = async (qrData: string) => {
        if (!validatingMissionId) return;

        try {
            let payload: any = {};

            if (qrData.includes('/qr/')) {
                const parts = qrData.split('/qr/')[1]?.split('/');
                if (parts && parts.length >= 2) {
                    payload = {
                        aluno_id: parseInt(parts[0]),
                        qr_token: parts[1]
                    };
                }
            } else {
                try {
                    const parsed = JSON.parse(qrData);
                    payload = {
                        aluno_id: parsed.user_id || parsed.aluno_id,
                        qr_token: parsed.qr_token || parsed.token
                    };
                } catch {
                    alert('QR Code inválido');
                    return;
                }
            }

            await apiClient.post(`/missoes/${validatingMissionId}/validar_presencial`, payload);
            alert('Missão validada com sucesso!');
            setValidatingMissionId(null);
            fetchPendingMissions();
            fetchCompletedMissions();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao validar missão');
        }
    };

    return (
        <div className="min-h-screen bg-dark text-white p-4 md:p-8">
            <div className="max-w-7xl mx-auto">
                <ProfessorHeader
                    schoolName={user?.escola_nome}
                    onLogout={logout}
                    onOpenShop={() => setShowShopModal(true)}
                />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-6">
                        <MissionCreationForm
                            isCreating={isCreating}
                            formData={formData}
                            clans={clans}
                            turmas={turmas}
                            onToggleCreate={() => setIsCreating(!isCreating)}
                            onFormChange={setFormData}
                            onSubmit={handleSubmit}
                        />

                        <MyMissionsList
                            missions={myMissions}
                            onDelete={handleDeleteMission}
                            onOpenQrScanner={setValidatingMissionId}
                        />

                        <PendingMissionsList
                            missions={pendingMissions}
                            onApprove={handleApproveMission}
                            onReject={handleRejectMission}
                        />

                        <CompletedMissionsList missions={completedMissions} />
                    </div>

                    <div className="lg:col-span-1">
                        <Ranking />
                    </div>
                </div>

                <QrCodeScanner
                    isOpen={validatingMissionId !== null}
                    missionId={validatingMissionId}
                    onClose={() => setValidatingMissionId(null)}
                    onScan={validateQrCode}
                />

                <ProfessorShopModal
                    isOpen={showShopModal}
                    onClose={() => setShowShopModal(false)}
                />
            </div>
        </div>
    );
};
