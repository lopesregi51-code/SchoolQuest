import React from 'react';
import { BookOpen, Plus } from 'lucide-react';

interface MissionFormData {
    titulo: string;
    descricao: string;
    pontos: number;
    moedas: number;
    categoria: string;
    tipo: string;
    clan_id: string;
    turma_id: string;
}

interface MissionCreationFormProps {
    isCreating: boolean;
    formData: MissionFormData;
    clans: any[];
    turmas: any[];
    onToggleCreate: () => void;
    onFormChange: (data: MissionFormData) => void;
    onSubmit: (e: React.FormEvent) => void;
}

export const MissionCreationForm: React.FC<MissionCreationFormProps> = ({
    isCreating,
    formData,
    clans,
    turmas,
    onToggleCreate,
    onFormChange,
    onSubmit
}) => {
    const handleChange = (field: keyof MissionFormData, value: any) => {
        onFormChange({ ...formData, [field]: value });
    };

    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <BookOpen className="w-6 h-6 text-primary" />
                    Criar Nova Missão
                </h2>
                {!isCreating && (
                    <button
                        onClick={onToggleCreate}
                        className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-blue-600 rounded-lg transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        Nova Missão
                    </button>
                )}
            </div>

            {isCreating && (
                <form onSubmit={onSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="mission-title" className="block text-gray-300 text-sm font-medium mb-2">
                            Título da Missão
                        </label>
                        <input
                            id="mission-title"
                            type="text"
                            value={formData.titulo}
                            onChange={(e) => handleChange('titulo', e.target.value)}
                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                            placeholder="Ex: Resolver 10 exercícios de Matemática"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="mission-description" className="block text-gray-300 text-sm font-medium mb-2">
                            Descrição
                        </label>
                        <textarea
                            id="mission-description"
                            value={formData.descricao}
                            onChange={(e) => handleChange('descricao', e.target.value)}
                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary"
                            rows={3}
                            placeholder="Descreva os detalhes da missão..."
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="mission-points" className="block text-gray-300 text-sm font-medium mb-2">
                                Pontos XP
                            </label>
                            <input
                                id="mission-points"
                                type="number"
                                value={formData.pontos}
                                onChange={(e) => handleChange('pontos', parseInt(e.target.value))}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                min="1"
                                required
                            />
                        </div>
                        <div>
                            <label htmlFor="mission-coins" className="block text-gray-300 text-sm font-medium mb-2">
                                Moedas
                            </label>
                            <input
                                id="mission-coins"
                                type="number"
                                value={formData.moedas}
                                onChange={(e) => handleChange('moedas', parseInt(e.target.value))}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                                min="0"
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="mission-category" className="block text-gray-300 text-sm font-medium mb-2">
                                Categoria
                            </label>
                            <select
                                id="mission-category"
                                value={formData.categoria}
                                onChange={(e) => handleChange('categoria', e.target.value)}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="diaria">Diária</option>
                                <option value="semanal">Semanal</option>
                                <option value="especial">Especial</option>
                            </select>
                        </div>
                        <div>
                            <label htmlFor="mission-type" className="block text-gray-300 text-sm font-medium mb-2">
                                Tipo
                            </label>
                            <select
                                id="mission-type"
                                value={formData.tipo}
                                onChange={(e) => handleChange('tipo', e.target.value)}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="individual">Individual</option>
                                <option value="clan">Clã</option>
                            </select>
                        </div>
                    </div>

                    {formData.tipo === 'clan' && (
                        <div>
                            <label htmlFor="mission-clan" className="block text-gray-300 text-sm font-medium mb-2">
                                Clã
                            </label>
                            <select
                                id="mission-clan"
                                value={formData.clan_id}
                                onChange={(e) => handleChange('clan_id', e.target.value)}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">Selecione um clã</option>
                                {clans.map((clan) => (
                                    <option key={clan.id} value={clan.id}>
                                        {clan.nome}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    <div>
                        <label htmlFor="mission-turma" className="block text-gray-300 text-sm font-medium mb-2">
                            Turma (Opcional)
                        </label>
                        <select
                            id="mission-turma"
                            value={formData.turma_id}
                            onChange={(e) => handleChange('turma_id', e.target.value)}
                            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            <option value="">Todas as turmas</option>
                            {turmas.map((turma) => (
                                <option key={turma.id} value={turma.id}>
                                    {turma.nome}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex gap-3">
                        <button
                            type="submit"
                            className="flex-1 bg-primary hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                        >
                            Criar Missão
                        </button>
                        <button
                            type="button"
                            onClick={onToggleCreate}
                            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                        >
                            Cancelar
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
};
