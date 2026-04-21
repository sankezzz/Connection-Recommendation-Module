from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException

from app.modules.chat.domain.entities import ConversationEntity, ConvStatus, MessageEntity
from app.modules.chat.domain.repository import IChatRepository


class OpenChatUseCase:
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(self, sender_id: UUID, participant_id: UUID, first_message: str) -> tuple[ConversationEntity, MessageEntity, bool]:
        if sender_id == participant_id:
            raise HTTPException(status_code=400, detail="Cannot open a chat with yourself.")

        conv, created = self.repo.get_or_create_dm(sender_id, participant_id)

        if conv.status == ConvStatus.BLOCKED:
            raise HTTPException(status_code=403, detail="This conversation is blocked.")

        message = self.repo.save_message(
            context_type="dm",
            context_id=conv.id,
            sender_id=sender_id,
            body=first_message,
            message_type="text",
        )
        return conv, message, created


class SendMessageUseCase:
    """
    DM send rules:
      requested → only the original initiator can send (receiver must accept first)
      active    → both members can send freely
      blocked   → nobody can send
    """

    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(
        self,
        sender_id: UUID,
        conv_id: UUID,
        body: Optional[str] = None,
        message_type: str = "text",
        media_url: Optional[str] = None,
        media_metadata: Optional[dict] = None,
        location_lat: Optional[float] = None,
        location_lon: Optional[float] = None,
        reply_to_id: Optional[UUID] = None,
    ) -> MessageEntity:
        conv = self.repo.get_conversation(conv_id, sender_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        if conv.status == ConvStatus.BLOCKED:
            raise HTTPException(status_code=403, detail="This conversation is blocked.")

        if conv.status == ConvStatus.REQUESTED:
            # Only the original initiator may send while the request is pending
            if conv.initiator_id is None or sender_id != conv.initiator_id:
                raise HTTPException(
                    status_code=403,
                    detail="Waiting for the other person to accept the chat request.",
                )

        if not self.repo.is_member(conv_id, sender_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation.")

        return self.repo.save_message(
            context_type="dm",
            context_id=conv_id,
            sender_id=sender_id,
            body=body,
            message_type=message_type,
            media_url=media_url,
            media_metadata=media_metadata,
            location_lat=location_lat,
            location_lon=location_lon,
            reply_to_id=reply_to_id,
        )


class AcceptConversationUseCase:
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(self, user_id: UUID, conv_id: UUID) -> ConversationEntity:
        conv = self.repo.get_conversation(conv_id, user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        if conv.status != ConvStatus.REQUESTED:
            raise HTTPException(status_code=409, detail=f"Cannot accept: conversation is already '{conv.status}'.")
        return self.repo.set_conversation_status(conv_id, ConvStatus.ACTIVE)


class DeclineConversationUseCase:
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(self, user_id: UUID, conv_id: UUID) -> ConversationEntity:
        conv = self.repo.get_conversation(conv_id, user_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        if conv.status != ConvStatus.REQUESTED:
            raise HTTPException(status_code=409, detail=f"Cannot decline: conversation is already '{conv.status}'.")
        return self.repo.set_conversation_status(conv_id, ConvStatus.BLOCKED)


class GetConversationsUseCase:
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(self, user_id: UUID, page: int = 1, per_page: int = 20) -> list[ConversationEntity]:
        return self.repo.get_conversations(user_id, page, per_page)


class GetMessagesUseCase:
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(self, user_id: UUID, conv_id: UUID, before: Optional[datetime] = None, limit: int = 50) -> list[MessageEntity]:
        if not self.repo.is_member(conv_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation.")
        return self.repo.get_messages("dm", conv_id, before, min(limit, 100))


class MarkReadUseCase:
    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(self, user_id: UUID, conv_id: UUID) -> None:
        if not self.repo.is_member(conv_id, user_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation.")
        self.repo.mark_read(conv_id, user_id)


class SendGroupMessageUseCase:
    """
    Group chat send rules:
      - Sender must be a group member
      - Sender must not be frozen
      - If chat_perm == 'admins_only', sender must be admin
    """

    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(
        self,
        sender_id: UUID,
        group_id: UUID,
        body: Optional[str] = None,
        message_type: str = "text",
        media_url: Optional[str] = None,
        media_metadata: Optional[dict] = None,
        reply_to_id: Optional[UUID] = None,
    ) -> tuple[MessageEntity, list[UUID]]:
        chat_perm = self.repo.get_group_chat_perm(group_id)
        if chat_perm is None:
            raise HTTPException(status_code=404, detail="Group not found.")

        member_role = self.repo.get_group_member_role(group_id, sender_id)
        if member_role is None:
            raise HTTPException(status_code=403, detail="Not a member of this group.")

        if self.repo.is_group_member_frozen(group_id, sender_id):
            raise HTTPException(status_code=403, detail="You are frozen in this group and cannot send messages.")

        if chat_perm == "admins_only" and member_role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can send messages in this group.")

        message = self.repo.save_message(
            context_type="group",
            context_id=group_id,
            sender_id=sender_id,
            body=body,
            message_type=message_type,
            media_url=media_url,
            media_metadata=media_metadata,
            reply_to_id=reply_to_id,
        )

        # Return member ids so the router can push to all online members
        member_ids = self.repo.get_group_member_ids(group_id)
        return message, member_ids


class GetGroupMessagesUseCase:
    """
    Cursor-based message history for a group chat.
    Sender must be a group member to read.
    """

    def __init__(self, repo: IChatRepository):
        self.repo = repo

    def execute(
        self,
        user_id: UUID,
        group_id: UUID,
        before: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[MessageEntity]:
        member_role = self.repo.get_group_member_role(group_id, user_id)
        if member_role is None:
            raise HTTPException(status_code=403, detail="Not a member of this group.")
        return self.repo.get_messages("group", group_id, before, min(limit, 100))
