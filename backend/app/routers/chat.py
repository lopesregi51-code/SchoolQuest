from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_user
from .. import models
from ..websocket import manager, NotificationType

router = APIRouter(prefix="/chat", tags=["chat"])


class MessageCreate(BaseModel):
    message: str


class MessageResponse(BaseModel):
    id: int
    clan_id: int
    user_id: int
    user_name: str
    user_avatar: str | None
    message: str
    created_at: datetime
    edited: bool
    
    class Config:
        from_attributes = True


@router.get("/clan/{clan_id}/messages", response_model=List[MessageResponse])
async def get_clan_messages(
    clan_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Busca mensagens do chat do clã"""
    # Verificar se usuário é membro do clã
    member = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id,
        models.ClanMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Você não é membro deste clã")
    
    # Buscar mensagens
    messages = db.query(models.ClanMessage).filter(
        models.ClanMessage.clan_id == clan_id
    ).order_by(models.ClanMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    # Formatar resposta
    result = []
    for msg in reversed(messages):  # Reverter para ordem cronológica
        result.append(MessageResponse(
            id=msg.id,
            clan_id=msg.clan_id,
            user_id=msg.user_id,
            user_name=msg.user.nome,
            user_avatar=msg.user.avatar_url,
            message=msg.message,
            created_at=msg.created_at,
            edited=msg.edited
        ))
    
    return result


@router.post("/clan/{clan_id}/messages", response_model=MessageResponse)
async def send_clan_message(
    clan_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Envia uma mensagem no chat do clã"""
    # Verificar se usuário é membro do clã
    member = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id,
        models.ClanMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Você não é membro deste clã")
    
    # Validar mensagem
    if not message_data.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
    
    if len(message_data.message) > 1000:
        raise HTTPException(status_code=400, detail="Mensagem muito longa (máximo 1000 caracteres)")
    
    # Criar mensagem
    new_message = models.ClanMessage(
        clan_id=clan_id,
        user_id=current_user.id,
        message=message_data.message.strip()
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Enviar via WebSocket para todos os membros do clã
    members = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id
    ).all()
    
    notification_data = {
        "type": NotificationType.CLAN_MESSAGE,
        "title": f"Nova mensagem em {member.clan.nome}",
        "message": f"{current_user.nome}: {message_data.message[:50]}...",
        "data": {
            "clan_id": clan_id,
            "message_id": new_message.id,
            "user_name": current_user.nome,
            "user_avatar": current_user.avatar_url,
            "message": message_data.message,
            "created_at": new_message.created_at.isoformat()
        }
    }
    
    for m in members:
        # Não enviar notificação para quem enviou a mensagem
        if m.user_id != current_user.id:
            await manager.send_personal_message(notification_data, m.user_id)
    
    return MessageResponse(
        id=new_message.id,
        clan_id=new_message.clan_id,
        user_id=new_message.user_id,
        user_name=current_user.nome,
        user_avatar=current_user.avatar_url,
        message=new_message.message,
        created_at=new_message.created_at,
        edited=new_message.edited
    )


@router.put("/clan/{clan_id}/messages/{message_id}")
async def edit_clan_message(
    clan_id: int,
    message_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Edita uma mensagem do chat (apenas o autor pode editar)"""
    message = db.query(models.ClanMessage).filter(
        models.ClanMessage.id == message_id,
        models.ClanMessage.clan_id == clan_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode editar suas próprias mensagens")
    
    # Validar nova mensagem
    if not message_data.message.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
    
    # Atualizar mensagem
    message.message = message_data.message.strip()
    message.edited = True
    message.edited_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Mensagem editada com sucesso"}


@router.delete("/clan/{clan_id}/messages/{message_id}")
async def delete_clan_message(
    clan_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Deleta uma mensagem do chat (autor ou líder do clã)"""
    message = db.query(models.ClanMessage).filter(
        models.ClanMessage.id == message_id,
        models.ClanMessage.clan_id == clan_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    # Verificar permissão (autor ou líder do clã)
    clan = db.query(models.Clan).filter(models.Clan.id == clan_id).first()
    
    if message.user_id != current_user.id and clan.lider_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Apenas o autor ou líder do clã pode deletar mensagens"
        )
    
    db.delete(message)
    db.commit()
    
    return {"message": "Mensagem deletada com sucesso"}
