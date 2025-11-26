import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { User, Shield, BookOpen, Image, ArrowLeft, Trash2, Upload, Gift } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

interface UserProfileData {
    id: number;
    nome: string;
    email: string;
    papel: string;
    serie?: string;
    nivel: number;
    xp: number;
    moedas: number;
    bio?: string;
    interesses?: string;
    avatar_url?: string;
    streak_count?: number;
    escola_nome?: string;
    joined_at: string;
    clan?: {
        id: number;
        nome: string;
        papel: string;
    };
    missoes_concluidas: {
        titulo: string;
        pontos: number;
        data: string;
    }[];
    posts: {
        id: number;
        conteudo: string;
        likes: number;
        data: string;
    }[];
}

export const UserProfile: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const { user: currentUser } = useAuth();
    const navigate = useNavigate();
    const [profile, setProfile] = useState<UserProfileData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState({
        nome: '',
        email: '',
        senha: '',
        bio: '',
        interesses: ''
    });
    const [inventory, setInventory] = useState<any[]>([]);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const targetId = id || currentUser?.id;
                if (!targetId) return;

                const response = await apiClient.get(`/users/${targetId}/profile`);
                setProfile(response.data);

                // Fetch inventory if viewing own profile
                if (!id || targetId === currentUser?.id) {
                    try {
                        const inventoryResponse = await apiClient.get('/shop/purchases');
                        setInventory(inventoryResponse.data);
                    } catch (error) {
                        console.error('Erro ao carregar inventário', error);
                    }
                }
            } catch (error) {
                console.error('Erro ao carregar perfil', error);
                alert('Erro ao carregar perfil');
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfile();
    }, [id, currentUser]);

    useEffect(() => {
        if (profile) {
            setEditForm({
                nome: profile.nome,
                email: profile.email,
                senha: '',
                bio: profile.bio || '',
                interesses: profile.interesses || ''
            });
        }
    }, [profile]);

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!profile) return;

        try {
            const data: any = {
                nome: editForm.nome,
                email: editForm.email,
                bio: editForm.bio,
                interesses: editForm.interesses
            };

            if (editForm.senha) {
                data.senha = editForm.senha;
            }

            const response = await apiClient.put(`/users/${profile.id}`, data);
            setProfile({ ...profile, ...response.data });
            setIsEditing(false);
            alert('Perfil atualizado com sucesso!');
        } catch (error: any) {
            console.error('Erro ao atualizar perfil:', error);
            alert(error.response?.data?.detail || 'Erro ao atualizar perfil');
        }
    };

    const handleDeleteUser = async () => {
        if (!profile) return;
        if (!confirm(`Tem certeza que deseja deletar o usuário ${profile.nome}? Esta ação é irreversível.`)) return;

        try {
            await apiClient.delete(`/users/${profile.id}`);
            alert('Usuário deletado com sucesso.');
            navigate(-1); // Go back
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao deletar usuário');
        }
    };

    const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            alert('Por favor, selecione uma imagem válida');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            alert('A imagem deve ter no máximo 5MB');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const targetId = id || currentUser?.id;
            const response = await apiClient.post(`/users/${targetId}/avatar`, formData);
            setProfile({ ...profile!, avatar_url: response.data.avatar_url });
            alert('Foto atualizada!');
        } catch (error: any) {
            console.error('Erro ao fazer upload:', error);
            alert(error.response?.data?.detail || 'Erro ao fazer upload da imagem');
        }
    };

    if (isLoading) return <div className="p-8 text-center text-white">Carregando perfil...</div>;
    if (!profile) return <div className="p-8 text-center text-white">Usuário não encontrado.</div>;

    const isAdmin = currentUser?.papel === 'admin';
    const isGestor = currentUser?.papel === 'gestor';
    const isOwner = currentUser?.id === profile.id;
    const canDelete = isAdmin || (isGestor && profile.escola_nome === currentUser?.escola_nome);
    const canEdit = isOwner || isAdmin || (isGestor && profile.escola_nome === currentUser?.escola_nome);

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <button
                onClick={() => navigate(-1)}
                className="mb-6 flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
                <ArrowLeft className="w-5 h-5" /> Voltar
            </button>

            <div className="max-w-4xl mx-auto space-y-8">
                {/* Header Card */}
                <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-blue-600 to-purple-600 opacity-20"></div>

                    <div className="relative flex flex-col md:flex-row items-center gap-8">
                        <div className="relative group">
                            <div className="w-32 h-32 rounded-full border-4 border-gray-800 shadow-xl overflow-hidden bg-gray-700 flex items-center justify-center">
                                {profile.avatar_url ? (
                                    <img
                                        src={profile.avatar_url.startsWith('http') ? profile.avatar_url : `${API_BASE_URL}${profile.avatar_url}`}
                                        alt={profile.nome}
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <User className="w-12 h-12 text-gray-400" />
                                )}
                                {/* Upload Button - Only for owner */}
                                {isOwner && (
                                    <label className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                                        <Upload className="w-6 h-6 text-white" />
                                        <input
                                            type="file"
                                            accept="image/*"
                                            onChange={handlePhotoUpload}
                                            className="hidden"
                                        />
                                    </label>
                                )}
                            </div>
                        </div>

                        <div className="flex-1 text-center md:text-left">
                            <h1 className="text-3xl font-bold mb-2">{profile.nome}</h1>
                            <div className="flex flex-wrap justify-center md:justify-start gap-3 mb-4">
                                <span className="px-3 py-1 bg-blue-900/50 text-blue-200 rounded-full text-sm border border-blue-500/30">
                                    Nível {profile.nivel}
                                </span>
                                <span className="px-3 py-1 bg-purple-900/50 text-purple-200 rounded-full text-sm border border-purple-500/30">
                                    {profile.papel.toUpperCase()}
                                </span>
                                {profile.serie && (
                                    <span className="px-3 py-1 bg-gray-700 text-gray-300 rounded-full text-sm">
                                        {profile.serie}
                                    </span>
                                )}
                            </div>

                            {profile.bio && <p className="text-gray-300 italic mb-4">"{profile.bio}"</p>}

                            <div className="flex gap-6 justify-center md:justify-start text-sm text-gray-400">
                                <div>
                                    <span className="block font-bold text-white text-lg">{profile.xp}</span>
                                    XP Total
                                </div>
                                <div>
                                    <span className="block font-bold text-white text-lg">{profile.moedas}</span>
                                    Moedas
                                </div>
                            </div>
                        </div>

                        <div className="absolute top-4 right-4 flex gap-2">
                            {canEdit && (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="p-2 bg-blue-600/20 text-blue-400 hover:bg-blue-600 hover:text-white rounded-lg transition-colors"
                                    title="Editar Perfil"
                                >
                                    ✏️
                                </button>
                            )}

                            {canDelete && !isOwner && (
                                <button
                                    onClick={handleDeleteUser}
                                    className="p-2 bg-red-600/20 text-red-400 hover:bg-red-600 hover:text-white rounded-lg transition-colors"
                                    title="Deletar Usuário"
                                >
                                    <Trash2 className="w-5 h-5" />
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Clan Info */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <Shield className="w-5 h-5 text-purple-400" />
                            Clã
                        </h2>
                        {profile.clan ? (
                            <div className="bg-gray-700/50 p-4 rounded-xl border border-gray-600">
                                <h3 className="font-bold text-lg text-purple-300">{profile.clan.nome}</h3>
                                <p className="text-gray-400 text-sm capitalize">{profile.clan.papel}</p>
                            </div>
                        ) : (
                            <p className="text-gray-400">Este usuário não participa de nenhum clã.</p>
                        )}
                    </div>

                    {/* Stats / Interests */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <User className="w-5 h-5 text-blue-400" />
                            Sobre
                        </h2>
                        <div className="space-y-3">
                            <div>
                                <p className="text-sm text-gray-400">Interesses</p>
                                <p className="text-white">{profile.interesses || 'Nenhum interesse listado.'}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400">Membro desde</p>
                                <p className="text-white">{new Date(profile.joined_at).toLocaleDateString()}</p>
                            </div>
                            {profile.escola_nome && (
                                <div>
                                    <p className="text-sm text-gray-400">Escola</p>
                                    <p className="text-white">{profile.escola_nome}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Stats Grid - Only for owner */}
                {isOwner && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                            <div className="text-yellow-400 font-bold text-2xl">{profile.moedas}</div>
                            <div className="text-gray-400 text-sm">Moedas</div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                            <div className="text-blue-400 font-bold text-2xl">{profile.xp}</div>
                            <div className="text-gray-400 text-sm">XP Total</div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                            <div className="text-orange-500 font-bold text-2xl flex items-center justify-center gap-1">
                                <span className="text-2xl">🔥</span> {profile.streak_count || 0}
                            </div>
                            <div className="text-gray-400 text-sm">Dias Seguidos</div>
                        </div>
                        <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                            <div className="text-purple-400 font-bold text-2xl">{inventory.length}</div>
                            <div className="text-gray-400 text-sm">Itens</div>
                        </div>
                    </div>
                )}

                {/* Inventory - Only for owner */}
                {isOwner && (
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <Gift className="w-5 h-5 text-purple-400" />
                            Inventário
                        </h2>

                        {inventory.length === 0 ? (
                            <p className="text-gray-400">Nenhum item ainda. Complete missões para ganhar moedas e compre itens na lojinha!</p>
                        ) : (
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                                {inventory.map((purchase) => (
                                    <div
                                        key={purchase.id}
                                        className="relative bg-gray-700 p-4 rounded-xl border-2 border-purple-500 flex flex-col items-center text-center transition-transform hover:scale-105"
                                    >
                                        <div className="absolute top-2 right-2">
                                            <span className={`text-xs px-2 py-1 rounded ${purchase.status === 'entregue' ? 'bg-green-900 text-green-200' :
                                                purchase.status === 'pendente' ? 'bg-yellow-900 text-yellow-200' :
                                                    'bg-red-900 text-red-200'
                                                }`}>
                                                {purchase.status}
                                            </span>
                                        </div>
                                        <div className="w-16 h-16 mb-3 bg-gray-800 rounded-full flex items-center justify-center overflow-hidden">
                                            {purchase.reward_imagem_url ? (
                                                <img src={purchase.reward_imagem_url} alt={purchase.reward_nome} className="w-full h-full object-cover" />
                                            ) : (
                                                <Gift className="w-8 h-8 text-gray-500" />
                                            )}
                                        </div>
                                        <h3 className="font-bold text-sm mb-1">{purchase.reward_nome}</h3>
                                        <p className="text-xs text-gray-400 mb-2">{purchase.reward_descricao}</p>
                                        <p className="text-xs text-yellow-400 font-bold">{purchase.custo_pago} Moedas</p>
                                        <p className="text-xs text-gray-500 mt-1">{purchase.data_compra}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Recent Activity Grid */}
                <div className="grid md:grid-cols-2 gap-8">
                    {/* Completed Missions */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <BookOpen className="w-5 h-5 text-green-400" />
                            Últimas Missões Concluídas
                        </h2>
                        {profile.missoes_concluidas.length > 0 ? (
                            <div className="space-y-3">
                                {profile.missoes_concluidas.map((m, idx) => (
                                    <div key={idx} className="flex justify-between items-center bg-gray-700/30 p-3 rounded-lg">
                                        <div>
                                            <p className="font-medium">{m.titulo}</p>
                                            <p className="text-xs text-gray-400">{new Date(m.data).toLocaleDateString()}</p>
                                        </div>
                                        <span className="text-yellow-400 text-sm font-bold">+{m.pontos} XP</span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-400">Nenhuma missão concluída recentemente.</p>
                        )}
                    </div>

                    {/* Mural Posts */}
                    <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                            <Image className="w-5 h-5 text-pink-400" />
                            Publicações no Mural
                        </h2>
                        {profile.posts.length > 0 ? (
                            <div className="space-y-3">
                                {profile.posts.map((post) => (
                                    <div key={post.id} className="bg-gray-700/30 p-3 rounded-lg">
                                        <p className="text-sm mb-2 line-clamp-2">"{post.conteudo}"</p>
                                        <div className="flex justify-between text-xs text-gray-400">
                                            <span>{new Date(post.data).toLocaleDateString()}</span>
                                            <span>❤️ {post.likes}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-400">Nenhuma publicação recente.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Edit Modal */}
            {isEditing && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-gray-800 rounded-2xl p-6 w-full max-w-md border border-gray-700">
                        <h2 className="text-2xl font-bold mb-6">Editar Perfil</h2>
                        <form onSubmit={handleUpdateUser} className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Nome</label>
                                <input
                                    type="text"
                                    value={editForm.nome}
                                    onChange={e => setEditForm({ ...editForm, nome: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Email</label>
                                <input
                                    type="email"
                                    value={editForm.email}
                                    onChange={e => setEditForm({ ...editForm, email: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Bio (Sobre você)</label>
                                <textarea
                                    value={editForm.bio}
                                    onChange={e => setEditForm({ ...editForm, bio: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary h-20 resize-none"
                                    placeholder="Conte um pouco sobre você..."
                                    maxLength={200}
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Interesses</label>
                                <input
                                    type="text"
                                    value={editForm.interesses}
                                    onChange={e => setEditForm({ ...editForm, interesses: e.target.value })}
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary"
                                    placeholder="Ex: Matemática, RPG, Futebol..."
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Nova Senha (opcional)</label>
                                <input
                                    type="password"
                                    value={editForm.senha}
                                    onChange={e => setEditForm({ ...editForm, senha: e.target.value })}
                                    placeholder="Deixe em branco para manter a atual"
                                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary"
                                />
                            </div>
                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setIsEditing(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-primary hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
                                >
                                    Salvar Alterações
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
