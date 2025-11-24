from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/school/overview")
async def get_school_overview(
    escola_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(403, "Acesso negado")
    
    # Logic for school filtering
    # Logic for school filtering
    target_escola_id = None
    if current_user.papel == 'gestor':
        target_escola_id = current_user.escola_id
    elif current_user.papel == 'admin':
        target_escola_id = escola_id
    
    # Base query filter
    # If target_escola_id is None (e.g. admin without school), we might want to show ALL data?
    # But the queries rely on filtering by school.
    # Let's assume for now admin MUST provide school_id or we use their own.
    
    if not target_escola_id and current_user.papel == 'admin':
         # If admin has no school and didn't provide one, maybe return empty or global?
         # Let's proceed with target_escola_id. If it's None, queries will filter by None.
         pass

    # Total de alunos
    query_students = db.query(models.User).filter(models.User.papel == 'aluno')
    if target_escola_id:
        query_students = query_students.filter(models.User.escola_id == target_escola_id)
    total_students = query_students.count()
    
    # Total de missões criadas
    query_missions = db.query(models.Missao).join(
        models.User, models.Missao.criador_id == models.User.id
    )
    if target_escola_id:
        query_missions = query_missions.filter(models.User.escola_id == target_escola_id)
    total_missions = query_missions.count()
    
    # Missões completadas este mês
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    query_completed = db.query(models.MissaoConcluida).join(
        models.User, models.MissaoConcluida.aluno_id == models.User.id
    ).filter(
        models.MissaoConcluida.data_validacao >= start_of_month,
        models.MissaoConcluida.validada == True
    )
    if target_escola_id:
        query_completed = query_completed.filter(models.User.escola_id == target_escola_id)
    missions_this_month = query_completed.count()
    
    # Média de XP por aluno
    query_avg = db.query(func.avg(models.User.xp)).filter(models.User.papel == 'aluno')
    if target_escola_id:
        query_avg = query_avg.filter(models.User.escola_id == target_escola_id)
    avg_xp = query_avg.scalar() or 0
    
    # Top 10 alunos
    query_top = db.query(models.User).filter(models.User.papel == 'aluno')
    if target_escola_id:
        query_top = query_top.filter(models.User.escola_id == target_escola_id)
    top_students = query_top.order_by(models.User.xp.desc()).limit(10).all()
    
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
    escola_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Atividade diária dos últimos N dias"""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(403, "Acesso negado")
    
    start_date = datetime.now() - timedelta(days=days)
    
    target_escola_id = None
    if current_user.papel == 'gestor':
        target_escola_id = current_user.escola_id
    elif current_user.papel == 'admin':
        target_escola_id = escola_id
    
    # Missões completadas por dia
    query = db.query(
        func.date(models.MissaoConcluida.data_validacao).label('date'),
        func.count(models.MissaoConcluida.id).label('count')
    ).join(
        models.User, models.MissaoConcluida.aluno_id == models.User.id
    ).filter(
        models.MissaoConcluida.data_validacao >= start_date,
        models.MissaoConcluida.validada == True
    )
    
    if target_escola_id:
        query = query.filter(models.User.escola_id == target_escola_id)
        
    daily_missions = query.group_by(func.date(models.MissaoConcluida.data_validacao)).all()
    
    return [
        {"date": str(item.date), "missions": item.count}
        for item in daily_missions
    ]

@router.get("/school/category-distribution")
async def get_category_distribution(
    escola_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Distribuição de missões por categoria"""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(403, "Acesso negado")
    
    target_escola_id = None
    if current_user.papel == 'gestor':
        target_escola_id = current_user.escola_id
    elif current_user.papel == 'admin':
        target_escola_id = escola_id
    
    query = db.query(
        models.Missao.categoria,
        func.count(models.Missao.id).label('count')
    ).join(
        models.User, models.Missao.criador_id == models.User.id
    )
    
    if target_escola_id:
        query = query.filter(models.User.escola_id == target_escola_id)
        
    distribution = query.group_by(models.Missao.categoria).all()
    
    return [
        {"categoria": item.categoria, "count": item.count}
        for item in distribution
    ]
