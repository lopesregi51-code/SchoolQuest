from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/school/overview")
async def get_school_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(403, "Acesso negado")
    
    escola_id = current_user.escola_id
    
    # Total de alunos
    total_students = db.query(models.User).filter(
        models.User.escola_id == escola_id,
        models.User.papel == 'aluno'
    ).count()
    
    # Total de missões criadas
    total_missions = db.query(models.Missao).join(
        models.User, models.Missao.criador_id == models.User.id
    ).filter(
        models.User.escola_id == escola_id
    ).count()
    
    # Missões completadas este mês
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    missions_this_month = db.query(models.MissaoConcluida).join(
        models.User, models.MissaoConcluida.aluno_id == models.User.id
    ).filter(
        models.User.escola_id == escola_id,
        models.MissaoConcluida.data_validacao >= start_of_month,
        models.MissaoConcluida.validada == True
    ).count()
    
    # Média de XP por aluno
    avg_xp = db.query(func.avg(models.User.xp)).filter(
        models.User.escola_id == escola_id,
        models.User.papel == 'aluno'
    ).scalar() or 0
    
    # Top 10 alunos
    top_students = db.query(models.User).filter(
        models.User.escola_id == escola_id,
        models.User.papel == 'aluno'
    ).order_by(models.User.xp.desc()).limit(10).all()
    
    return {
        "total_students": total_students,
        "total_missions": total_missions,
        "missions_this_month": missions_this_month,
        "avg_xp": round(avg_xp, 2),
        "top_students": [
            {"nome": s.nome, "xp": s.xp, "nivel": s.nivel}
            for s in top_students
        ]
    }

@router.get("/school/activity-timeline")
async def get_activity_timeline(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Atividade diária dos últimos N dias"""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(403, "Acesso negado")
    
    start_date = datetime.now() - timedelta(days=days)
    escola_id = current_user.escola_id
    
    # Missões completadas por dia
    daily_missions = db.query(
        func.date(models.MissaoConcluida.data_validacao).label('date'),
        func.count(models.MissaoConcluida.id).label('count')
    ).join(
        models.User, models.MissaoConcluida.aluno_id == models.User.id
    ).filter(
        models.User.escola_id == escola_id,
        models.MissaoConcluida.data_validacao >= start_date,
        models.MissaoConcluida.validada == True
    ).group_by(func.date(models.MissaoConcluida.data_validacao)).all()
    
    return [
        {"date": str(item.date), "missions": item.count}
        for item in daily_missions
    ]

@router.get("/school/category-distribution")
async def get_category_distribution(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Distribuição de missões por categoria"""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(403, "Acesso negado")
    
    escola_id = current_user.escola_id
    
    distribution = db.query(
        models.Missao.categoria,
        func.count(models.Missao.id).label('count')
    ).join(
        models.User, models.Missao.criador_id == models.User.id
    ).filter(
        models.User.escola_id == escola_id
    ).group_by(models.Missao.categoria).all()
    
    return [
        {"categoria": item.categoria, "count": item.count}
        for item in distribution
    ]
