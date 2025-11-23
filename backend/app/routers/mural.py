from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
from ..database import get_db
from ..models import User, MuralPost, PostLike
from ..auth import get_current_user

router = APIRouter(
    prefix="/mural",
    tags=["mural"]
)

class PostCreate(BaseModel):
    texto: Optional[str] = None

class PostResponse(BaseModel):
    id: int
    user_id: int
    user_nome: str
    escola_id: int
    texto: Optional[str]
    imagem_url: Optional[str]
    data_criacao: str
    likes_count: int
    liked_by_me: bool
    liked_by: List[str]  # Lista de nomes dos usuários que curtiram

    class Config:
        orm_mode = True

@router.get("/", response_model=List[PostResponse])
def get_posts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all posts from the user's school."""
    if not current_user.escola_id:
        return []
    
    posts = db.query(MuralPost).filter(
        MuralPost.escola_id == current_user.escola_id
    ).order_by(MuralPost.data_criacao.desc()).all()
    
    result = []
    for post in posts:
        liked_by_me = any(like.user_id == current_user.id for like in post.likes)
        liked_by_names = [like.user.nome for like in post.likes]
        
        result.append({
            "id": post.id,
            "user_id": post.user_id,
            "user_nome": post.user.nome,
            "escola_id": post.escola_id,
            "texto": post.texto,
            "imagem_url": post.imagem_url,
            "data_criacao": post.data_criacao.strftime("%d/%m/%Y %H:%M"),
            "likes_count": len(post.likes),
            "liked_by_me": liked_by_me,
            "liked_by": liked_by_names
        })
    
    return result

@router.post("/", response_model=PostResponse)
async def create_post(
    texto: Optional[str] = Form(None),
    imagem: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new post on the school wall."""
    """Create a new post on the school wall."""
    if not current_user.escola_id:
        raise HTTPException(status_code=400, detail="Você precisa estar associado a uma escola")
    
    if not texto and not imagem:
        raise HTTPException(status_code=400, detail="Post deve ter texto ou imagem")
    
    imagem_url = None
    if imagem:
        # Save image
        upload_dir = "uploads/mural"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = imagem.filename.split('.')[-1] if imagem.filename and '.' in imagem.filename else 'jpg'
        safe_filename = f"post_{current_user.id}_{int(datetime.now().timestamp())}.{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        contents = await imagem.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        imagem_url = f"/{file_path.replace(os.sep, '/')}"
    
    post = MuralPost(
        user_id=current_user.id,
        escola_id=current_user.escola_id,
        texto=texto,
        imagem_url=imagem_url
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {
        "id": post.id,
        "user_id": post.user_id,
        "user_nome": current_user.nome,
        "escola_id": post.escola_id,
        "texto": post.texto,
        "imagem_url": post.imagem_url,
        "data_criacao": post.data_criacao.strftime("%d/%m/%Y %H:%M"),
        "likes_count": 0,
        "liked_by_me": False,
        "liked_by": []
    }

@router.post("/{post_id}/like")
def toggle_like(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Toggle like on a post (like if not liked, unlike if already liked)."""
    post = db.query(MuralPost).filter(MuralPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    # Check if user already liked
    existing_like = db.query(PostLike).filter(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        return {"message": "Curtida removida", "liked": False, "likes_count": len(post.likes)}
    else:
        # Like
        new_like = PostLike(
            post_id=post_id,
            user_id=current_user.id
        )
        db.add(new_like)
        db.commit()
        db.refresh(post)
        return {"message": "Post curtido!", "liked": True, "likes_count": len(post.likes)}

@router.delete("/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a post (only owner or gestor/admin can delete)."""
    post = db.query(MuralPost).filter(MuralPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    # Only post owner, gestor, or admin can delete
    if post.user_id != current_user.id and current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Você não pode deletar este post")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deletado"}
