from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from ..database import get_db
from .. import models, schemas, auth

router = APIRouter(
    prefix="/missoes",
    tags=["missoes"]
)

logger = logging.getLogger(__name__)

class ValidacaoPresencialRequest(BaseModel):
    aluno_id: Optional[int] = None
    qr_token: Optional[str] = None

# ==================== HELPER FUNCTIONS ====================

def calcular_nivel(xp: int) -> int:
    """Calculate level based on XP. Standard formula: 1 + (XP // 100)"""
    return 1 + (xp // 100)

def aplicar_recompensas(aluno: models.User, missao: models.Missao, db: Session):
    """Apply mission rewards to student (XP, coins, level)."""
    if missao.tipo == 'clan':
        # Clan missions give coins to the clan
        clan_member = db.query(models.ClanMember).filter(
            models.ClanMember.user_id == aluno.id
        ).first()
        if clan_member:
            clan_member.clan.moedas += missao.moedas
    else:
        # Individual missions give XP and coins to student
        aluno.xp += missao.pontos
        aluno.moedas += missao.moedas
        
        # Update level if necessary
        novo_nivel = calcular_nivel(aluno.xp)
        if novo_nivel > aluno.nivel:
            aluno.nivel = novo_nivel
            logger.info(f"Student {aluno.nome} leveled up to {novo_nivel}!")

@router.get("/", response_model=List[schemas.MissaoResponse])
def read_missoes(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar todas as missões disponíveis."""
    try:
        if current_user.papel == 'aluno':
            logger.info(f"Fetching missions for student: {current_user.nome} (escola_id: {current_user.escola_id}, serie_id: {current_user.serie_id})")
            
            # Students see missions from their school (individual and turma types)
            missoes = db.query(models.Missao).join(
                models.User, models.Missao.criador_id == models.User.id
            ).filter(
                models.User.escola_id == current_user.escola_id,
                models.Missao.tipo.in_(['individual', 'turma'])
            ).all()
            
            # Filter turma missions - only show if student belongs to that turma
            filtered_missoes = []
            for missao in missoes:
                if missao.tipo == 'turma':
                    # Only include if student's serie_id matches mission's turma_id
                    if missao.turma_id and current_user.serie_id == missao.turma_id:
                        filtered_missoes.append(missao)
                else:
                    # Include all individual missions
                    filtered_missoes.append(missao)
            
            missoes = filtered_missoes
            logger.info(f"Found {len(missoes)} school/turma missions for student {current_user.nome}")
            
            # Add clan missions if student is in a clan
            clan_member = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
            if clan_member:
                clan_missions = db.query(models.Missao).filter(
                    models.Missao.tipo == 'clan',
                    models.Missao.clan_id == clan_member.clan_id
                ).all()
                logger.info(f"Found {len(clan_missions)} clan missions for student {current_user.nome}")
                missoes.extend(clan_missions)
            
            # Add status for each mission
            result = []
            for missao in missoes:
                # Get professor info
                criador = db.query(models.User).filter(models.User.id == missao.criador_id).first()
                
                # Get turma name if applicable
                turma_nome = None
                if missao.tipo == 'turma' and missao.turma_id:
                    serie = db.query(models.Serie).filter(models.Serie.id == missao.turma_id).first()
                    turma_nome = serie.nome if serie else None
                
                missao_dict = {
                    "id": missao.id,
                    "titulo": missao.titulo,
                    "descricao": missao.descricao,
                    "pontos": missao.pontos,
                    "moedas": missao.moedas,
                    "categoria": missao.categoria,
                    "criador_id": missao.criador_id,
                    "criador_nome": criador.nome if criador else None,
                    "criador_disciplina": criador.disciplina if criador else None,
                    "turma_nome": turma_nome,
                    "tipo": missao.tipo,
                    "clan_id": missao.clan_id,
                    "criado_em": missao.criado_em,
                    "status": "disponivel"  # default
                }
                
                # Check if student has completed this mission
                conclusao = db.query(models.MissaoConcluida).filter(
                    models.MissaoConcluida.missao_id == missao.id,
                    models.MissaoConcluida.aluno_id == current_user.id
                ).first()
                
                if conclusao:
                    if conclusao.validada:
                        missao_dict["status"] = "aprovada"
                    else:
                        missao_dict["status"] = "pendente"
                
                result.append(missao_dict)
            
            logger.info(f"Returning {len(result)} missions for student {current_user.nome}")
            return result
        else:
            # Professors and managers see all missions from their school - using JOIN
            logger.info(f"Fetching missions for {current_user.papel}: {current_user.nome} (escola_id: {current_user.escola_id})")
            
            missoes = db.query(models.Missao).join(
                models.User, models.Missao.criador_id == models.User.id
            ).filter(
                models.User.escola_id == current_user.escola_id
            ).all()
            
            logger.info(f"Returning {len(missoes)} missions for {current_user.papel} {current_user.nome}")
            return missoes
    except Exception as e:
        logger.error(f"Error fetching missions for user {current_user.nome}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar missões: {str(e)}")

from ..websocket import manager

@router.post("/", response_model=schemas.MissaoResponse)
async def create_missao(missao: schemas.MissaoCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Criar nova missão."""
    db_missao = models.Missao(**missao.dict(), criador_id=current_user.id)
    db.add(db_missao)
    db.commit()
    db.refresh(db_missao)
    logger.info(f"Mission created: {missao.titulo} by {current_user.nome}")
    
    # Send real-time notification
    try:
        notification = {
            "type": "new_mission",
            "title": "Nova Missão!",
            "message": f"Nova missão disponível: {missao.titulo}",
            "data": {"mission_id": db_missao.id}
        }
        
        if missao.tipo == 'clan' and missao.clan_id:
            await manager.broadcast_to_clan(notification, missao.clan_id, db)
        else:
            # Notify all students from the school
            students = db.query(models.User).filter(
                models.User.escola_id == current_user.escola_id,
                models.User.papel == 'aluno'
            ).all()
            
            for student in students:
                await manager.send_personal_message(notification, student.id)
                
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        # Don't fail the request if notification fails
        
    return db_missao

@router.delete("/{missao_id}")
def delete_missao(missao_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Deletar uma missão (apenas o criador ou gestor)."""
    missao = db.query(models.Missao).filter(models.Missao.id == missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    
    if current_user.papel != 'admin' and current_user.papel != 'gestor' and missao.criador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para excluir esta missão")
    
    db.delete(missao)
    db.commit()
    logger.info(f"Mission deleted: {missao.titulo} by {current_user.nome}")
    return {"message": "Missão excluída com sucesso!"}

@router.post("/{missao_id}/completar")
def completar_missao(missao_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Aluno marca missão como concluída (pendente de validação)."""
    if current_user.papel != 'aluno':
        raise HTTPException(status_code=403, detail="Apenas alunos podem completar missões")
    
    # Validate mission exists and belongs to student's school
    missao = db.query(models.Missao).join(
        models.User, models.Missao.criador_id == models.User.id
    ).filter(
        models.Missao.id == missao_id,
        models.User.escola_id == current_user.escola_id
    ).first()
    
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada ou não pertence à sua escola")
    
    # Validate clan missions
    if missao.tipo == 'clan':
        clan_member = db.query(models.ClanMember).filter(
            models.ClanMember.user_id == current_user.id,
            models.ClanMember.clan_id == missao.clan_id
        ).first()
        if not clan_member:
            raise HTTPException(status_code=403, detail="Você não é membro deste clã")
    
    # Check if already completed
    existing = db.query(models.MissaoConcluida).filter(
        models.MissaoConcluida.missao_id == missao_id,
        models.MissaoConcluida.aluno_id == current_user.id
    ).first()
    
    if existing:
        if existing.validada:
            raise HTTPException(status_code=400, detail="Você já completou esta missão")
        else:
            raise HTTPException(status_code=400, detail="Esta missão já está pendente de validação")
    
    # Create completion record
    conclusao = models.MissaoConcluida(missao_id=missao_id, aluno_id=current_user.id)
    db.add(conclusao)
    
    # Streak Logic
    today = datetime.utcnow().date()
    last_activity = current_user.last_activity_date.date() if current_user.last_activity_date else None
    
    if last_activity != today:
        if last_activity == today - timedelta(days=1):
            current_user.streak_count += 1
        else:
            current_user.streak_count = 1
        current_user.last_activity_date = datetime.utcnow()
        
        if current_user.streak_count % 5 == 0:
            current_user.xp += 50
            
    db.commit()
    logger.info(f"Mission completed: {missao.titulo} by {current_user.nome}")
    return {"message": "Missão enviada para validação!"}

# Specific routes MUST come before parameterized routes
# Otherwise FastAPI will try to match 'pendentes' as a missao_id

@router.get("/pendentes")
def read_missoes_pendentes(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar missões pendentes de validação (para professor)."""
    if current_user.papel not in ['professor', 'gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas professores podem ver missões pendentes")
    
    try:
        logger.info(f"Fetching pending missions for {current_user.papel}: {current_user.nome}")
        
        # Get pending missions for missions created by this professor
        pendentes = db.query(models.MissaoConcluida).join(models.Missao).filter(
            models.MissaoConcluida.validada == False,
            models.Missao.criador_id == current_user.id
        ).all()
        
        logger.info(f"Found {len(pendentes)} pending missions for {current_user.nome}")
        
        resultado = []
        for pendente in pendentes:
            resultado.append({
                "id": pendente.id,
                "missao_id": pendente.missao_id,
                "missao_titulo": pendente.missao.titulo,
                "aluno_id": pendente.aluno_id,
                "aluno_nome": pendente.aluno.nome if pendente.aluno else "Aluno Desconhecido",
                "aluno_serie": (pendente.aluno.serie_nome if pendente.aluno else "Sem série") or "Sem série",
                "data_solicitacao": pendente.data_solicitacao
            })
        
        return resultado
    except Exception as e:
        logger.error(f"Error fetching pending missions for {current_user.nome}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar missões pendentes: {str(e)}")

@router.get("/professor/concluidas")
def read_professor_completed_missions(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar missões concluídas e validadas criadas pelo professor."""
    if current_user.papel not in ['professor', 'gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas professores podem acessar esta rota")
    
    try:
        logger.info(f"Fetching completed missions for {current_user.papel}: {current_user.nome}")
        
        # Get completed missions for missions created by this professor
        completed = db.query(models.MissaoConcluida).join(models.Missao).filter(
            models.Missao.criador_id == current_user.id,
            models.MissaoConcluida.validada == True
        ).all()
        
        logger.info(f"Found {len(completed)} completed missions for {current_user.nome}")
        
        resultado = []
        for conclusao in completed:
            resultado.append({
                "id": conclusao.id,
                "missao_id": conclusao.missao_id,
                "missao_titulo": conclusao.missao.titulo,
                "aluno_id": conclusao.aluno_id,
                "aluno_nome": conclusao.aluno.nome if conclusao.aluno else "Aluno Desconhecido",
                "aluno_serie": (conclusao.aluno.serie_nome if conclusao.aluno else "Sem série") or "Sem série",
                "data_validacao": conclusao.data_validacao,
                "validada": conclusao.validada
            })
        
        return resultado
    except Exception as e:
        logger.error(f"Error fetching completed missions for {current_user.nome}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar missões concluídas: {str(e)}")

@router.get("/recebidas", response_model=List[schemas.MissaoAtribuidaResponse])
def read_missoes_recebidas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar missões atribuídas ao aluno (pendentes de aceite)."""
    if current_user.papel != 'aluno':
        raise HTTPException(status_code=403, detail="Apenas alunos podem ver missões recebidas")
    
    atribuicoes = db.query(models.MissaoAtribuida).filter(
        models.MissaoAtribuida.aluno_id == current_user.id,
        models.MissaoAtribuida.status == 'pendente'
    ).all()
    
    # Populate extra fields for response
    for atrib in atribuicoes:
        atrib.aluno_nome = current_user.nome
        
    return atribuicoes

@router.post("/atribuidas/{id}/aceitar")
def aceitar_missao_atribuida(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Aceitar uma missão atribuída."""
    atribuicao = db.query(models.MissaoAtribuida).filter(
        models.MissaoAtribuida.id == id,
        models.MissaoAtribuida.aluno_id == current_user.id
    ).first()
    
    if not atribuicao:
        raise HTTPException(status_code=404, detail="Atribuição não encontrada")
        
    if atribuicao.status != 'pendente':
        raise HTTPException(status_code=400, detail="Esta missão já foi aceita ou recusada")
        
    atribuicao.status = 'aceita'
    atribuicao.data_resposta = datetime.utcnow()
    db.commit()
    
    return {"message": "Missão aceita com sucesso!"}

@router.post("/atribuidas/{id}/recusar")
def recusar_missao_atribuida(id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Recusar uma missão atribuída."""
    atribuicao = db.query(models.MissaoAtribuida).filter(
        models.MissaoAtribuida.id == id,
        models.MissaoAtribuida.aluno_id == current_user.id
    ).first()
    
    if not atribuicao:
        raise HTTPException(status_code=404, detail="Atribuição não encontrada")
        
    if atribuicao.status != 'pendente':
        raise HTTPException(status_code=400, detail="Esta missão já foi aceita ou recusada")
        
    atribuicao.status = 'recusada'
    atribuicao.data_resposta = datetime.utcnow()
    db.commit()
    
    return {"message": "Missão recusada."}

@router.get("/{missao_id}", response_model=schemas.MissaoResponse)
def get_missao(missao_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get details of a specific mission."""
    missao = db.query(models.Missao).join(
        models.User, models.Missao.criador_id == models.User.id
    ).filter(
        models.Missao.id == missao_id,
        models.User.escola_id == current_user.escola_id
    ).first()
    
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada ou não pertence à sua escola")
    
    return missao



@router.post("/validar/{submissao_id}")
def validar_missao(submissao_id: int, aprovado: bool, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Validate (approve or reject) a completed mission."""
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas professores podem validar missões")
        
    submissao = db.query(models.MissaoConcluida).filter(models.MissaoConcluida.id == submissao_id).first()
    if not submissao:
        raise HTTPException(status_code=404, detail="Submissão não encontrada")
        
    if submissao.validada:
        raise HTTPException(status_code=400, detail="Esta missão já foi validada")
        
    # Mark as validated (reviewed by professor)
    submissao.validada = True
    submissao.validada_por = current_user.id
    submissao.data_validacao = datetime.utcnow()
    
    if aprovado:
        # Apply rewards using helper function
        aplicar_recompensas(submissao.aluno, submissao.missao, db)
        logger.info(f"Mission approved: {submissao.missao.titulo} for {submissao.aluno.nome}")
        message = "Missão aprovada com sucesso!"
    else:
        # Rejected - no rewards, student can resubmit by deleting this record
        logger.info(f"Mission rejected: {submissao.missao.titulo} for {submissao.aluno.nome}")
        # Delete the rejected submission so student can try again
        db.delete(submissao)
        message = "Missão rejeitada. O aluno pode tentar novamente."
        
    db.commit()
    return {"message": message}



@router.post("/{missao_id}/validar_presencial")
def validar_missao_presencial(
    missao_id: int,
    request: ValidacaoPresencialRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Valida uma missão presencialmente para um aluno específico (via QR Code ou ID)."""
    # Verificar permissões (professor criador ou admin/gestor)
    missao = db.query(models.Missao).filter(models.Missao.id == missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
        
    if current_user.papel == 'professor' and missao.criador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode validar suas próprias missões")
        
    if current_user.papel == 'aluno':
        raise HTTPException(status_code=403, detail="Alunos não podem validar missões")

    # Buscar aluno
    aluno = None
    if request.qr_token:
        aluno = db.query(models.User).filter(models.User.qr_token == request.qr_token).first()
    elif request.aluno_id:
        aluno = db.query(models.User).filter(models.User.id == request.aluno_id).first()
        
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Verificar se já completou
    conclusao = db.query(models.MissaoConcluida).filter(
        models.MissaoConcluida.missao_id == missao_id,
        models.MissaoConcluida.aluno_id == aluno.id
    ).first()
    
    if conclusao:
        if conclusao.validada:
            return {"message": "Missão já foi validada para este aluno", "status": "already_validated", "aluno": aluno.nome}
        else:
            # Already submitted but not validated -> Validate now
            conclusao.validada = True
            conclusao.data_validacao = datetime.utcnow()
            conclusao.validada_por = current_user.id
            
            # Apply rewards using helper function
            aplicar_recompensas(aluno, missao, db)
            
            db.commit()
            return {"message": "Missão validada com sucesso!", "status": "validated", "aluno": aluno.nome}
            
    # Create new validated completion
    nova_conclusao = models.MissaoConcluida(
        missao_id=missao_id,
        aluno_id=aluno.id,
        data_solicitacao=datetime.utcnow(),
        validada=True,
        validada_por=current_user.id,
        data_validacao=datetime.utcnow()
    )
    db.add(nova_conclusao)
    
    # Apply rewards using helper function
    aplicar_recompensas(aluno, missao, db)
    
    db.commit()
    
    return {"message": f"Missão validada para {aluno.nome}!", "status": "created_and_validated", "aluno": aluno.nome}

@router.get("/turmas")
def list_turmas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """List all turmas/series from the current user's school."""
    if current_user.papel not in ['professor', 'gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas professores e gestores podem acessar turmas")
    
    # Get all series from the user's school
    logger.info(f"Fetching turmas for user {current_user.nome} (escola_id: {current_user.escola_id})")
    
    series = db.query(models.Serie).filter(
        models.Serie.escola_id == current_user.escola_id
    ).all()
    
    logger.info(f"Found {len(series)} turmas")
    return [{"id": s.id, "nome": s.nome} for s in series]
