from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import datetime
from ..database import get_db
from ..models import User, Reward, Purchase, Item, UserItem
from ..auth import get_current_user

router = APIRouter(
    tags=["shop"]
)

# ==================== REWARD ENDPOINTS (PREFIX /shop) ====================

class RewardCreate(BaseModel):
    nome: str
    descricao: str
    custo: int
    estoque: int = -1
    imagem_url: Optional[str] = None

class RewardUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    custo: Optional[int] = None
    estoque: Optional[int] = None
    imagem_url: Optional[str] = None

class RewardResponse(BaseModel):
    id: int
    nome: str
    descricao: str
    custo: Optional[int] = 0
    estoque: Optional[int] = -1
    imagem_url: Optional[str]
    escola_id: Optional[int]

    @validator('custo', pre=True, always=True)
    def set_default_custo(cls, v):
        return v if v is not None else 0

    @validator('estoque', pre=True, always=True)
    def set_default_estoque(cls, v):
        return v if v is not None else -1

    @validator('nome', pre=True, always=True)
    def set_default_nome(cls, v):
        return v or "Item sem nome"

    @validator('descricao', pre=True, always=True)
    def set_default_descricao(cls, v):
        return v or ""

    class Config:
        orm_mode = True

import logging

# Configurar logger
logger = logging.getLogger(__name__)

@router.get("/shop/", response_model=List[RewardResponse])
def list_rewards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        query = db.query(Reward)
        
        # Gestores, admins e professores veem todas da escola
        if current_user.escola_id:
            try:
                query = query.filter((Reward.escola_id == current_user.escola_id) | (Reward.escola_id == None))
                rewards = query.all()
            except Exception as e:
                logger.warning(f"Erro ao filtrar por escola (coluna inexistente?): {e}")
                db.rollback()
                rewards = db.query(Reward).all()
        else:
            rewards = query.all()
        valid_rewards = []
        
        for r in rewards:
            try:
                # Tenta converter para o modelo Pydantic para validar
                valid_reward = RewardResponse.from_orm(r)
                valid_rewards.append(valid_reward)
            except Exception as e:
                logger.error(f"Erro ao processar recompensa ID {r.id}: {e}")
                # Continua para o próximo item em vez de quebrar tudo
                continue
                
        return valid_rewards
        
    except Exception as e:
        logger.error(f"Erro fatal ao listar recompensas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar loja")

@router.post("/shop/buy/{item_id}")
def buy_reward(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Reward).filter(Reward.id == item_id).first()
    return db_reward

@router.delete("/shop/items/{item_id}")
def delete_reward(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    db_reward = db.query(Reward).filter(Reward.id == item_id).first()
    if not db_reward:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    db.delete(db_reward)
    db.commit()
    return {"message": "Item removido"}

class PurchaseResponse(BaseModel):
    id: int
    reward_nome: Optional[str]
    reward_descricao: Optional[str]
    reward_imagem_url: Optional[str]
    item_nome: Optional[str]
    custo_pago: int
    data_compra: str
    status: str

    class Config:
        orm_mode = True

@router.get("/shop/purchases", response_model=List[PurchaseResponse])
def get_my_purchases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all purchases for the current user."""
    purchases = db.query(Purchase).filter(Purchase.user_id == current_user.id).order_by(Purchase.data_compra.desc()).all()
    
    return [
        {
            "id": p.id,
            "reward_nome": p.reward.nome if p.reward else None,
            "reward_descricao": p.reward.descricao if p.reward else None,
            "reward_imagem_url": p.reward.imagem_url if p.reward else None,
            "item_nome": p.item.nome if p.item else None,
            "custo_pago": p.custo_pago,
            "data_compra": p.data_compra.strftime("%d/%m/%Y %H:%M"),
            "status": p.status
        }
        for p in purchases
    ]

# ==================== ITEM ENDPOINTS (PREFIX /loja) ====================

@router.post("/loja/comprar/{item_id}")
def comprar_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    if current_user.moedas < item.preco_moedas:
        raise HTTPException(status_code=400, detail="Moedas insuficientes")
    
    current_user.moedas -= item.preco_moedas
    
    # Create pending purchase
    purchase = Purchase(
        user_id=current_user.id,
        item_id=item_id,
        custo_pago=item.preco_moedas,
        status='pendente',
        data_compra=datetime.utcnow()
    )
    db.add(purchase)
    db.commit()
    
    return {"message": "Compra realizada com sucesso!", "purchase_id": purchase.id}

@router.get("/loja/compras/pendentes")
def get_pending_purchases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List pending purchases for manager approval."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem ver compras pendentes")
    
    query = db.query(Purchase).join(User).filter(Purchase.status == 'pendente')
    
    if current_user.papel == 'gestor' and current_user.escola_id:
        query = query.filter(User.escola_id == current_user.escola_id)
        
    purchases = query.all()
    
    result = []
    for p in purchases:
        item_nome = p.item.nome if p.item else None
        reward_nome = p.reward.nome if p.reward else None
        
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "user_nome": p.user.nome,
            "item_id": p.item_id,
            "item_nome": item_nome,
            "reward_id": p.reward_id,
            "reward_nome": reward_nome,
            "custo_pago": p.custo_pago,
            "data_compra": p.data_compra,
            "status": p.status
        })
        
    return result

@router.post("/loja/compras/{compra_id}/aprovar")
def approve_purchase(compra_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Approve a pending purchase."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem aprovar compras")
        
    purchase = db.query(Purchase).filter(Purchase.id == compra_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada")
        
    if purchase.status != 'pendente':
        raise HTTPException(status_code=400, detail="Esta compra não está pendente")
        
    # Verify school permission
    if current_user.papel == 'gestor' and purchase.user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você não pode aprovar compras de outra escola")
        
    # Grant item if it's an inventory item (from lootbox or direct item purchase)
    if purchase.item_id:
        inventario_item = UserItem(user_id=purchase.user_id, item_id=purchase.item_id)
        db.add(inventario_item)
        
    # For Rewards (Shop), we just mark as delivered (manual delivery or just status update)
    # No automatic inventory addition for Rewards as they are not Items
        
    purchase.status = 'entregue'
    db.commit()
    
    return {"message": "Compra aprovada!"}

@router.post("/loja/compras/{compra_id}/rejeitar")
def reject_purchase(compra_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Reject a pending purchase and refund coins."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem rejeitar compras")
        
    purchase = db.query(Purchase).filter(Purchase.id == compra_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada")
        
    if purchase.status != 'pendente':
        raise HTTPException(status_code=400, detail="Esta compra não está pendente")
        
    # Verify school permission
    if current_user.papel == 'gestor' and purchase.user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você não pode rejeitar compras de outra escola")
        
    # Refund coins
    purchase.user.moedas += purchase.custo_pago
    
    # Refund stock if it's a Reward
    if purchase.reward_id and purchase.reward:
        if purchase.reward.estoque != -1: # If not infinite
            purchase.reward.estoque += 1
            
    purchase.status = 'rejeitada' # Or delete? Better keep history
    db.commit()
    
    return {"message": "Compra rejeitada e moedas devolvidas!"}
