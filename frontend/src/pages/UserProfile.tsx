import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { User, Shield, BookOpen, Image, ArrowLeft, Trash2 } from 'lucide-react';
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

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                // If id is present, fetch that user. If not, fetch current user (me)
                // But wait, our endpoint is /users/{id}/profile. 
                // If we are viewing "my profile", we can use currentUser.id
                const targetId = id || currentUser?.id;
                if (!targetId) return;

                const response = await apiClient.get(`/users/${targetId}/profile`);
                setProfile(response.data);
            } catch (error) {
                console.error('Erro ao carregar perfil', error);
                alert('Erro ao carregar perfil');
            } finally {
                setIsLoading(false);
            }
        };

        fetchProfile();
    }, [id, currentUser]);

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

    if (isLoading) return <div className="p-8 text-center text-white">Carregando perfil...</div>;
    if (!profile) return <div className="p-8 text-center text-white">Usuário não encontrado.</div>;

    const isAdmin = currentUser?.papel === 'admin';
    const isGestor = currentUser?.papel === 'gestor';
    const canDelete = isAdmin || (isGestor && profile.escola_nome === currentUser?.escola_nome);

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

                        {canDelete && currentUser?.id !== profile.id && (
                            <button
                                onClick={handleDeleteUser}
                                className="absolute top-4 right-4 p-2 bg-red-600/20 text-red-400 hover:bg-red-600 hover:text-white rounded-lg transition-colors"
                                title="Deletar Usuário"
                            >
                                <Trash2 className="w-5 h-5" />
                            </button>
                        )}
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
        </div>
    );
};
