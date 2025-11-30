from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter(
    prefix="/clans",
    tags=["clans"]
)

logger = logging.getLogger(__name__)

# ==================== CLAN MANAGEMENT ====================

@router.post("/", response_model=schemas.ClanResponse)
def create_clan(clan: schemas.ClanCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Create a new clan (students only)."""
    if current_user.papel != 'aluno':
        raise HTTPException(status_code=403, detail="Apenas alunos podem criar clãs")
    
    # Check if already in a clan
    existing_membership = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
    if existing_membership:
        raise HTTPException(status_code=400, detail="Você já está em um clã")
        
    # Check unique name
    if db.query(models.Clan).filter(models.Clan.nome == clan.nome, models.Clan.escola_id == current_user.escola_id).first():
        raise HTTPException(status_code=400, detail="Nome de clã já existe nesta escola")
        
    db_clan = models.Clan(
        nome=clan.nome,
        descricao=clan.descricao,
        lider_id=current_user.id,
        escola_id=current_user.escola_id
    )
    db.add(db_clan)
    db.commit()
    db.refresh(db_clan)
    
    # Add leader as member
    member = models.ClanMember(clan_id=db_clan.id, user_id=current_user.id, papel="lider")
    try:
        db.add(member)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating clan member: {e}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar líder ao clã")
    
    logger.info(f"Clan created: {clan.nome} by {current_user.nome}")
    return db_clan

@router.get("/", response_model=List[schemas.ClanResponse])
def read_clans(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """List clans from user's school."""
    try:
        if not current_user.escola_id:
            return []
        clans = db.query(models.Clan).filter(models.Clan.escola_id == current_user.escola_id).all()
        return clans
    except Exception as e:
        logger.error(f"Error fetching clans: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar clãs: {str(e)}")

@router.get("/me", response_model=Optional[schemas.ClanResponse])
def get_my_clan(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get current user's clan."""
    membership = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
    if not membership:
        return None
    return membership.clan

@router.get("/suggestions", response_model=List[schemas.ClanResponse])
def suggest_clans(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Suggest clans from the same school."""
    clans = db.query(models.Clan).filter(
        models.Clan.escola_id == current_user.escola_id
    ).limit(5).all()
    return clans

@router.get("/{clan_id}/members", response_model=List[schemas.ClanMemberResponse])
def get_clan_members(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get members of a clan."""
    members = db.query(models.ClanMember).filter(models.ClanMember.clan_id == clan_id).all()
    return [
        schemas.ClanMemberResponse(
            id=m.id,
            user_id=m.user_id,
            user_nome=m.user.nome,
            papel=m.papel,
            user_avatar=m.user.avatar_url
        ) for m in members
    ]

@router.get("/{clan_id}/missoes", response_model=List[schemas.MissaoResponse])
def get_clan_missions(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get missions for a clan (members only)."""
    # Check if user is member
    membership = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id,
        models.ClanMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Você não é membro deste clã")

    missoes = db.query(models.Missao).filter(
        models.Missao.tipo == 'clan',
        models.Missao.clan_id == clan_id
    ).all()
    
    return missoes

@router.get("/{clan_id}/missoes/progress", response_model=List[schemas.ClanMissionProgressResponse])
def get_clan_missions_progress(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get mission progress for clan (leader only)."""
    # Check if user is leader
    membership = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id,
        models.ClanMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.papel != 'lider':
        raise HTTPException(status_code=403, detail="Apenas o líder pode ver o progresso das missões")

    # Get clan missions
    missoes = db.query(models.Missao).filter(
        models.Missao.tipo == 'clan',
        models.Missao.clan_id == clan_id
    ).all()
    
    # Get clan members
    members = db.query(models.ClanMember).filter(models.ClanMember.clan_id == clan_id).all()
    
    result = []
    for missao in missoes:
        completed = []
        pending = []
        
        # Get validated completions for this mission
        conclusoes = db.query(models.MissaoConcluida).filter(
            models.MissaoConcluida.missao_id == missao.id,
            models.MissaoConcluida.validada == True
        ).all()
        completed_ids = [c.aluno_id for c in conclusoes]
        
        for member in members:
            member_response = schemas.ClanMemberResponse(
                id=member.id,
                user_id=member.user_id,
                user_nome=member.user.nome,
                papel=member.papel,
                user_avatar=member.user.avatar_url
            )
            if member.user_id in completed_ids:
                completed.append(member_response)
            else:
                pending.append(member_response)
                
        result.append({
            "mission": missao,
            "completed_by": completed,
            "pending_by": pending
        })
        
    return result

@router.delete("/{clan_id}")
def delete_clan(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Delete a clan (leader, admin, or manager only)."""
    clan = db.query(models.Clan).filter(models.Clan.id == clan_id).first()
    if not clan:
        raise HTTPException(status_code=404, detail="Clã não encontrado")
        
    if current_user.papel not in ['admin', 'gestor'] and clan.lider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    db.delete(clan)
    db.commit()
    return {"message": "Clã excluído"}

# ==================== CLAN INVITES ====================

@router.post("/invite")
def invite_to_clan(email: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Invite a user to join clan (leader only)."""
    # Check if is leader
    membership = db.query(models.ClanMember).filter(
        models.ClanMember.user_id == current_user.id,
        models.ClanMember.papel == 'lider'
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Apenas o líder pode convidar")
        
    target_user = db.query(models.User).filter(models.User.email == email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    if target_user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=400, detail="Usuário deve ser da mesma escola")
        
    # Check if already in clan
    if db.query(models.ClanMember).filter(models.ClanMember.user_id == target_user.id).first():
        raise HTTPException(status_code=400, detail="Usuário já está em um clã")
        
    # Create invite
    invite = models.ClanInvite(
        clan_id=membership.clan_id,
        destinatario_email=email
    )
    db.add(invite)
    db.commit()
    return {"message": f"Convite enviado para {email}"}

@router.get("/invites/my", response_model=List[schemas.ClanInviteResponse])
def get_my_invites(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get pending invites for current user."""
    invites = db.query(models.ClanInvite).filter(
        models.ClanInvite.destinatario_email == current_user.email,
        models.ClanInvite.status == 'pendente'
    ).all()
    
    return [
        schemas.ClanInviteResponse(
            id=inv.id,
            clan_id=inv.clan_id,
            clan_nome=inv.clan.nome,
            status=inv.status,
            criado_em=inv.criado_em
        ) for inv in invites
    ]

@router.post("/invites/{invite_id}/accept")
def accept_invite(invite_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Accept a clan invite."""
    invite = db.query(models.ClanInvite).filter(models.ClanInvite.id == invite_id).first()
    if not invite or invite.destinatario_email != current_user.email:
        raise HTTPException(status_code=404, detail="Convite não encontrado")
        
    if invite.status != 'pendente':
        raise HTTPException(status_code=400, detail="Convite inválido")
        
    # Check again if already has clan
    if db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Você já está em um clã")
        
    # Accept
    invite.status = 'aceito'
    member = models.ClanMember(clan_id=invite.clan_id, user_id=current_user.id)
    db.add(member)
    db.commit()
    return {"message": f"Bem-vindo ao clã {invite.clan.nome}!"}

@router.post("/leave")
def leave_clan(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Leave current clan."""
    membership = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="Você não está em um clã")
        
    if membership.papel == 'lider':
        # If leader, check if there are other members
        members_count = db.query(models.ClanMember).filter(models.ClanMember.clan_id == membership.clan_id).count()
        if members_count > 1:
            raise HTTPException(status_code=400, detail="Líder não pode sair sem passar a liderança ou remover todos os membros")
        else:
            # Delete clan
            db.delete(membership.clan)
    else:
        db.delete(membership)
    db.commit()
    return {"message": "Você saiu do clã"}
