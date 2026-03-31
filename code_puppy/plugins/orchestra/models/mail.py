"""Mail (inter-agent messaging) models.

Mail enables asynchronous communication between agents.
Inspired by Gastown's mail system.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid


class MailPriority(Enum):
    """Priority levels for mail."""
    URGENT = 0     # Immediate attention required
    HIGH = 1       # Important
    NORMAL = 2     # Standard
    LOW = 3        # FYI


class MailStatus(Enum):
    """Status of a mail message."""
    DRAFT = "draft"           # Being composed
    QUEUED = "queued"         # Ready to send
    SENT = "sent"             # Sent to recipient
    DELIVERED = "delivered"   # In recipient's inbox
    READ = "read"             # Recipient has read
    REPLIED = "replied"       # Recipient replied
    ARCHIVED = "archived"     # Archived


@dataclass
class Mail:
    """An inter-agent mail message.
    
    Mail provides asynchronous communication between agents.
    Unlike real-time chat, mail persists and can be read when
    the recipient is ready.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Routing
    from_agent: str = ""  # Sender agent ID
    to_agent: str = ""    # Recipient agent ID
    cc_agents: List[str] = field(default_factory=list)  # CC recipients
    
    # Content
    subject: str = ""
    body: str = ""
    thread_id: Optional[str] = None  # For message threading
    in_reply_to: Optional[str] = None  # ID of message being replied to
    
    # Context
    bead_id: Optional[str] = None  # Related bead
    convoy_id: Optional[str] = None  # Related convoy
    rig_id: Optional[str] = None  # Related rig
    
    # Status
    status: MailStatus = MailStatus.DRAFT
    priority: MailPriority = MailPriority.NORMAL
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # Delivery tracking
    delivery_attempts: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "cc_agents": self.cc_agents,
            "subject": self.subject,
            "body": self.body,
            "thread_id": self.thread_id,
            "in_reply_to": self.in_reply_to,
            "bead_id": self.bead_id,
            "convoy_id": self.convoy_id,
            "rig_id": self.rig_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "delivery_attempts": self.delivery_attempts,
            "last_error": self.last_error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mail":
        return cls(
            id=data["id"],
            from_agent=data.get("from_agent", ""),
            to_agent=data.get("to_agent", ""),
            cc_agents=data.get("cc_agents", []),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            thread_id=data.get("thread_id"),
            in_reply_to=data.get("in_reply_to"),
            bead_id=data.get("bead_id"),
            convoy_id=data.get("convoy_id"),
            rig_id=data.get("rig_id"),
            status=MailStatus(data.get("status", "draft")),
            priority=MailPriority(data.get("priority", 2)),
            created_at=datetime.fromisoformat(data["created_at"]),
            sent_at=datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None,
            read_at=datetime.fromisoformat(data["read_at"]) if data.get("read_at") else None,
            delivery_attempts=data.get("delivery_attempts", 0),
            last_error=data.get("last_error"),
        )
    
    def send(self) -> None:
        """Mark this mail as sent."""
        self.status = MailStatus.SENT
        self.sent_at = datetime.now()
    
    def mark_read(self) -> None:
        """Mark this mail as read."""
        self.status = MailStatus.READ
        self.read_at = datetime.now()
    
    def reply(self, body: str, from_agent: str) -> "Mail":
        """Create a reply to this mail."""
        return Mail(
            from_agent=from_agent,
            to_agent=self.from_agent,  # Reply to sender
            subject=f"Re: {self.subject}" if not self.subject.startswith("Re: ") else self.subject,
            body=body,
            thread_id=self.thread_id or self.id,
            in_reply_to=self.id,
            bead_id=self.bead_id,
            convoy_id=self.convoy_id,
            rig_id=self.rig_id,
        )
