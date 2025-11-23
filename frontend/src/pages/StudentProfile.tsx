import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Gift, Edit2, Save, Upload, QrCode } from 'lucide-react';
import apiClient from '../api/client';
import { API_BASE_URL } from '../config/api';



interface UserData {
    id: number;
    nome: string;
    email: string;
    papel: string;
    nivel: number;
    xp: number;
    moedas: number;
    serie?: string;
    escola_id?: number;
    escola_nome?: string;
    bio?: string;
    interesses?: string;
    streak_count?: number;
    avatar_url?: string;
}

export const StudentProfile: React.FC = () => {
    const { user: authUser } = useAuth();
    const [user, setUser] = useState<UserData | null>(authUser);
    const [isEditing, setIsEditing] = useState(false);
    const [bio, setBio] = useState(authUser?.bio || '');
    const [interesses, setInteresses] = useState(authUser?.interesses || '');
    const [inventory, setInventory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showQrCode, setShowQrCode] = useState(false);
    const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [userResponse, purchasesResponse] = await Promise.all([
                    apiClient.get('/users/me'),
                    apiClient.get('/shop/purchases')
                ]);
                setUser(userResponse.data);
                setBio(userResponse.data.bio || '');
                setInteresses(userResponse.data.interesses || '');
                setInventory(purchasesResponse.data);

                // Fetch QR Code
                try {
                    const qrResponse = await apiClient.get('/users/me/qrcode');
                    setQrCodeUrl(qrResponse.data.qrcode_base64);
                } catch (e) {
                    console.error("Failed to load QR Code", e);
                }

            } catch (error) {
                console.error('Erro ao carregar dados', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleSaveProfile = async () => {
        try {
            const params = new URLSearchParams();
            if (bio) params.append('bio', bio);
            if (interesses) params.append('interesses', interesses);

            const response = await apiClient.put(`/users/me/profile?${params.toString()}`);
            setUser(response.data);
            setIsEditing(false);
            alert('Perfil atualizado!');
        } catch (error) {
            console.error('Erro ao atualizar perfil:', error);
            alert('Erro ao atualizar perfil. Tente novamente.');
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
            const response = await apiClient.post('/users/me/avatar', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setUser(response.data);
            alert('Foto atualizada!');
        } catch (error: any) {
            console.error('Erro ao fazer upload:', error);
            alert(error.response?.data?.detail || 'Erro ao fazer upload da imagem');
        }
    };

    if (!user) return null;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <div className="max-w-4xl mx-auto space-y-8">
                {/* Profile Header */}
                <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700 flex flex-col md:flex-row gap-8 items-center md:items-start">
                    {/* Avatar Section */}
                    <div className="relative group">
                        <div className="w-32 h-32 rounded-full bg-gray-700 border-4 border-primary overflow-hidden flex items-center justify-center">
                            {user.avatar_url ? (
                                <img
                                    src={user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`}
                                    alt="Avatar"
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <User className="w-16 h-16 text-gray-400" />
                            )}
                        </div>
                        <div className="absolute -bottom-2 -right-2 bg-primary text-white w-8 h-8 rounded-full flex items-center justify-center font-bold border-2 border-gray-800">
                            {user.nivel}
                        </div>
                        {/* Upload Button */}
                        <label className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer rounded-full">
                            <Upload className="w-6 h-6 text-white" />
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handlePhotoUpload}
                                className="hidden"
                            />
                        </label>
                    </div>

                    {/* Info Section */}
                    <div className="flex-1 w-full">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h1 className="text-3xl font-bold">{user.nome}</h1>
                                <p className="text-gray-400">{user.serie}{user.escola_nome ? ` • ${user.escola_nome}` : ''}</p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setShowQrCode(!showQrCode)}
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 transition-colors"
                                >
                                    <QrCode className="w-4 h-4" />
                                    QR Code
                                </button>
                                <button
                                    onClick={() => isEditing ? handleSaveProfile() : setIsEditing(true)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${isEditing
                                        ? 'bg-green-600 hover:bg-green-500'
                                        : 'bg-gray-700 hover:bg-gray-600'
                                        }`}
                                >
                                    {isEditing ? <Save className="w-4 h-4" /> : <Edit2 className="w-4 h-4" />}
                                    {isEditing ? 'Salvar' : 'Editar'}
                                </button>
                            </div>
                        </div>

                        {showQrCode && (
                            <div className="mb-6 p-4 bg-white rounded-xl flex flex-col items-center text-black animate-fade-in">
                                <h3 className="font-bold mb-2">Seu Cartão de Aventureiro</h3>
                                {qrCodeUrl ? (
                                    <img src={qrCodeUrl} alt="QR Code" className="w-48 h-48" />
                                ) : (
                                    <div className="w-48 h-48 bg-gray-200 flex items-center justify-center">
                                        Carregando...
                                    </div>
                                )}
                                <p className="text-sm text-gray-600 mt-2">Mostre para o professor validar missões!</p>
                            </div>
                        )}

                        {isEditing ? (
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Bio</label>
                                    <textarea
                                        value={bio}
                                        onChange={(e) => setBio(e.target.value)}
                                        className="w-full bg-gray-900 border border-gray-600 rounded p-2 text-white"
                                        rows={2}
                                        placeholder="Conte um pouco sobre você..."
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">Interesses (separados por vírgula)</label>
                                    <input
                                        type="text"
                                        value={interesses}
                                        onChange={(e) => setInteresses(e.target.value)}
                                        className="w-full bg-gray-900 border border-gray-600 rounded p-2 text-white"
                                        placeholder="Matemática, Ciências, Artes..."
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <p className="text-gray-300 italic">"{bio || 'Nenhuma bio definida...'}"</p>
                                <div className="flex gap-2 flex-wrap">
                                    {interesses ? interesses.split(',').map((tag: string, i: number) => (
                                        <span key={i} className="px-2 py-1 bg-gray-700 rounded-full text-xs text-gray-300">
                                            {tag.trim()}
                                        </span>
                                    )) : (
                                        <span className="text-gray-500 text-sm">Sem interesses definidos</span>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                        <div className="text-yellow-400 font-bold text-2xl">{user.moedas}</div>
                        <div className="text-gray-400 text-sm">Moedas</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                        <div className="text-blue-400 font-bold text-2xl">{user.xp}</div>
                        <div className="text-gray-400 text-sm">XP Total</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                        <div className="text-orange-500 font-bold text-2xl flex items-center justify-center gap-1">
                            <span className="text-2xl">🔥</span> {user.streak_count || 0}
                        </div>
                        <div className="text-gray-400 text-sm">Dias Seguidos</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 text-center">
                        <div className="text-purple-400 font-bold text-2xl">{inventory.length}</div>
                        <div className="text-gray-400 text-sm">Itens</div>
                    </div>
                </div>

                {/* Inventory */}
                <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Gift className="w-5 h-5 text-purple-400" />
                        Inventário
                    </h2>

                    {loading ? (
                        <p>Carregando...</p>
                    ) : inventory.length === 0 ? (
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
            </div>
        </div>
    );
};
