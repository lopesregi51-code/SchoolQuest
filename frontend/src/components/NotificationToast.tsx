import React from 'react';
import { useWebSocket, type Notification } from '../hooks/useWebSocket';
import { X } from 'lucide-react';

export const NotificationToast: React.FC = () => {
    const { notifications } = useWebSocket();
    const [visibleNotifications, setVisibleNotifications] = React.useState<Notification[]>([]);

    React.useEffect(() => {
        // Mostrar apenas as últimas 3 notificações não lidas
        const recent = notifications
            .filter(n => !n.read)
            .slice(0, 3);

        setVisibleNotifications(recent);

        // Auto-remover após 5 segundos
        if (recent.length > 0) {
            const timer = setTimeout(() => {
                setVisibleNotifications([]);
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [notifications]);

    const removeNotification = (id: string) => {
        setVisibleNotifications(prev => prev.filter(n => n.id !== id));
    };

    if (visibleNotifications.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-50 space-y-2">
            {visibleNotifications.map((notification) => (
                <div
                    key={notification.id}
                    className="bg-gray-800 border border-gray-700 rounded-lg shadow-2xl p-4 w-80 animate-slide-in-right"
                >
                    <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                            <h4 className="font-bold text-white mb-1">{notification.title}</h4>
                            <p className="text-gray-300 text-sm">{notification.message}</p>
                        </div>
                        <button
                            onClick={() => removeNotification(notification.id)}
                            className="text-gray-400 hover:text-white flex-shrink-0"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
};
