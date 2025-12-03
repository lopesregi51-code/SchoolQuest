/* eslint-disable no-undef */
self.addEventListener('push', function (event) {
    const data = event.data ? event.data.json() : {
        title: 'SchoolQuest',
        body: 'Nova notificação!',
        icon: '/pwa-192x192.png'
    };

    const options = {
        body: data.body,
        icon: data.icon || '/pwa-192x192.png',
        badge: '/pwa-192x192.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
