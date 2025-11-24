import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { UserPlus, Building, LogOut, Trash2, Edit, Copy, CheckCircle, BarChart2 } from 'lucide-react';
import apiClient from '../api/client';
import { useNavigate } from 'react-router-dom';

interface Escola {
    id: number;
    nome: string;
    criado_em: string;
}

interface Manager {
    id: number;
    nome: string;
    email: string;
    escola_id: number;
    escola_nome?: string;
    criado_em: string;
}

export const AdminPanel: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [escolas, setEscolas] = useState<Escola[]>([]);
    const [managers, setManagers] = useState<Manager[]>([]);
    const [newSchoolName, setNewSchoolName] = useState('');
    const [managerData, setManagerData] = useState({
        nome: '',
        email: '',
        senha: '',
        escola_id: ''
    });
    const [editingManager, setEditingManager] = useState<Manager | null>(null);
    const [editPassword, setEditPassword] = useState('');
    const [createdCredentials, setCreatedCredentials] = useState<{ nome: string, email: string, senha: string, escola: string } | null>(null);
    const [copied, setCopied] = useState(false);

    const [topSchools, setTopSchools] = useState<any[]>([]);

    useEffect(() => {
        fetchEscolas();
        fetchTopSchools();
        fetchManagers();
    }, []);

    const fetchTopSchools = async () => {
        try {
            const response = await apiClient.get('/reports/top_schools');
            setTopSchools(response.data);
        } catch (error) {
            console.error('Erro ao buscar top escolas', error);
        }
    };

    const fetchEscolas = async () => {
        try {
            const response = await apiClient.get('/escolas/');
            setEscolas(response.data);
        } catch (error) {
            console.error('Erro ao buscar escolas', error);
        }
    };

    const fetchManagers = async () => {
        try {
            const response = await apiClient.get('/users/');
            const gestores = response.data.filter((u: any) => u.papel === 'gestor');
            setManagers(gestores);
        } catch (error) {
            console.error('Erro ao buscar gestores', error);
        }
    };

    const handleCreateSchool = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await apiClient.post('/escolas/', { nome: newSchoolName });
            alert('Escola criada com sucesso!');
            setNewSchoolName('');
            fetchEscolas();
        } catch (error) {
            alert('Erro ao criar escola');
        }
    };

    const handleDeleteSchool = async (id: number) => {
        if (!confirm('Tem certeza que deseja excluir esta escola? Isso não pode ser desfeito.')) return;

        try {
            await apiClient.delete(`/escolas/${id}`);
            alert('Escola excluída com sucesso!');
            fetchEscolas();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao excluir escola');
        }
    };

    const handleCreateManager = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await apiClient.post('/admin/gestor', {
                ...managerData,
                papel: 'gestor',
                escola_id: parseInt(managerData.escola_id)
            });

            // Mostrar credenciais
            const escolaNome = escolas.find(e => e.id === parseInt(managerData.escola_id))?.nome || '';
            setCreatedCredentials({
                nome: managerData.nome,
                email: managerData.email,
                senha: managerData.senha,
                escola: escolaNome
            });

            setManagerData({ nome: '', email: '', senha: '', escola_id: '' });
            fetchManagers();
        } catch (error: any) {
            alert(`Erro ao criar gestor: ${error.response?.data?.detail || 'Erro desconhecido'}`);
        }
    };

    const handleUpdateManager = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingManager) return;

        try {
            const updateData: any = {
                nome: editingManager.nome,
                email: editingManager.email,
                papel: 'gestor',
                escola_id: editingManager.escola_id
            };

            if (editPassword) {
                updateData.senha = editPassword;
            }

            await apiClient.put(`/users/${editingManager.id}`, updateData);
            alert('Gestor atualizado com sucesso!');
            setEditingManager(null);
            setEditPassword('');
            fetchManagers();
        } catch (error: any) {
            alert(`Erro ao atualizar gestor: ${error.response?.data?.detail || 'Erro desconhecido'}`);
        }
    };

    const handleDeleteManager = async (id: number, nome: string) => {
        if (!confirm(`Tem certeza que deseja excluir o gestor "${nome}"? Esta ação não pode ser desfeita.`)) return;

        try {
            await apiClient.delete(`/users/${id}`);
            alert('Gestor excluído com sucesso!');
            fetchManagers();
        } catch (error: any) {
            alert(`Erro ao excluir gestor: ${error.response?.data?.detail || 'Erro desconhecido'}`);
        }
    };

    const copyCredentials = () => {
        if (!createdCredentials) return;
        const text = `Nome: ${createdCredentials.nome}\nEmail: ${createdCredentials.email}\nSenha: ${createdCredentials.senha}\nEscola: ${createdCredentials.escola}`;
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (!user || user.papel !== 'admin') return <div className="text-white p-10">Acesso Negado</div>;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <header className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-red-500">Painel Administrativo</h1>
                    <p className="text-gray-400">Gerencie escolas e acessos</p>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={() => navigate('/analytics')}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-bold transition-colors"
                    >
                        <BarChart2 className="w-4 h-4" />
                        Relatórios
                    </button>
                    <button
                        onClick={logout}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                        Sair
                    </button>
                </div>
            </header>

            {/* Top Schools Chart */}
            {topSchools.length > 0 && (
                <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 mb-8">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <span className="text-yellow-400">🏆</span> Top Escolas (XP Total)
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                        {topSchools.map((school, index) => (
                            <div key={index} className="bg-gray-700/50 p-4 rounded-lg text-center border border-gray-600">
                                <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center font-bold
                                    ${index === 0 ? 'bg-yellow-500 text-black' :
                                        index === 1 ? 'bg-gray-400 text-black' :
                                            index === 2 ? 'bg-orange-700 text-white' :
                                                'bg-gray-600 text-gray-300'}`}>
                                    #{index + 1}
                                </div>
                                <h3 className="font-bold truncate" title={school.nome}>{school.nome}</h3>
                                <p className="text-blue-400 font-bold text-lg">{school.total_xp} XP</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid md:grid-cols-2 gap-8">
                {/* Escolas */}
                <div className="space-y-6">
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                            <Building className="w-6 h-6 text-blue-400" />
                            Nova Escola
                        </h2>
                        <form onSubmit={handleCreateSchool} className="flex gap-2">
                            <input
                                type="text"
                                value={newSchoolName}
                                onChange={(e) => setNewSchoolName(e.target.value)}
                                placeholder="Nome da Escola"
                                className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                required
                            />
                            <button
                                type="submit"
                                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold"
                            >
                                Criar
                            </button>
                        </form>
                    </div>

                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-xl font-bold mb-4">Escolas Cadastradas</h2>
                        <div className="space-y-2">
                            {escolas.map((escola) => (
                                <div key={escola.id} className="p-3 bg-gray-700 rounded-lg flex justify-between items-center group">
                                    <div>
                                        <span className="font-medium block">{escola.nome}</span>
                                        <span className="text-xs text-gray-400">ID: {escola.id}</span>
                                    </div>
                                    <button
                                        onClick={() => handleDeleteSchool(escola.id)}
                                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-600 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                        title="Excluir Escola"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Gestores */}
                <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                    <h2 className="text-2xl font-bold flex items-center gap-2 mb-6">
                        <UserPlus className="w-6 h-6 text-green-400" />
                        Cadastrar Gestor
                    </h2>
                    <form onSubmit={handleCreateManager} className="space-y-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Escola</label>
                            <select
                                value={managerData.escola_id}
                                onChange={(e) => setManagerData({ ...managerData, escola_id: e.target.value })}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                                required
                            >
                                <option value="">Selecione uma escola...</option>
                                {escolas.map((escola) => (
                                    <option key={escola.id} value={escola.id}>
                                        {escola.nome}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Nome do Gestor</label>
                            <input
                                type="text"
                                value={managerData.nome}
                                onChange={(e) => setManagerData({ ...managerData, nome: e.target.value })}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Email</label>
                            <input
                                type="email"
                                value={managerData.email}
                                onChange={(e) => setManagerData({ ...managerData, email: e.target.value })}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Senha</label>
                            <input
                                type="password"
                                value={managerData.senha}
                                onChange={(e) => setManagerData({ ...managerData, senha: e.target.value })}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            className="w-full py-3 bg-green-600 hover:bg-green-500 rounded-lg font-bold mt-2"
                        >
                            Cadastrar Gestor
                        </button>
                    </form>
                </div>
            </div>

            {/* Lista de Gestores */}
            <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 mt-8">
                <h2 className="text-2xl font-bold mb-6">Gestores Cadastrados</h2>

                {managers.length === 0 ? (
                    <p className="text-gray-400 text-center py-8">Nenhum gestor cadastrado</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-900/50 text-gray-400 uppercase text-xs">
                                <tr>
                                    <th className="p-4 text-left">Nome</th>
                                    <th className="p-4 text-left">Email</th>
                                    <th className="p-4 text-left">Escola</th>
                                    <th className="p-4 text-center">Ações</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {managers.map((manager) => {
                                    const escola = escolas.find(e => e.id === manager.escola_id);
                                    return (
                                        <tr key={manager.id} className="hover:bg-gray-700/50">
                                            <td className="p-4 font-medium">{manager.nome}</td>
                                            <td className="p-4 text-gray-400">{manager.email}</td>
                                            <td className="p-4 text-gray-400">
                                                {escola ? escola.nome : 'N/A'}
                                            </td>
                                            <td className="p-4">
                                                <div className="flex justify-center gap-2">
                                                    <button
                                                        onClick={() => setEditingManager(manager)}
                                                        className="p-2 text-blue-400 hover:text-blue-300 hover:bg-gray-600 rounded-lg transition-colors"
                                                        title="Editar"
                                                    >
                                                        <Edit className="w-4 h-4" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteManager(manager.id, manager.nome)}
                                                        className="p-2 text-red-400 hover:text-red-300 hover:bg-gray-600 rounded-lg transition-colors"
                                                        title="Excluir"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}</tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Modal de Edição */}
            {editingManager && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 max-w-md w-full">
                        <h2 className="text-2xl font-bold mb-4">Editar Gestor</h2>
                        <form onSubmit={handleUpdateManager} className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Nome</label>
                                <input
                                    type="text"
                                    value={editingManager.nome}
                                    onChange={(e) => setEditingManager({ ...editingManager, nome: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Email</label>
                                <input
                                    type="email"
                                    value={editingManager.email}
                                    onChange={(e) => setEditingManager({ ...editingManager, email: e.target.value })}
                                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Escola</label>
                                <select
                                    value={editingManager.escola_id}
                                    onChange={(e) => setEditingManager({ ...editingManager, escola_id: parseInt(e.target.value) })}
                                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                                    required
                                >
                                    {escolas.map((escola) => (
                                        <option key={escola.id} value={escola.id}>
                                            {escola.nome}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Nova Senha (deixe em branco para não alterar)</label>
                                <input
                                    type="password"
                                    value={editPassword}
                                    onChange={(e) => setEditPassword(e.target.value)}
                                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                                    placeholder="••••••••"
                                />
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setEditingManager(null);
                                        setEditPassword('');
                                    }}
                                    className="flex-1 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg font-bold"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold"
                                >
                                    Salvar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal de Credenciais */}
            {createdCredentials && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-gradient-to-br from-green-900/90 to-gray-800 rounded-2xl p-8 border-2 border-green-500 max-w-lg w-full shadow-2xl">
                        <div className="flex items-center justify-center mb-6">
                            <CheckCircle className="w-16 h-16 text-green-400" />
                        </div>
                        <h2 className="text-3xl font-bold text-center mb-2 text-green-400">Gestor Criado!</h2>
                        <p className="text-center text-yellow-300 font-bold mb-6">⚠️ ATENÇÃO: Guarde estas credenciais! Esta é a ÚNICA vez que a senha será exibida.</p>

                        <div className="bg-gray-900/50 rounded-lg p-6 mb-6 space-y-3">
                            <div>
                                <span className="text-gray-400 text-sm">Nome:</span>
                                <p className="text-white font-bold text-lg">{createdCredentials.nome}</p>
                            </div>
                            <div>
                                <span className="text-gray-400 text-sm">Email:</span>
                                <p className="text-white font-mono">{createdCredentials.email}</p>
                            </div>
                            <div>
                                <span className="text-gray-400 text-sm">Senha:</span>
                                <p className="text-green-400 font-mono text-xl font-bold">{createdCredentials.senha}</p>
                            </div>
                            <div>
                                <span className="text-gray-400 text-sm">Escola:</span>
                                <p className="text-white">{createdCredentials.escola}</p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={copyCredentials}
                                className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold flex items-center justify-center gap-2"
                            >
                                {copied ? (
                                    <>
                                        <CheckCircle className="w-5 h-5" />
                                        Copiado!
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-5 h-5" />
                                        Copiar Credenciais
                                    </>
                                )}
                            </button>
                            <button
                                onClick={() => setCreatedCredentials(null)}
                                className="flex-1 py-3 bg-gray-600 hover:bg-gray-500 rounded-lg font-bold"
                            >
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
