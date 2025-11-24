import React, { useState } from 'react';
import { Bell, X, CheckCheck } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useNavigate } from 'react-router-dom';

export const NotificationBell: React.FC = () => {
    const { notifications, unreadCount, markAsRead, markAllAsRead, clearNotifications, requestPermission } = useWebSocket();
    const [isOpen, setIsOpen] = useState(false);
    const navigate = useNavigate();

    React.useEffect(() => {
        // Solicitar permissão para notificações do navegador
        requestPermission();
    }, [requestPermission]);

    const handleNotificationClick = (notification: any) => {
        markAsRead(notification.id);

        // Navegar baseado no tipo de notificação
        switch (notification.type) {
            case 'mission_assigned':
            case 'mission_validated':
            case 'mission_rejected':
                navigate('/dashboard');
                break;
            case 'clan_invite':
                navigate('/clans');
                break;
            case 'clan_message':
                navigate('/clans');
                break;
            case 'new_achievement':
                navigate('/achievements');
                break;
        }

        setIsOpen(false);
    };

    const getNotificationIcon = (type: string) => {
        switch (type) {
            case 'mission_assigned':
                return '📋';
            case 'mission_validated':
                return '✅';
            case 'mission_rejected':
                return '❌';
            case 'clan_invite':
                return '🛡️';
            case 'clan_message':
                return '💬';
            case 'new_achievement':
                return '🏆';
            case 'system_announcement':
                return '📢';
            default:
                return '🔔';
        }
    };

    const formatTimestamp = (date: Date) => {
        const now = new Date();
        const diff = now.getTime() - new Date(date).getTime();
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Agora';
        if (minutes < 60) return `${minutes}m atrás`;
        if (hours < 24) return `${hours}h atrás`;
        return `${days}d atrás`;
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
                <Bell className="w-6 h-6 text-gray-300" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold animate-pulse">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {isOpen && (
                <>
                    {/* Overlay */}
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute right-0 mt-2 w-96 bg-gray-800 border border-gray-700 rounded-xl shadow-2xl z-50 max-h-[600px] flex flex-col">
                        {/* Header */}
                        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
                            <h3 className="text-lg font-bold text-white">Notificações</h3>
                            <div className="flex items-center gap-2">
                                {unreadCount > 0 && (
                                    <button
                                        onClick={markAllAsRead}
                                        className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
                                        title="Marcar todas como lidas"
                                    >
                                        <CheckCheck className="w-4 h-4" />
                                    </button>
                                )}
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="text-gray-400 hover:text-white"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Notifications List */}
                        <div className="flex-1 overflow-y-auto">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center text-gray-400">
                                    <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                    <p>Nenhuma notificação</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-gray-700">
                                    {notifications.map((notification) => (
                                        <div
                                            key={notification.id}
                                            onClick={() => handleNotificationClick(notification)}
                                            className={`p-4 hover:bg-gray-700 cursor-pointer transition-colors ${!notification.read ? 'bg-gray-750' : ''
                                                }`}
                                        >
                                            <div className="flex items-start gap-3">
                                                <span className="text-2xl flex-shrink-0">
                                                    {getNotificationIcon(notification.type)}
                                                </span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center justify-between gap-2 mb-1">
                                                        <h4 className="font-bold text-white text-sm truncate">
                                                            {notification.title}
                                                        </h4>
                                                        {!notification.read && (
                                                            <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                                                        )}
                                                    </div>
                                                    <p className="text-gray-300 text-sm mb-1">
                                                        {notification.message}
                                                    </p>
                                                    <span className="text-xs text-gray-500">
                                                        {formatTimestamp(notification.timestamp)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        {notifications.length > 0 && (
                            <div className="p-3 border-t border-gray-700">
                                <button
                                    onClick={() => {
                                        clearNotifications();
                                        setIsOpen(false);
                                    }}
                                    className="w-full text-sm text-red-400 hover:text-red-300 py-2"
                                >
                                    Limpar todas
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};
