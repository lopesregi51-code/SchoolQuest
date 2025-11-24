/**
 * API Configuration
 * Centraliza a configuração da URL base da API
 */

export const API_BASE_URL = 'http://localhost:8000';

// Validar configuração
if (!API_BASE_URL) {
    console.error('VITE_API_URL não está configurada! Usando valor padrão.');
}

export default {
    API_BASE_URL
};
