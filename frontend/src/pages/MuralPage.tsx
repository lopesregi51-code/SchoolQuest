import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import { Heart, Trash2, Image as ImageIcon, Send } from 'lucide-react';
import { API_BASE_URL } from '../config/api';
import { Link } from 'react-router-dom';

interface Post {
    id: number;
    user_id: number;
    user_nome: string;
    escola_id: number;
    texto: string | null;
    imagem_url: string | null;
    data_criacao: string;
    likes_count: number;
    liked_by_me: boolean;
    liked_by: string[];
}

export const MuralPage: React.FC = () => {
    const { user } = useAuth();
    const [posts, setPosts] = useState<Post[]>([]);
    const [newPostText, setNewPostText] = useState('');
    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPosts();
    }, []);

    const fetchPosts = async () => {
        try {
            const res = await apiClient.get('/mural/');
            setPosts(res.data);
        } catch (error) {
            console.error('Erro ao carregar posts', error);
        } finally {
            setLoading(false);
        }
    };

    const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedImage(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleCreatePost = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!newPostText && !selectedImage) {
            alert('Adicione um texto ou uma imagem!');
            return;
        }

        try {
            const formData = new FormData();
            if (newPostText) formData.append('texto', newPostText);
            if (selectedImage) formData.append('imagem', selectedImage);

            await apiClient.post('/mural/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            setNewPostText('');
            setSelectedImage(null);
            setImagePreview(null);
            fetchPosts();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao criar post');
        }
    };

    const handleLike = async (postId: number) => {
        try {
            await apiClient.post(`/mural/${postId}/like`);
            fetchPosts();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao curtir post');
        }
    };

    const handleDelete = async (postId: number) => {
        if (!confirm('Tem certeza que deseja deletar este post?')) return;

        try {
            await apiClient.delete(`/mural/${postId}`);
            fetchPosts();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao deletar post');
        }
    };

    return (
        <div className="min-h-screen bg-dark text-white p-4">
            <div className="max-w-2xl mx-auto space-y-4">
                <header className="bg-gray-800 rounded-xl p-4 border border-gray-700 flex justify-between items-center">
                    <div>
                        <h1 className="text-xl font-bold">Mural da Escola</h1>
                        <p className="text-xs text-gray-400">Compartilhe momentos!</p>
                    </div>
                </header>

                {/* Create Post */}
                <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                    <form onSubmit={handleCreatePost} className="space-y-3">
                        <textarea
                            id="post-content"
                            name="post-content"
                            placeholder="O que você quer compartilhar?"
                            value={newPostText}
                            onChange={(e) => setNewPostText(e.target.value)}
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg p-3 text-sm text-white resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                            rows={2}
                        />

                        {imagePreview && (
                            <div className="relative inline-block">
                                <img src={imagePreview} alt="Preview" className="h-32 w-auto object-cover rounded-lg border border-gray-600" />
                                <button
                                    type="button"
                                    onClick={() => {
                                        setSelectedImage(null);
                                        setImagePreview(null);
                                    }}
                                    className="absolute -top-2 -right-2 bg-red-600 hover:bg-red-500 p-1 rounded-full shadow-lg"
                                >
                                    <Trash2 className="w-3 h-3" />
                                </button>
                            </div>
                        )}

                        <div className="flex justify-between items-center pt-2 border-t border-gray-700/50">
                            <label className="flex items-center gap-2 text-xs text-gray-400 hover:text-white cursor-pointer transition-colors">
                                <ImageIcon className="w-4 h-4" />
                                <span>Adicionar Foto</span>
                                <input
                                    id="post-image"
                                    name="post-image"
                                    type="file"
                                    accept="image/*"
                                    onChange={handleImageSelect}
                                    className="hidden"
                                />
                            </label>
                            <button
                                type="submit"
                                className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-bold transition-colors"
                            >
                                <Send className="w-3 h-3" />
                                Publicar
                            </button>
                        </div>
                    </form>
                </div>

                {/* Posts Feed */}
                {loading ? (
                    <div className="text-center py-8 text-sm text-gray-500">Carregando...</div>
                ) : posts.length === 0 ? (
                    <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 text-center text-gray-400">
                        <p className="text-sm">Nenhuma publicação ainda.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {posts.map((post) => (
                            <div key={post.id} className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                                {/* Post Header */}
                                <div className="px-4 py-3 flex justify-between items-start">
                                    <div className="flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-300">
                                            {post.user_nome.charAt(0)}
                                        </div>
                                        <div>
                                            {post.user_id ? (
                                                <Link to={`/profile/${post.user_id}`} className="text-sm font-bold leading-tight hover:text-blue-400 hover:underline">
                                                    {post.user_nome}
                                                </Link>
                                            ) : (
                                                <span className="text-sm font-bold leading-tight">{post.user_nome}</span>
                                            )}
                                            <p className="text-[10px] text-gray-500">{post.data_criacao}</p>
                                        </div>
                                    </div>
                                    {(user?.id === post.user_id || user?.papel === 'gestor' || user?.papel === 'admin') && (
                                        <button
                                            onClick={() => handleDelete(post.id)}
                                            className="text-gray-500 hover:text-red-400 transition-colors"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    )}
                                </div>

                                {/* Post Content */}
                                <div className="px-4 pb-2">
                                    {post.texto && <p className="text-sm text-gray-200 mb-2 leading-relaxed">{post.texto}</p>}
                                    {post.imagem_url && (
                                        <div className="mt-2">
                                            <img
                                                src={post.imagem_url.startsWith('http') ? post.imagem_url : `${API_BASE_URL}${post.imagem_url}`}
                                                alt="Post"
                                                className="max-h-96 w-full object-cover rounded-lg border border-gray-700"
                                            />
                                        </div>
                                    )}
                                </div>

                                {/* Post Actions */}
                                <div className="px-4 py-2 border-t border-gray-700/50 flex items-center gap-4">
                                    <button
                                        onClick={() => handleLike(post.id)}
                                        className={`flex items-center gap-1.5 text-xs font-medium transition-colors ${post.liked_by_me
                                            ? 'text-red-400'
                                            : 'text-gray-400 hover:text-gray-300'
                                            }`}
                                    >
                                        <Heart className={`w-3.5 h-3.5 ${post.liked_by_me ? 'fill-current' : ''}`} />
                                        <span>{post.likes_count}</span>
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
