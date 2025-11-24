from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from .. import models

router = APIRouter(prefix="/api/mobile/v1", tags=["mobile"])


# Schemas otimizados para mobile
class MobileUserResponse(BaseModel):
    id: int
    nome: str
    email: str
    papel: str
    xp: int
    nivel: int
    moedas: int
    avatar_url: Optional[str]
    streak_count: int
    escola_id: Optional[int]
    serie_id: Optional[int]
    
    class Config:
        from_attributes = True


class MobileMissionResponse(BaseModel):
    id: int
    titulo: str
    descricao: str
    pontos: int
    moedas: int
    categoria: str
    data_limite: Optional[datetime]
    status: str  # disponivel, pendente, aprovada
    
    class Config:
        from_attributes = True


class DeviceTokenRequest(BaseModel):
    device_token: str
    platform: str  # ios, android


class MobileStatsResponse(BaseModel):
    total_xp: int
    nivel: int
    moedas: int
    missoes_concluidas: int
    streak_count: int
    ranking_posicao: Optional[int]
    clan_nome: Optional[str]


@router.get("/me", response_model=MobileUserResponse)
async def get_mobile_profile(
    current_user: models.User = Depends(get_current_user)
):
    """Retorna perfil do usuário otimizado para mobile"""
    return current_user


@router.get("/stats", response_model=MobileStatsResponse)
async def get_mobile_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna estatísticas do usuário para dashboard mobile"""
    
    # Contar missões concluídas
    missoes_concluidas = db.query(models.MissaoConcluida).filter(
        models.MissaoConcluida.aluno_id == current_user.id,
        models.MissaoConcluida.validada == True
    ).count()
    
    # Buscar clã
    clan_member = db.query(models.ClanMember).filter(
        models.ClanMember.user_id == current_user.id
    ).first()
    clan_nome = clan_member.clan.nome if clan_member else None
    
    # Calcular ranking (simplificado)
    if current_user.escola_id:
        users_above = db.query(models.User).filter(
            models.User.escola_id == current_user.escola_id,
            models.User.xp > current_user.xp
        ).count()
        ranking_posicao = users_above + 1
    else:
        ranking_posicao = None
    
    return MobileStatsResponse(
        total_xp=current_user.xp,
        nivel=current_user.nivel,
        moedas=current_user.moedas,
        missoes_concluidas=missoes_concluidas,
        streak_count=current_user.streak_count,
        ranking_posicao=ranking_posicao,
        clan_nome=clan_nome
    )


@router.get("/missions", response_model=List[MobileMissionResponse])
async def get_mobile_missions(
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna missões disponíveis otimizadas para mobile"""
    
    missoes = db.query(models.Missao).limit(limit).all()
    
    resultado = []
    for missao in missoes:
        # Determinar status
        status_missao = "disponivel"
        conclusao = db.query(models.MissaoConcluida).filter_by(
            missao_id=missao.id,
            aluno_id=current_user.id
        ).first()
        
        if conclusao:
            status_missao = "aprovada" if conclusao.validada else "pendente"
        
        resultado.append(MobileMissionResponse(
            id=missao.id,
            titulo=missao.titulo,
            descricao=missao.descricao,
            pontos=missao.pontos,
            moedas=missao.moedas,
            categoria=missao.categoria,
            data_limite=missao.data_limite,
            status=status_missao
        ))
    
    return resultado


@router.post("/missions/{mission_id}/complete")
async def complete_mobile_mission(
    mission_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca missão como concluída (versão mobile)"""
    
    missao = db.query(models.Missao).filter(models.Missao.id == mission_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    
    # Verificar se já concluiu
    existente = db.query(models.MissaoConcluida).filter_by(
        missao_id=mission_id,
        aluno_id=current_user.id
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="Missão já enviada para validação")
    
    # Criar conclusão
    conclusao = models.MissaoConcluida(
        missao_id=mission_id,
        aluno_id=current_user.id
    )
    db.add(conclusao)
    db.commit()
    
    return {
        "success": True,
        "message": "Missão enviada para validação!",
        "xp_pendente": missao.pontos,
        "moedas_pendentes": missao.moedas
    }


@router.post("/device-token")
async def register_device_token(
    token_data: DeviceTokenRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra token do dispositivo para push notifications"""
    
    # Verificar se já existe
    existing = db.query(models.DeviceToken).filter(
        models.DeviceToken.user_id == current_user.id,
        models.DeviceToken.device_token == token_data.device_token
    ).first()
    
    if existing:
        existing.updated_at = datetime.utcnow()
        existing.active = True
    else:
        device_token = models.DeviceToken(
            user_id=current_user.id,
            device_token=token_data.device_token,
            platform=token_data.platform
        )
        db.add(device_token)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Token registrado com sucesso"
    }


@router.delete("/device-token")
async def unregister_device_token(
    device_token: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove token do dispositivo"""
    
    token = db.query(models.DeviceToken).filter(
        models.DeviceToken.user_id == current_user.id,
        models.DeviceToken.device_token == device_token
    ).first()
    
    if token:
        token.active = False
        db.commit()
    
    return {"success": True, "message": "Token removido"}


@router.get("/ranking")
async def get_mobile_ranking(
    limit: int = 10,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna ranking da escola (versão mobile otimizada)"""
    
    if not current_user.escola_id:
        return {"ranking": [], "user_position": None}
    
    # Top usuários
    top_users = db.query(models.User).filter(
        models.User.escola_id == current_user.escola_id
    ).order_by(models.User.xp.desc()).limit(limit).all()
    
    ranking = []
    user_position = None
    
    for idx, user in enumerate(top_users, 1):
        ranking.append({
            "posicao": idx,
            "nome": user.nome,
            "xp": user.xp,
            "nivel": user.nivel,
            "avatar_url": user.avatar_url,
            "is_current_user": user.id == current_user.id
        })
        
        if user.id == current_user.id:
            user_position = idx
    
    # Se usuário não está no top, buscar posição
    if user_position is None:
        users_above = db.query(models.User).filter(
            models.User.escola_id == current_user.escola_id,
            models.User.xp > current_user.xp
        ).count()
        user_position = users_above + 1
    
    return {
        "ranking": ranking,
        "user_position": user_position,
        "total_users": db.query(models.User).filter(
            models.User.escola_id == current_user.escola_id
        ).count()
    }


@router.get("/health")
async def mobile_health_check():
    """Health check para mobile API"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
