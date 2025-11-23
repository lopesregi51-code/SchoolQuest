from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..models import User, Reward, Purchase
from ..auth import get_current_user

router = APIRouter(
    prefix="/shop",
    tags=["shop"]
)

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
    custo: int
    estoque: int
    imagem_url: Optional[str]
    escola_id: Optional[int]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[RewardResponse])
def list_rewards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Reward)
    if current_user.escola_id:
        query = query.filter((Reward.escola_id == current_user.escola_id) | (Reward.escola_id == None))
    return query.all()

@router.post("/buy/{item_id}")
def buy_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(Reward).filter(Reward.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    if item.estoque == 0:
        raise HTTPException(status_code=400, detail="Item esgotado")
    
    if current_user.moedas < item.custo:
        raise HTTPException(status_code=400, detail="Moedas insuficientes")
    
    # Process purchase
    current_user.moedas -= item.custo
    if item.estoque > 0:
        item.estoque -= 1
    
    purchase = Purchase(
        user_id=current_user.id,
        reward_id=item.id,
        custo_pago=item.custo,
        status="pendente"
    )
    
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    
    return {"message": "Compra realizada com sucesso!", "purchase_id": purchase.id, "new_moedas": current_user.moedas}

# Manager endpoints
@router.post("/items", response_model=RewardResponse)
def create_reward(reward: RewardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem criar itens")
    
    db_reward = Reward(
        nome=reward.nome,
        descricao=reward.descricao,
        custo=reward.custo,
        estoque=reward.estoque,
        imagem_url=reward.imagem_url,
        escola_id=current_user.escola_id
    )
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

@router.put("/items/{item_id}", response_model=RewardResponse)
def update_reward(item_id: int, reward: RewardUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    db_reward = db.query(Reward).filter(Reward.id == item_id).first()
    if not db_reward:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    if reward.nome: db_reward.nome = reward.nome
    if reward.descricao: db_reward.descricao = reward.descricao
    if reward.custo: db_reward.custo = reward.custo
    if reward.estoque: db_reward.estoque = reward.estoque
    if reward.imagem_url: db_reward.imagem_url = reward.imagem_url
    
    db.commit()
    db.refresh(db_reward)
    return db_reward

@router.delete("/items/{item_id}")
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
    reward_nome: str
    reward_descricao: str
    reward_imagem_url: Optional[str]
    custo_pago: int
    data_compra: str
    status: str

    class Config:
        orm_mode = True

@router.get("/purchases", response_model=List[PurchaseResponse])
def get_my_purchases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all purchases for the current user."""
    purchases = db.query(Purchase).filter(Purchase.user_id == current_user.id).order_by(Purchase.data_compra.desc()).all()
    
    return [
        {
            "id": p.id,
            "reward_nome": p.reward.nome if p.reward else "Item removido",
            "reward_descricao": p.reward.descricao if p.reward else "",
            "reward_imagem_url": p.reward.imagem_url if p.reward else None,
            "custo_pago": p.custo_pago,
            "data_compra": p.data_compra.strftime("%d/%m/%Y %H:%M"),
            "status": p.status
        }
        for p in purchases
    ]
