import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export interface Notification {
    id: string;
    type: string;
    title: string;
    message: string;
    data?: any;
    timestamp: Date;
    read: boolean;
}

export const useWebSocket = () => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        if (!user) return;

        // Determinar URL do WebSocket baseado no ambiente
        const wsUrl = process.env.NODE_ENV === 'production'
            ? `wss://${window.location.host}/ws/${user.id}`
            : `ws://localhost:8000/ws/${user.id}`;

        const websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('WebSocket connected');
            setIsConnected(true);

            // Enviar heartbeat a cada 30 segundos
            const heartbeat = setInterval(() => {
                if (websocket.readyState === WebSocket.OPEN) {
                    websocket.send('ping');
                }
            }, 30000);

            // Limpar interval ao desconectar
            websocket.onclose = () => {
                clearInterval(heartbeat);
                setIsConnected(false);
            };
        };

        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Ignorar pongs
                if (data.type === 'pong') return;

                // Criar notificação
                const notification: Notification = {
                    id: Date.now().toString(),
                    type: data.type,
                    title: data.title,
                    message: data.message,
                    data: data.data,
                    timestamp: new Date(),
                    read: false
                };

                setNotifications(prev => [notification, ...prev]);

                // Mostrar notificação do navegador se permitido
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification(data.title, {
                        body: data.message,
                        icon: '/logo.png'
                    });
                }

                // Tocar som de notificação
                const audio = new Audio('/notification.mp3');
                audio.play().catch(() => { });

            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        setWs(websocket);

        return () => {
            websocket.close();
        };
    }, [user]);

    const markAsRead = useCallback((notificationId: string) => {
        setNotifications(prev =>
            prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        );
    }, []);

    const markAllAsRead = useCallback(() => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    }, []);

    const clearNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    const requestPermission = useCallback(async () => {
        if ('Notification' in window && Notification.permission === 'default') {
            await Notification.requestPermission();
        }
    }, []);

    return {
        notifications,
        ws,
        isConnected,
        markAsRead,
        markAllAsRead,
        clearNotifications,
        requestPermission,
        unreadCount: notifications.filter(n => !n.read).length
    };
};
