export interface LevelInfo {
    level: number;
    rankTitle: string;
    rankIcon: string;
    xpCurrent: number;
    xpNextLevel: number;
    progressPercent: number;
    xpForNextLevel: number;
}

export const RANKS = [
    { minLevel: 1, maxLevel: 4, title: 'Novato', icon: '/ranks/rank_novato.png' },
    { minLevel: 5, maxLevel: 9, title: 'Aprendiz', icon: '/ranks/rank_aprendiz.png' },
    { minLevel: 10, maxLevel: 19, title: 'Explorador', icon: '/ranks/rank_explorador.png' },
    { minLevel: 20, maxLevel: 49, title: 'Mestre', icon: '/ranks/rank_mestre.png' },
    { minLevel: 50, maxLevel: 999, title: 'Lenda', icon: '/ranks/rank_lenda.png' },
];

export const getLevelInfo = (xp: number): LevelInfo => {
    const level = 1 + Math.floor(xp / 100);
    const rank = RANKS.find(r => level >= r.minLevel && level <= r.maxLevel) || RANKS[RANKS.length - 1];

    const xpForNextLevel = level * 100;
    const xpCurrentLevelStart = (level - 1) * 100;
    const xpCurrent = xp - xpCurrentLevelStart;
    const xpNeededForLevel = 100;
    const progressPercent = Math.min(100, Math.max(0, (xpCurrent / xpNeededForLevel) * 100));

    return {
        level,
        rankTitle: rank.title,
        rankIcon: rank.icon,
        xpCurrent,
        xpNextLevel: xpForNextLevel,
        progressPercent,
        xpForNextLevel: xpForNextLevel
    };
};
