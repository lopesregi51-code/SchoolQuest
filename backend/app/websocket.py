from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Gerenciador de conexões WebSocket para notificações em tempo real"""
    
    def __init__(self):
        # Dicionário de user_id -> lista de WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Aceita e registra uma nova conexão WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove uma conexão WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Envia mensagem para um usuário específico"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Remover conexões que falharam
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast_to_school(self, message: dict, escola_id: int, db):
        """Envia mensagem para todos os usuários de uma escola"""
        from .models import User
        users = db.query(User).filter(User.escola_id == escola_id).all()
        for user in users:
            await self.send_personal_message(message, user.id)
    
    async def broadcast_to_clan(self, message: dict, clan_id: int, db):
        """Envia mensagem para todos os membros de um clã"""
        from .models import ClanMember
        members = db.query(ClanMember).filter(ClanMember.clan_id == clan_id).all()
        for member in members:
            await self.send_personal_message(message, member.user_id)
    
    async def broadcast_to_all(self, message: dict):
        """Envia mensagem para todos os usuários conectados"""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)


class NotificationType:
    """Tipos de notificações do sistema"""
    MISSION_ASSIGNED = "mission_assigned"
    MISSION_VALIDATED = "mission_validated"
    MISSION_REJECTED = "mission_rejected"
    CLAN_INVITE = "clan_invite"
    CLAN_MESSAGE = "clan_message"
    NEW_ACHIEVEMENT = "new_achievement"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    DAILY_CHALLENGE = "daily_challenge"
    EVENT_STARTED = "event_started"
    POWERUP_EXPIRED = "powerup_expired"


# Instância global do gerenciador
manager = ConnectionManager()
