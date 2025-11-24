import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader } from 'lucide-react';
import apiClient from '../api/client';
import { useWebSocket } from '../hooks/useWebSocket';

interface Message {
    id: number;
    clan_id: number;
    user_id: number;
    user_name: string;
    user_avatar: string | null;
    message: string;
    created_at: string;
    edited: boolean;
}

interface ClanChatProps {
    clanId: number;
    currentUserId: number;
}

export const ClanChat: React.FC<ClanChatProps> = ({ clanId, currentUserId }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const { notifications } = useWebSocket();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchMessages();
    }, [clanId]);

    useEffect(() => {
        // Escutar novas mensagens via WebSocket
        const chatNotifications = notifications.filter(
            n => n.type === 'clan_message' && n.data?.clan_id === clanId
        );

        if (chatNotifications.length > 0) {
            const latestNotification = chatNotifications[0];
            if (latestNotification.data) {
                const newMsg: Message = {
                    id: latestNotification.data.message_id,
                    clan_id: clanId,
                    user_id: latestNotification.data.user_id || 0,
                    user_name: latestNotification.data.user_name,
                    user_avatar: latestNotification.data.user_avatar,
                    message: latestNotification.data.message,
                    created_at: latestNotification.data.created_at,
                    edited: false
                };

                setMessages(prev => {
                    // Evitar duplicatas
                    if (prev.some(m => m.id === newMsg.id)) return prev;
                    return [...prev, newMsg];
                });
                scrollToBottom();
            }
        }
    }, [notifications, clanId]);

    const fetchMessages = async () => {
        try {
            setLoading(true);
            const res = await apiClient.get(`/chat/clan/${clanId}/messages?limit=50`);
            setMessages(res.data);
            setTimeout(scrollToBottom, 100);
        } catch (error) {
            console.error('Error fetching messages:', error);
        } finally {
            setLoading(false);
        }
    };

    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMessage.trim() || sending) return;

        try {
            setSending(true);
            const res = await apiClient.post(`/chat/clan/${clanId}/messages`, {
                message: newMessage.trim()
            });

            // Adicionar mensagem localmente (WebSocket enviará para outros)
            setMessages(prev => [...prev, res.data]);
            setNewMessage('');
            scrollToBottom();
        } catch (error: any) {
            console.error('Error sending message:', error);
            alert(error.response?.data?.detail || 'Erro ao enviar mensagem');
        } finally {
            setSending(false);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Hoje';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Ontem';
        } else {
            return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
        }
    };

    const groupMessagesByDate = () => {
        const grouped: { [key: string]: Message[] } = {};

        messages.forEach(msg => {
            const dateKey = formatDate(msg.created_at);
            if (!grouped[dateKey]) {
                grouped[dateKey] = [];
            }
            grouped[dateKey].push(msg);
        });

        return grouped;
    };

    const groupedMessages = groupMessagesByDate();

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <Loader className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[600px] bg-gray-800 rounded-xl border border-gray-700">
            {/* Header */}
            <div className="p-4 border-b border-gray-700">
                <h3 className="text-lg font-bold text-white">💬 Chat do Clã</h3>
                <p className="text-sm text-gray-400">{messages.length} mensagens</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {Object.keys(groupedMessages).length === 0 ? (
                    <div className="text-center text-gray-400 py-8">
                        <p>Nenhuma mensagem ainda.</p>
                        <p className="text-sm">Seja o primeiro a enviar uma mensagem!</p>
                    </div>
                ) : (
                    Object.entries(groupedMessages).map(([date, msgs]) => (
                        <div key={date}>
                            {/* Date Separator */}
                            <div className="flex items-center justify-center my-4">
                                <div className="bg-gray-700 px-3 py-1 rounded-full text-xs text-gray-400">
                                    {date}
                                </div>
                            </div>

                            {/* Messages for this date */}
                            {msgs.map((msg, index) => {
                                const isOwn = msg.user_id === currentUserId;
                                const showAvatar = index === 0 || msgs[index - 1].user_id !== msg.user_id;

                                return (
                                    <div
                                        key={msg.id}
                                        className={`flex items-start gap-3 mb-3 ${isOwn ? 'flex-row-reverse' : ''}`}
                                    >
                                        {/* Avatar */}
                                        {showAvatar ? (
                                            <img
                                                src={msg.user_avatar || '/default-avatar.png'}
                                                alt={msg.user_name}
                                                className="w-8 h-8 rounded-full flex-shrink-0"
                                            />
                                        ) : (
                                            <div className="w-8 flex-shrink-0" />
                                        )}

                                        {/* Message Bubble */}
                                        <div className={`flex flex-col ${isOwn ? 'items-end' : 'items-start'} max-w-[70%]`}>
                                            {showAvatar && (
                                                <span className="text-xs text-gray-400 mb-1 px-2">
                                                    {msg.user_name}
                                                </span>
                                            )}
                                            <div
                                                className={`px-4 py-2 rounded-2xl ${isOwn
                                                    ? 'bg-primary text-white'
                                                    : 'bg-gray-700 text-gray-100'
                                                    }`}
                                            >
                                                <p className="text-sm break-words">{msg.message}</p>
                                                {msg.edited && (
                                                    <span className="text-xs opacity-70">(editado)</span>
                                                )}
                                            </div>
                                            <span className="text-xs text-gray-500 mt-1 px-2">
                                                {formatTime(msg.created_at)}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={sendMessage} className="p-4 border-t border-gray-700">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Digite sua mensagem..."
                        maxLength={1000}
                        disabled={sending}
                        className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                    />
                    <button
                        type="submit"
                        disabled={!newMessage.trim() || sending}
                        className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {sending ? (
                            <Loader className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                    {newMessage.length}/1000 caracteres
                </p>
            </form>
        </div>
    );
};
