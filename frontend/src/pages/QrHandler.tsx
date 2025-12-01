import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

/**
 * QR Code Handler Page
 * Processes QR code scans and redirects appropriately
 * Format: /qr/:userId/:token
 */
export const QrHandler: React.FC = () => {
    const { userId, token } = useParams<{ userId: string; token: string }>();
    const navigate = useNavigate();

    useEffect(() => {
        // This page is meant to be scanned by professors
        // When a student's QR code is scanned, it opens this URL
        // The professor should be using the in-app scanner instead

        // For now, just show a message
        // In the future, we could auto-validate if the professor is logged in

        console.log('QR Code scanned:', { userId, token });

        // Redirect to login with a message
        setTimeout(() => {
            navigate('/login', {
                state: {
                    message: 'Use o scanner dentro do painel do professor para validar missões.'
                }
            });
        }, 3000);
    }, [userId, token, navigate]);

    return (
        <div className="min-h-screen bg-dark text-white flex items-center justify-center p-6">
            <div className="bg-gray-800 rounded-2xl p-8 max-w-md text-center border border-gray-700">
                <div className="w-16 h-16 bg-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <rect x="3" y="3" width="7" height="7" />
                        <rect x="14" y="3" width="7" height="7" />
                        <rect x="14" y="14" width="7" height="7" />
                        <rect x="3" y="14" width="7" height="7" />
                    </svg>
                </div>
                <h1 className="text-2xl font-bold mb-2">QR Code Detectado</h1>
                <p className="text-gray-400 mb-4">
                    Este QR Code pertence a um aluno do SchoolQuest.
                </p>
                <p className="text-sm text-gray-500">
                    Para validar missões, use o scanner dentro do painel do professor.
                </p>
                <div className="mt-6 text-xs text-gray-600">
                    Redirecionando...
                </div>
            </div>
        </div>
    );
};
