import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Users, Upload, Trash2, Plus, Shield, ShoppingBag, Edit, X, Save, Image } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface User {
    id: number;
    nome: string;
    email: string;
    papel: string;
    nivel: number;
    serie_id?: number;
    serie_nome?: string;
    disciplina?: string;
}

interface ReportStats {
    total_alunos: number;
    total_missoes: number;
    media_xp: number;
    top_alunos: { nome: string; xp: number; nivel: number }[];
}

interface Reward {
    id: number;
    nome: string;
    descricao: string;
    custo: number;
    estoque: number;
    imagem_url?: string;
}

interface Serie {
    id: number;
    nome: string;
    escola_id: number;
    criado_em: string;
}

export const ManagerPanel: React.FC = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [file, setFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [error, setError] = useState('');
    const [newUser, setNewUser] = useState({ nome: '', email: '', senha: '', papel: 'aluno', serie_id: '', disciplina: '' });
    const [isResetting, setIsResetting] = useState(false);

    // Search and Filter State
    const [searchTerm, setSearchTerm] = useState('');
    const [filterRole, setFilterRole] = useState('todos');
    const [reports, setReports] = useState<ReportStats | null>(null);
    const [topProfessors, setTopProfessors] = useState<any[]>([]);
    const [participationStats, setParticipationStats] = useState<any[]>([]);

    // Shop State
    const [rewards, setRewards] = useState<Reward[]>([]);
    const [newReward, setNewReward] = useState({ nome: '', descricao: '', custo: 0, estoque: 1, imagem_url: '' });
    const [showShopManager, setShowShopManager] = useState(false);

    // Series State
    const [series, setSeries] = useState<Serie[]>([]);
    const [newSerie, setNewSerie] = useState({ nome: '' });
    const [showSeriesManager, setShowSeriesManager] = useState(false);

    // User Edit State
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [showEditUserModal, setShowEditUserModal] = useState(false);
    const [editFormData, setEditFormData] = useState<Partial<User> & { senha?: string }>({});

    useEffect(() => {
        fetchUsers();
        fetchExtraStats();
        fetchRewards();
        fetchSeries();
    }, []);

    const fetchRewards = async () => {
        try {
            const res = await apiClient.get('/shop/');
            setRewards(res.data);
        } catch (error) {
            console.error("Error fetching rewards", error);
        }
    };

    const fetchSeries = async () => {
        try {
            const res = await apiClient.get('/series/');
            setSeries(res.data);
        } catch (error) {
            console.error("Error fetching series", error);
        }
    };

    const handleCreateSerie = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await apiClient.post('/series/', newSerie);
            alert('Série criada com sucesso!');
            setNewSerie({ nome: '' });
            fetchSeries();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao criar série');
        }
    };

    const handleUpdateSerie = async (serie: Serie) => {
        const novoNome = prompt('Novo nome da série:', serie.nome);
        if (!novoNome || novoNome === serie.nome) return;

        try {
            await apiClient.put(`/series/${serie.id}`, { nome: novoNome });
            alert('Série atualizada!');
            fetchSeries();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao atualizar série');
        }
    };

    const handleDeleteSerie = async (id: number) => {
        if (!confirm('Tem certeza que deseja excluir esta série?')) return;

        try {
            await apiClient.delete(`/series/${id}`);
            alert('Série excluída!');
            fetchSeries();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao excluir série');
        }
    };

    const fetchExtraStats = async () => {
        try {
            const [profRes, partRes] = await Promise.all([
                apiClient.get('/reports/top_professors'),
                apiClient.get('/reports/participation')
            ]);
            setTopProfessors(profRes.data);
            setParticipationStats(partRes.data);
        } catch (error) {
            console.error("Error fetching extra stats", error);
        }
    };

    const fetchUsers = async () => {
        try {
            const [usersRes, reportsRes] = await Promise.all([
                apiClient.get('/users/'),
                apiClient.get('/reports/stats')
            ]);
            setUsers(usersRes.data);
            setReports(reportsRes.data);
        } catch (error: any) {
            console.error('Erro ao buscar dados', error);
            setError(error.message || 'Erro ao buscar dados');
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const [uploadErrors, setUploadErrors] = useState<string[]>([]);

    const handleUpload = async () => {
        if (!file) return;

        try {
            setUploadStatus('Enviando...');
            setUploadErrors([]);
            const formData = new FormData();
            formData.append('file', file);

            const response = await apiClient.post('/users/import', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            const { imported, errors } = response.data;

            if (errors && errors.length > 0) {
                setUploadStatus(`${imported} usuários importados. ${errors.length} erros encontrados:`);
                setUploadErrors(errors);
            } else {
                setUploadStatus(`${imported} usuários importados com sucesso!`);
            }

            fetchUsers();
            setFile(null);
        } catch (error: any) {
            setUploadStatus('Erro ao importar usuários');
            if (error.response?.data?.detail) {
                setUploadErrors([error.response.data.detail]);
            }
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Prepare user data, only include serie_id for students
            const userData: any = {
                nome: newUser.nome,
                email: newUser.email,
                senha: newUser.senha,
                papel: newUser.papel,
                disciplina: newUser.disciplina || undefined
            };

            // Only include serie_id if it's a student and a serie is selected
            if (newUser.papel === 'aluno' && newUser.serie_id) {
                userData.serie_id = parseInt(newUser.serie_id);
            }

            await apiClient.post('/users/', userData);
            alert('Usuário criado com sucesso!');
            setNewUser({ nome: '', email: '', senha: '', papel: 'aluno', serie_id: '', disciplina: '' });
            fetchUsers();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao criar usuário');
        }
    };

    const handleResetSystem = async () => {
        if (!confirm('ATENÇÃO: Esta ação irá apagar TODOS os alunos. Tem certeza?')) {
            return;
        }

        try {
            setIsResetting(true);
            const response = await apiClient.delete('/users/all');
            alert(`${response.data.deleted} usuários deletados com sucesso!`);
            fetchUsers();
        } catch (error: any) {
            console.error('Erro ao resetar sistema', error);
            alert(`Erro: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsResetting(false);
        }
    };

    const handleCreateReward = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await apiClient.post('/shop/items', newReward);
            alert('Recompensa criada!');
            setNewReward({ nome: '', descricao: '', custo: 0, estoque: 1, imagem_url: '' });
            fetchRewards();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao criar recompensa');
        }
    };

    const handleDeleteReward = async (id: number) => {
        if (!confirm('Deletar recompensa?')) return;
        try {
            await apiClient.delete(`/shop/items/${id}`);
            fetchRewards();
        } catch (error) {
            alert('Erro ao deletar');
        }
    };

    const openEditUser = (user: User) => {
        setEditingUser(user);
        setEditFormData({ ...user });
        setShowEditUserModal(true);
    };

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingUser) return;
        try {
            await apiClient.put(`/users/${editingUser.id}`, editFormData);
            alert('Usuário atualizado!');
            setShowEditUserModal(false);
            fetchUsers();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao atualizar usuário');
        }
    };

    const handleDeleteUser = async () => {
        if (!editingUser) return;
        if (!confirm(`Tem certeza que deseja excluir o usuário ${editingUser.nome}?`)) return;

        try {
            await apiClient.delete(`/users/${editingUser.id}`);
            alert('Usuário excluído com sucesso!');
            setShowEditUserModal(false);
            fetchUsers();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao excluir usuário');
        }
    };

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <header className="flex justify-between items-center mb-8 bg-gray-800 p-4 rounded-xl border border-gray-700">
                <div className="flex items-center">
                    <Shield className="w-8 h-8 text-primary mr-3" />
                    <div>
                        <h1 className="text-2xl font-bold">Painel do Gestor</h1>
                        <p className="text-gray-400">Bem-vindo, {user?.nome}{user?.escola_nome ? ` • ${user.escola_nome}` : ''}</p>
                    </div>
                </div>
            </header>

            {/* Actions Bar */}
            <div className="flex gap-4 mb-8">
                <button
                    onClick={() => navigate('/mural')}
                    className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg font-bold transition-colors"
                >
                    <Image className="w-5 h-5" />
                    Mural
                </button>
                <button
                    onClick={() => setShowShopManager(!showShopManager)}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg font-bold transition-colors"
                >
                    <ShoppingBag className="w-5 h-5" />
                    Gerenciar Loja
                </button>
                <button
                    onClick={() => setShowSeriesManager(!showSeriesManager)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold transition-colors"
                >
                    <Users className="w-5 h-5" />
                    Gerenciar Séries
                </button>
            </div>

            {/* Shop Manager Section */}
            {showShopManager && (
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 mb-8 animate-fade-in">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <ShoppingBag className="w-6 h-6 text-purple-400" />
                        Gerenciar Recompensas
                    </h2>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Form */}
                        <div className="bg-gray-700/50 p-4 rounded-lg h-fit">
                            <h3 className="font-bold mb-3">Nova Recompensa</h3>
                            <form onSubmit={handleCreateReward} className="space-y-3">
                                <input
                                    type="text"
                                    placeholder="Nome do Item"
                                    value={newReward.nome}
                                    onChange={e => setNewReward({ ...newReward, nome: e.target.value })}
                                    className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    required
                                />
                                <textarea
                                    placeholder="Descrição"
                                    value={newReward.descricao}
                                    onChange={e => setNewReward({ ...newReward, descricao: e.target.value })}
                                    className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    required
                                />
                                <div className="grid grid-cols-2 gap-2">
                                    <input
                                        type="number"
                                        placeholder="Custo (Moedas)"
                                        value={newReward.custo}
                                        onChange={e => setNewReward({ ...newReward, custo: parseInt(e.target.value) })}
                                        className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                        required
                                    />
                                    <input
                                        type="number"
                                        placeholder="Estoque"
                                        value={newReward.estoque}
                                        onChange={e => setNewReward({ ...newReward, estoque: parseInt(e.target.value) })}
                                        className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                        required
                                    />
                                </div>
                                <div>
                                    <input
                                        type="text"
                                        placeholder="URL da Imagem (Opcional)"
                                        value={newReward.imagem_url || ''}
                                        onChange={e => setNewReward({ ...newReward, imagem_url: e.target.value })}
                                        className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    />
                                </div>
                                <button type="submit" className="w-full bg-green-600 hover:bg-green-500 py-2 rounded font-bold">
                                    Adicionar Item
                                </button>
                            </form>
                        </div>

                        {/* List */}
                        <div className="md:col-span-2 grid sm:grid-cols-2 gap-4">
                            {rewards.map(item => (
                                <div key={item.id} className="bg-gray-700 p-3 rounded-lg flex justify-between items-start border border-gray-600">
                                    <div>
                                        <h4 className="font-bold">{item.nome}</h4>
                                        <p className="text-xs text-gray-400 mb-1">{item.descricao}</p>
                                        <div className="flex gap-2 text-xs font-mono">
                                            <span className="text-yellow-400">{item.custo} Moedas</span>
                                            <span className="text-blue-300">Estoque: {item.estoque}</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteReward(item.id)}
                                        className="text-red-400 hover:text-red-300 p-1"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Series Manager Section */}
            {showSeriesManager && (
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 mb-8 animate-fade-in">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Users className="w-6 h-6 text-blue-400" />
                        Gerenciar Séries
                    </h2>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Form */}
                        <div className="bg-gray-700/50 p-4 rounded-lg h-fit">
                            <h3 className="font-bold mb-3">Nova Série</h3>
                            <form onSubmit={handleCreateSerie} className="space-y-3">
                                <input
                                    type="text"
                                    placeholder="Nome da Série (ex: 5º Ano A)"
                                    value={newSerie.nome}
                                    onChange={e => setNewSerie({ nome: e.target.value })}
                                    className="w-full bg-gray-600 border border-gray-500 rounded p-2 text-white"
                                    required
                                />
                                <button type="submit" className="w-full bg-green-600 hover:bg-green-500 py-2 rounded font-bold">
                                    Adicionar Série
                                </button>
                            </form>
                        </div>

                        {/* List */}
                        <div className="md:col-span-2 grid sm:grid-cols-2 gap-4">
                            {series.map(serie => (
                                <div key={serie.id} className="bg-gray-700 p-3 rounded-lg flex justify-between items-center border border-gray-600">
                                    <div>
                                        <h4 className="font-bold">{serie.nome}</h4>
                                        <p className="text-xs text-gray-400">ID: {serie.id}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleUpdateSerie(serie)}
                                            className="text-blue-400 hover:text-blue-300 p-1"
                                            title="Editar"
                                        >
                                            <Edit className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteSerie(serie.id)}
                                            className="text-red-400 hover:text-red-300 p-1"
                                            title="Excluir"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Relatórios */}
            {reports && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 text-center">
                        <h3 className="text-gray-400 text-sm mb-2">Total de Alunos</h3>
                        <p className="text-4xl font-bold text-blue-400">{reports.total_alunos}</p>
                    </div>
                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 text-center">
                        <h3 className="text-gray-400 text-sm mb-2">Missões Criadas</h3>
                        <p className="text-4xl font-bold text-purple-400">{reports.total_missoes}</p>
                    </div>
                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 text-center">
                        <h3 className="text-gray-400 text-sm mb-2">Média de XP</h3>
                        <p className="text-4xl font-bold text-yellow-400">{reports.media_xp}</p>
                    </div>
                </div>
            )}

            <div className="grid md:grid-cols-2 gap-6 mb-8">
                {/* Top Alunos */}
                {reports && reports.top_alunos.length > 0 && (
                    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                        <h2 className="text-xl font-bold mb-4 flex items-center">
                            <span className="mr-2">🏆</span> Top 3 Alunos
                        </h2>
                        <div className="space-y-3">
                            {reports.top_alunos.map((aluno, index) => (
                                <div key={index} className="bg-gray-700/50 p-3 rounded-lg flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold
                                            ${index === 0 ? 'bg-yellow-500 text-black' :
                                                index === 1 ? 'bg-gray-400 text-black' :
                                                    'bg-orange-700 text-white'}`}>
                                            #{index + 1}
                                        </div>
                                        <div>
                                            <p className="font-bold">{aluno.nome}</p>
                                            <p className="text-xs text-gray-400">Nível {aluno.nivel}</p>
                                        </div>
                                    </div>
                                    <span className="text-blue-400 font-bold">{aluno.xp} XP</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Top Professores */}
                {topProfessors.length > 0 && (
                    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                        <h2 className="text-xl font-bold mb-4 flex items-center">
                            <span className="mr-2">👨‍🏫</span> Top Professores
                        </h2>
                        <div className="space-y-3">
                            {topProfessors.map((prof, index) => (
                                <div key={index} className="bg-gray-700/50 p-3 rounded-lg flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-blue-900 flex items-center justify-center font-bold text-blue-200">
                                            {index + 1}
                                        </div>
                                        <p className="font-bold">{prof.nome}</p>
                                    </div>
                                    <span className="text-green-400 font-bold">{prof.missoes_concluidas} Missões</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Participation Stats */}
            {participationStats.length > 0 && (
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-8">
                    <h2 className="text-xl font-bold mb-4 flex items-center">
                        <span className="mr-2">📊</span> Engajamento por Série (Média XP)
                    </h2>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {participationStats.map((stat, index) => (
                            <div key={index} className="bg-gray-700/50 p-4 rounded-lg text-center">
                                <h3 className="font-bold text-lg mb-1">{stat.serie}</h3>
                                <p className="text-2xl font-bold text-yellow-400">{stat.media_xp}</p>
                                <p className="text-xs text-gray-400">XP Médio</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid md:grid-cols-2 gap-6 mb-8">
                {/* Importar CSV */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <div className="flex items-center mb-4">
                        <Upload className="w-6 h-6 text-blue-400 mr-2" />
                        <h2 className="text-xl font-bold">Importar Usuários (CSV)</h2>
                    </div>
                    <p className="text-sm text-gray-400 mb-4">Formato: nome,email,senha,papel,serie,disciplina</p>
                    <div className="flex gap-2">
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileChange}
                            className="block w-full text-sm text-gray-400
                                file:mr-4 file:py-2 file:px-4
                                file:rounded-full file:border-0
                                file:text-sm file:font-semibold
                                file:bg-blue-50 file:text-blue-700
                                hover:file:bg-blue-100"
                        />
                        <button
                            onClick={handleUpload}
                            disabled={!file}
                            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg disabled:opacity-50"
                        >
                            Importar
                        </button>
                    </div>
                    {uploadStatus && (
                        <div className={`mt-2 text-sm ${uploadErrors.length > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                            <p className="font-bold">{uploadStatus}</p>
                            {uploadErrors.length > 0 && (
                                <div className="mt-2 max-h-32 overflow-y-auto bg-black/30 p-2 rounded border border-yellow-500/30">
                                    <ul className="list-disc list-inside space-y-1">
                                        {uploadErrors.map((err, idx) => (
                                            <li key={idx} className="text-xs text-red-300">{err}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Criar Usuário Manualmente */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <div className="flex items-center mb-4">
                        <Plus className="w-6 h-6 text-green-400 mr-2" />
                        <h2 className="text-xl font-bold">Novo Usuário</h2>
                    </div>
                    <form onSubmit={handleCreateUser} className="space-y-3">
                        <input
                            type="text"
                            placeholder="Nome"
                            value={newUser.nome}
                            onChange={e => setNewUser({ ...newUser, nome: e.target.value })}
                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            required
                        />
                        <input
                            type="email"
                            placeholder="Email"
                            value={newUser.email}
                            onChange={e => setNewUser({ ...newUser, email: e.target.value })}
                            className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            required
                        />
                        <div className="flex gap-2">
                            <input
                                type="password"
                                placeholder="Senha"
                                value={newUser.senha}
                                onChange={e => setNewUser({ ...newUser, senha: e.target.value })}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                required
                            />
                            <select
                                value={newUser.papel}
                                onChange={e => setNewUser({ ...newUser, papel: e.target.value })}
                                className="bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            >
                                <option value="aluno">Aluno</option>
                                <option value="professor">Professor</option>
                                <option value="gestor">Gestor</option>
                            </select>
                        </div>
                        {newUser.papel === 'aluno' && (
                            <select
                                value={newUser.serie_id}
                                onChange={e => setNewUser({ ...newUser, serie_id: e.target.value })}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            >
                                <option value="">Selecione a Série</option>
                                {series.map(s => (
                                    <option key={s.id} value={s.id}>{s.nome}</option>
                                ))}
                            </select>
                        )}
                        {newUser.papel === 'professor' && (
                            <input
                                type="text"
                                placeholder="Disciplina (ex: Matemática)"
                                value={newUser.disciplina}
                                onChange={e => setNewUser({ ...newUser, disciplina: e.target.value })}
                                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                            />
                        )}
                        <button type="submit" className="w-full bg-green-600 hover:bg-green-700 py-2 rounded-lg">
                            Criar Usuário
                        </button>
                    </form>
                </div>
            </div>

            {/* Lista de Usuários */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden mb-8">
                <div className="p-6 border-b border-gray-700">
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center">
                            <Users className="w-6 h-6 text-purple-400 mr-2" />
                            <h2 className="text-xl font-bold">Usuários Cadastrados</h2>
                        </div>
                        <span className="text-gray-400 text-sm">
                            {users.filter(u => {
                                const matchesSearch = u.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                    u.email.toLowerCase().includes(searchTerm.toLowerCase());
                                const matchesRole = filterRole === 'todos' || u.papel === filterRole;
                                return matchesSearch && matchesRole;
                            }).length} usuários
                        </span>
                    </div>

                    {/* Busca e Filtros */}
                    <div className="flex gap-4">
                        <input
                            type="text"
                            placeholder="Buscar por nome ou email..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
                        />
                        <select
                            value={filterRole}
                            onChange={e => setFilterRole(e.target.value)}
                            className="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-purple-500"
                        >
                            <option value="todos">Todos os papéis</option>
                            <option value="aluno">Alunos</option>
                            <option value="professor">Professores</option>
                            <option value="gestor">Gestores</option>
                        </select>
                    </div>
                </div>

                {error && (
                    <div className="p-4 bg-red-900/50 text-red-200 border-b border-red-800">
                        {error}
                    </div>
                )}

                {isLoading ? (
                    <div className="p-8 text-center text-gray-400">Carregando usuários...</div>
                ) : (
                    <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-900/50 text-gray-400 uppercase text-xs">
                                <tr>
                                    <th className="p-4">Nome</th>
                                    <th className="p-4">Email</th>
                                    <th className="p-4">Papel</th>
                                    <th className="p-4">Série</th>
                                    <th className="p-4">Nível</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {users
                                    .filter(u => {
                                        const matchesSearch = u.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                            u.email.toLowerCase().includes(searchTerm.toLowerCase());
                                        const matchesRole = filterRole === 'todos' || u.papel === filterRole;
                                        return matchesSearch && matchesRole;
                                    })
                                    .map(u => (
                                        <tr key={u.id} className="hover:bg-gray-700/50">
                                            <td className="p-4 font-medium">{u.nome}</td>
                                            <td className="p-4 text-gray-400">{u.email}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded text-xs font-bold
                                                ${u.papel === 'gestor' ? 'bg-red-900 text-red-200' :
                                                        u.papel === 'professor' ? 'bg-blue-900 text-blue-200' :
                                                            'bg-green-900 text-green-200'}`}>
                                                    {u.papel.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="p-4 text-gray-400">{u.serie_nome || '-'}</td>
                                            <td className="p-4 text-yellow-500 font-bold">{u.nivel}</td>
                                            <td className="p-4">
                                                <button
                                                    onClick={() => openEditUser(u)}
                                                    className="text-gray-400 hover:text-white p-1"
                                                >
                                                    <Edit className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Zona de Perigo */}
            <div className="bg-red-900/20 border border-red-900/50 rounded-xl p-6">
                <h2 className="text-xl font-bold text-red-500 mb-4 flex items-center">
                    <Shield className="w-6 h-6 mr-2" />
                    Zona de Perigo
                </h2>
                <p className="text-gray-400 mb-4">
                    Atenção: Esta ação irá apagar TODOS os alunos do sistema.
                </p>
                <button
                    onClick={handleResetSystem}
                    disabled={isResetting}
                    className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-bold flex items-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Trash2 className="w-5 h-5 mr-2" />
                    {isResetting ? 'DELETANDO...' : 'DELETAR TODOS OS ALUNOS'}
                </button>
            </div>


            {/* Edit User Modal */}
            {showEditUserModal && editingUser && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-xl w-full max-w-md border border-gray-700">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
                            <h3 className="font-bold text-lg">Editar Usuário</h3>
                            <button onClick={() => setShowEditUserModal(false)}><X className="w-5 h-5" /></button>
                        </div>
                        <form onSubmit={handleUpdateUser} className="p-4 space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Nome</label>
                                <input
                                    type="text"
                                    value={editFormData.nome || ''}
                                    onChange={e => setEditFormData({ ...editFormData, nome: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Email</label>
                                <input
                                    type="email"
                                    value={editFormData.email || ''}
                                    onChange={e => setEditFormData({ ...editFormData, email: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Papel</label>
                                <select
                                    value={editFormData.papel || 'aluno'}
                                    onChange={e => setEditFormData({ ...editFormData, papel: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                >
                                    <option value="aluno">Aluno</option>
                                    <option value="professor">Professor</option>
                                    <option value="gestor">Gestor</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Nova Senha (deixe em branco para não alterar)</label>
                                <input
                                    type="password"
                                    placeholder="Nova senha (opcional)"
                                    value={editFormData.senha || ''}
                                    onChange={e => setEditFormData({ ...editFormData, senha: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-white"
                                />
                            </div>
                            <div className="flex gap-2">
                                <button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-500 py-2 rounded font-bold flex justify-center items-center gap-2">
                                    <Save className="w-4 h-4" /> Salvar
                                </button>
                                <button
                                    type="button"
                                    onClick={handleDeleteUser}
                                    className="flex-1 bg-red-600 hover:bg-red-500 py-2 rounded font-bold flex justify-center items-center gap-2"
                                >
                                    <Trash2 className="w-4 h-4" /> Excluir
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
