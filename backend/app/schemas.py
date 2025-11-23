from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EscolaBase(BaseModel):
    nome: str

class EscolaCreate(EscolaBase):
    pass

class EscolaResponse(EscolaBase):
    id: int
    criado_em: datetime
    
    class Config:
        orm_mode = True

class SerieBase(BaseModel):
    nome: str

class SerieCreate(SerieBase):
    pass

class SerieUpdate(SerieBase):
    pass

class SerieResponse(SerieBase):
    id: int
    escola_id: int
    criado_em: datetime
    
    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    nome: str
    papel: str = "aluno"
    serie_id: Optional[int] = None
    disciplina: Optional[str] = None
    escola_id: Optional[int] = None
    bio: Optional[str] = None
    interesses: Optional[str] = None

class UserCreate(UserBase):
    senha: str

class UserResponse(UserBase):
    id: int
    pontos: int
    moedas: int
    xp: int
    nivel: int
    streak_count: int = 0
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    interesses: Optional[str] = None
    escola_nome: Optional[str] = None
    serie_nome: Optional[str] = None
    
    class Config:
        orm_mode = True

class MissaoBase(BaseModel):
    titulo: str
    descricao: str
    pontos: int
    moedas: int
    categoria: str

class MissaoCreate(MissaoBase):
    turma_id: Optional[int] = None

class MissaoResponse(MissaoBase):
    id: int
    criador_id: int
    status: Optional[str] = "disponivel"
    criado_em: datetime
    
    class Config:
        orm_mode = True

class MissaoAtribuidaBase(BaseModel):
    missao_id: int
    aluno_id: int

class MissaoAtribuidaCreate(MissaoAtribuidaBase):
    pass

class MissaoAtribuidaResponse(MissaoAtribuidaBase):
    id: int
    status: str
    data_atribuicao: datetime
    data_resposta: Optional[datetime] = None
    missao: Optional[MissaoResponse] = None
    aluno_nome: Optional[str] = None
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ItemBase(BaseModel):
    nome: str
    descricao: str
    raridade: str
    tipo: str
    imagem_url: Optional[str] = None
    preco_moedas: int = 0

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int
    
    class Config:
        orm_mode = True

class UserItemResponse(BaseModel):
    id: int
    item: ItemResponse
    equipado: bool
    data_obtencao: datetime
    
    class Config:
        orm_mode = True

class ConquistaBase(BaseModel):
    titulo: str
    descricao: str
    xp_bonus: int

class ConquistaResponse(ConquistaBase):
    id: int
    secreta: bool
    
    class Config:
        orm_mode = True

# --- Clan Schemas ---

class ClanBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class ClanCreate(ClanBase):
    pass

class ClanResponse(ClanBase):
    id: int
    lider_id: int
    escola_id: int
    criado_em: datetime
    
    class Config:
        orm_mode = True

class ClanMemberResponse(BaseModel):
    id: int
    user_id: int
    user_nome: str
    papel: str
    user_avatar: Optional[str] = None
    
    class Config:
        orm_mode = True

class ClanInviteResponse(BaseModel):
    id: int
    clan_id: int
    clan_nome: str
    status: str
    criado_em: datetime
    
    class Config:
        orm_mode = True

# --- Mural Schemas ---

class MuralPostBase(BaseModel):
    conteudo: str
    imagem_url: Optional[str] = None

class MuralPostCreate(MuralPostBase):
    pass

class MuralPostResponse(MuralPostBase):
    id: int
    user_id: int
    user_nome: str
    user_avatar: Optional[str] = None
    likes: int
    criado_em: datetime
    liked_by_me: bool = False

    class Config:
        orm_mode = True
