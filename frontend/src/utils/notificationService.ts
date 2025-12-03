import apiClient from '../api/client';

export class NotificationService {
    private static publicKey: string | null = null;

    static async init() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push notifications not supported');
            return false;
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            console.log('Service Worker is ready:', registration);
            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }

    static async getPublicKey(): Promise<string> {
        if (this.publicKey) return this.publicKey;

        try {
            const response = await apiClient.get('/notifications/vapid_public_key');
            this.publicKey = response.data.publicKey;
            return this.publicKey;
        } catch (error) {
            console.error('Failed to get VAPID public key:', error);
            throw error;
        }
    }

    static urlBase64ToUint8Array(base64String: string): Uint8Array {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    static async subscribe(): Promise<boolean> {
        try {
            const registration = await navigator.serviceWorker.ready;
            const publicKey = await this.getPublicKey();

            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(publicKey)
            });

            // Send subscription to backend
            await apiClient.post('/notifications/subscribe', subscription.toJSON());

            console.log('Push notification subscription successful');
            return true;
        } catch (error) {
            console.error('Failed to subscribe to push notifications:', error);
            return false;
        }
    }

    static async unsubscribe(): Promise<boolean> {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();

            if (subscription) {
                await subscription.unsubscribe();
                console.log('Unsubscribed from push notifications');
            }

            return true;
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
            return false;
        }
    }

    static async isSubscribed(): Promise<boolean> {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            return subscription !== null;
        } catch {
            return false;
        }
    }

    static async sendTestNotification(): Promise<boolean> {
        try {
            await apiClient.post('/notifications/send_test');
            return true;
        } catch (error) {
            console.error('Failed to send test notification:', error);
            return false;
        }
    }
}
