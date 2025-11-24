from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Escola(Base):
    __tablename__ = "escolas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    usuarios = relationship("User", back_populates="escola")
    series = relationship("Serie", back_populates="escola", cascade="all, delete-orphan")

class Serie(Base):
    __tablename__ = "series"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    escola_id = Column(Integer, ForeignKey("escolas.id"))
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    escola = relationship("Escola", back_populates="series")
    usuarios = relationship("User", back_populates="serie_obj")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    papel = Column(String) # 'aluno', 'professor', 'gestor', 'admin'
    avatar_url = Column(String, nullable=True)
    
    # Gamification
    pontos = Column(Integer, default=0)
    moedas = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    nivel = Column(Integer, default=1)
    
    turma_id = Column(Integer, nullable=True)
    casa_id = Column(Integer, nullable=True)
    
    # Novos campos
    serie_id = Column(Integer, ForeignKey("series.id"), nullable=True)
    disciplina = Column(String, nullable=True) # Ex: "Matemática" (para professores)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=True)
    
    # Gamification Fields
    bio = Column(String, nullable=True)
    interesses = Column(String, nullable=True)
    streak_count = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    
    escola = relationship("Escola", back_populates="usuarios")
    serie_obj = relationship("Serie", back_populates="usuarios")
    itens = relationship("UserItem", back_populates="user")
    conquistas = relationship("UserConquista", back_populates="user")
    
    criado_em = Column(DateTime, default=datetime.utcnow)

    @property
    def serie_nome(self):
        return self.serie_obj.nome if self.serie_obj else None

class Missao(Base):
    __tablename__ = "missoes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    descricao = Column(String)
    pontos = Column(Integer)
    moedas = Column(Integer, default=0)
    categoria = Column(String) # 'tarefa', 'comportamento', 'evento'
    
    criador_id = Column(Integer, ForeignKey("users.id"))
    turma_id = Column(Integer, nullable=True)
    
    data_limite = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class MissaoConcluida(Base):
    __tablename__ = "missoes_concluidas"
    
    id = Column(Integer, primary_key=True, index=True)
    missao_id = Column(Integer, ForeignKey("missoes.id"))
    aluno_id = Column(Integer, ForeignKey("users.id"))
    data_solicitacao = Column(DateTime, default=datetime.utcnow)
    validada = Column(Boolean, default=False)
    validada_por = Column(Integer, ForeignKey("users.id"), nullable=True)
    data_validacao = Column(DateTime, nullable=True)
    
    missao = relationship("Missao")
    aluno = relationship("User", foreign_keys=[aluno_id])

class MissaoAtribuida(Base):
    __tablename__ = "missoes_atribuidas"
    
    id = Column(Integer, primary_key=True, index=True)
    missao_id = Column(Integer, ForeignKey("missoes.id"))
    aluno_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pendente") # pendente, aceita, recusada
    data_atribuicao = Column(DateTime, default=datetime.utcnow)
    data_resposta = Column(DateTime, nullable=True)
    
    missao = relationship("Missao")
    aluno = relationship("User", foreign_keys=[aluno_id])

class Item(Base):
    __tablename__ = "itens"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String)
    raridade = Column(String) # comum, incomum, raro, epico, lendario
    tipo = Column(String) # avatar, badge, consumivel
    imagem_url = Column(String, nullable=True)
    preco_moedas = Column(Integer, default=0)

class UserItem(Base):
    __tablename__ = "user_itens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("itens.id"))
    data_obtencao = Column(DateTime, default=datetime.utcnow)
    equipado = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="itens")
    item = relationship("Item")

class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tipo = Column(String)  # 'compra', 'lootbox', etc.
    descricao = Column(String)
    moedas = Column(Integer, default=0)
    data = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class Conquista(Base):
    __tablename__ = "conquistas"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    descricao = Column(String)
    secreta = Column(Boolean, default=False)
    criterio = Column(String) # Ex: "streak_5", "xp_1000"
    xp_bonus = Column(Integer, default=0)

class UserConquista(Base):
    __tablename__ = "user_conquistas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    conquista_id = Column(Integer, ForeignKey("conquistas.id"))
    data_conquista = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="conquistas")
    conquista = relationship("Conquista")

class Clan(Base):
    __tablename__ = "clans"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    descricao = Column(String)
    lider_id = Column(Integer, ForeignKey("users.id"))
    criado_em = Column(DateTime, default=datetime.utcnow)
    escola_id = Column(Integer, ForeignKey("escolas.id"))

    lider = relationship("User", foreign_keys=[lider_id])
    membros = relationship("ClanMember", back_populates="clan")
    invites = relationship("ClanInvite", back_populates="clan")

class ClanMember(Base):
    __tablename__ = "clan_members"

    id = Column(Integer, primary_key=True, index=True)
    clan_id = Column(Integer, ForeignKey("clans.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    papel = Column(String, default="membro") # membro, vice_lider
    entrou_em = Column(DateTime, default=datetime.utcnow)

    clan = relationship("Clan", back_populates="membros")
    user = relationship("User")

class ClanInvite(Base):
    __tablename__ = "clan_invites"

    id = Column(Integer, primary_key=True, index=True)
    clan_id = Column(Integer, ForeignKey("clans.id"))
    destinatario_email = Column(String)
    status = Column(String, default="pendente") # pendente, aceito, rejeitado
    criado_em = Column(DateTime, default=datetime.utcnow)

    clan = relationship("Clan", back_populates="invites")



class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    descricao = Column(String)
    custo = Column(Integer) # XP cost by default
    estoque = Column(Integer, default=-1) # -1 for infinite
    imagem_url = Column(String, nullable=True)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    escola = relationship("Escola")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    reward_id = Column(Integer, ForeignKey("rewards.id"))
    data_compra = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pendente") # pendente, entregue, cancelado
    custo_pago = Column(Integer)

    user = relationship("User")
    reward = relationship("Reward")

class MuralPost(Base):
    __tablename__ = "mural_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    escola_id = Column(Integer, ForeignKey("escolas.id"))
    texto = Column(String, nullable=True)
    imagem_url = Column(String, nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    escola = relationship("Escola")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")

class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("mural_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    data_curtida = Column(DateTime, default=datetime.utcnow)

    post = relationship("MuralPost", back_populates="likes")
    user = relationship("User")

class DeviceToken(Base):
    """Modelo para tokens de dispositivos móveis (push notifications)"""
    __tablename__ = "device_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_token = Column(String, unique=True, index=True)
    platform = Column(String)  # ios, android
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class ClanMessage(Base):
    """Modelo para mensagens de chat do clã"""
    __tablename__ = "clan_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    clan_id = Column(Integer, ForeignKey("clans.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    
    clan = relationship("Clan")
    user = relationship("User")

