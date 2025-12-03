import React, { useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { X } from 'lucide-react';

interface QrCodeScannerProps {
    isOpen: boolean;
    missionId: number | null;
    onClose: () => void;
    onScan: (qrData: string) => void;
}

export const QrCodeScanner: React.FC<QrCodeScannerProps> = ({
    isOpen,
    missionId,
    onClose,
    onScan
}) => {
    const html5QrCodeRef = useRef<Html5Qrcode | null>(null);

    useEffect(() => {
        if (isOpen && missionId) {
            startScanner();
        }

        return () => {
            stopScanner();
        };
    }, [isOpen, missionId]);

    const startScanner = async () => {
        try {
            if (!html5QrCodeRef.current) {
                html5QrCodeRef.current = new Html5Qrcode("qr-reader");
            }

            if (html5QrCodeRef.current.isScanning) {
                await html5QrCodeRef.current.stop();
            }

            await html5QrCodeRef.current.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: 250 },
                (decodedText) => {
                    onScan(decodedText);
                    stopScanner();
                },
                () => {
                    // Silently ignore scan errors
                }
            );
        } catch (error) {
            console.error("Erro ao iniciar scanner:", error);
        }
    };

    const stopScanner = async () => {
        try {
            if (html5QrCodeRef.current?.isScanning) {
                await html5QrCodeRef.current.stop();
            }
        } catch (error) {
            console.error("Erro ao parar scanner:", error);
        }
    };

    const handleClose = () => {
        stopScanner();
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full border border-gray-700">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold">Escanear QR Code</h3>
                    <button
                        onClick={handleClose}
                        className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
                <div id="qr-reader" className="rounded-lg overflow-hidden"></div>
                <p className="text-sm text-gray-400 mt-4 text-center">
                    Aponte a câmera para o QR Code do aluno
                </p>
            </div>
        </div>
    );
};
