"""Human-in-the-Loop (HITL) Tool Approval System.

Implements the PAI Agent SDK pattern for requiring human approval
before executing sensitive operations.

Features:
- Tool-level `requires_approval` flag
- Configurable approval strategies
- Timeout handling
- Audit logging
- Integration with existing callbacks system
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"  # YOLO mode


class RiskLevel(str, Enum):
    """Risk level for operations requiring approval."""

    LOW = "low"  # Read operations, safe queries
    MEDIUM = "medium"  # File modifications, command execution
    HIGH = "high"  # Destructive operations, system changes
    CRITICAL = "critical"  # Irreversible operations


@dataclass
class ApprovalRequest:
    """A request for human approval."""

    request_id: str
    tool_name: str
    tool_args: Dict[str, Any]
    risk_level: RiskLevel
    reason: str
    timestamp: float = field(default_factory=time.time)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approval_time: Optional[float] = None
    denial_reason: Optional[str] = None


@dataclass
class ToolApprovalConfig:
    """Configuration for a tool that requires approval."""

    tool_name: str
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.MEDIUM
    approval_message: Optional[str] = None
    allow_yolo_override: bool = True  # Can YOLO mode skip approval?
    timeout_seconds: float = 300.0  # 5 minute default


class ApprovalSettings(BaseModel):
    """Global settings for the approval system."""

    enabled: bool = Field(
        default=True,
        description="Whether approval system is enabled",
    )
    
    yolo_mode: bool = Field(
        default=False,
        description="Auto-approve all requests (dangerous!)",
    )
    
    default_timeout: float = Field(
        default=300.0,
        ge=10.0,
        description="Default timeout for approval requests in seconds",
    )
    
    log_all_requests: bool = Field(
        default=True,
        description="Log all approval requests for audit",
    )
    
    require_reason_for_denial: bool = Field(
        default=False,
        description="Require a reason when denying requests",
    )
    
    auto_approve_tools: List[str] = Field(
        default_factory=list,
        description="Tools that are always auto-approved",
    )
    
    always_require_tools: List[str] = Field(
        default_factory=lambda: [
            "delete_file",
            "run_dangerous_command",
            "modify_system_config",
        ],
        description="Tools that always require approval regardless of YOLO mode",
    )


class ApprovalHandler:
    """Abstract base for approval request handlers."""

    async def request_approval(
        self,
        request: ApprovalRequest,
    ) -> ApprovalStatus:
        """Request approval from the user.
        
        Subclasses implement the actual UI interaction.
        
        Returns:
            ApprovalStatus indicating the result
        """
        raise NotImplementedError


class CLIApprovalHandler(ApprovalHandler):
    """CLI-based approval handler using rich prompts."""

    def __init__(self, timeout: float = 300.0):
        self.timeout = timeout

    async def request_approval(
        self,
        request: ApprovalRequest,
    ) -> ApprovalStatus:
        """Request approval via CLI prompt."""
        from code_puppy.messaging import (
            emit_warning,
            get_message_bus,
        )
        
        # Format the approval message
        risk_emoji = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴",
        }
        
        emoji = risk_emoji.get(request.risk_level, "⚪")
        
        message = f"""
{emoji} **Approval Required** ({request.risk_level.value} risk)

**Tool:** `{request.tool_name}`
**Reason:** {request.reason}

**Arguments:**
```
{self._format_args(request.tool_args)}
```

Approve this operation? [y/n/s(kip all)]: """

        emit_warning(message)
        
        # Use asyncio to handle input with timeout
        try:
            response = await asyncio.wait_for(
                self._get_user_input(),
                timeout=self.timeout,
            )
            
            response = response.strip().lower()
            
            if response in ("y", "yes", "approve"):
                request.status = ApprovalStatus.APPROVED
                request.approval_time = time.time()
                return ApprovalStatus.APPROVED
            elif response in ("s", "skip", "yolo"):
                request.status = ApprovalStatus.SKIPPED
                return ApprovalStatus.SKIPPED
            else:
                request.status = ApprovalStatus.DENIED
                request.denial_reason = response if len(response) > 1 else "User denied"
                return ApprovalStatus.DENIED
                
        except asyncio.TimeoutError:
            request.status = ApprovalStatus.TIMEOUT
            return ApprovalStatus.TIMEOUT

    async def _get_user_input(self) -> str:
        """Get input from user asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input)

    def _format_args(self, args: Dict[str, Any], max_length: int = 500) -> str:
        """Format arguments for display."""
        lines = []
        for key, value in args.items():
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:97] + "..."
            lines.append(f"  {key}: {str_value}")
        
        result = "\n".join(lines)
        if len(result) > max_length:
            result = result[:max_length - 3] + "..."
        return result


class ToolApprovalRegistry:
    """Registry for tools that require approval.
    
    This maintains the mapping of tools to their approval configurations
    and handles the approval workflow.
    """

    def __init__(
        self,
        settings: Optional[ApprovalSettings] = None,
        handler: Optional[ApprovalHandler] = None,
    ):
        self.settings = settings or ApprovalSettings()
        self.handler = handler or CLIApprovalHandler(self.settings.default_timeout)
        self._tool_configs: Dict[str, ToolApprovalConfig] = {}
        self._request_history: List[ApprovalRequest] = []
        self._session_approved: Set[str] = set()  # Tools approved for session
    
    def register_tool(
        self,
        tool_name: str,
        requires_approval: bool = False,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        approval_message: Optional[str] = None,
        allow_yolo_override: bool = True,
    ) -> None:
        """Register a tool with approval configuration.
        
        Args:
            tool_name: Name of the tool
            requires_approval: Whether this tool requires approval
            risk_level: Risk level of the operation
            approval_message: Custom message for approval prompt
            allow_yolo_override: Whether YOLO mode can skip approval
        """
        self._tool_configs[tool_name] = ToolApprovalConfig(
            tool_name=tool_name,
            requires_approval=requires_approval,
            risk_level=risk_level,
            approval_message=approval_message,
            allow_yolo_override=allow_yolo_override,
        )
    
    def requires_approval(self, tool_name: str) -> bool:
        """Check if a tool requires approval."""
        # Check always-require list
        if tool_name in self.settings.always_require_tools:
            return True
        
        # Check auto-approve list
        if tool_name in self.settings.auto_approve_tools:
            return False
        
        # Check session approvals
        if tool_name in self._session_approved:
            return False
        
        # Check registry
        config = self._tool_configs.get(tool_name)
        if config:
            return config.requires_approval
        
        return False
    
    async def request_approval(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        reason: Optional[str] = None,
    ) -> ApprovalStatus:
        """Request approval for a tool execution.
        
        Args:
            tool_name: Name of the tool
            tool_args: Arguments being passed to the tool
            reason: Why this operation is being performed
            
        Returns:
            ApprovalStatus indicating if execution should proceed
        """
        import uuid
        
        # Check if approval is needed
        if not self.settings.enabled:
            return ApprovalStatus.SKIPPED
        
        config = self._tool_configs.get(tool_name, ToolApprovalConfig(tool_name))
        
        # Handle YOLO mode
        if self.settings.yolo_mode and config.allow_yolo_override:
            if tool_name not in self.settings.always_require_tools:
                return ApprovalStatus.SKIPPED
        
        # Check session approval
        if tool_name in self._session_approved:
            return ApprovalStatus.APPROVED
        
        # Create request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            tool_name=tool_name,
            tool_args=tool_args,
            risk_level=config.risk_level,
            reason=reason or config.approval_message or f"Executing {tool_name}",
        )
        
        # Log if configured
        if self.settings.log_all_requests:
            self._request_history.append(request)
            logger.info(
                f"Approval requested: {tool_name} "
                f"(risk: {config.risk_level.value}, id: {request.request_id})"
            )
        
        # Request approval
        status = await self.handler.request_approval(request)
        
        # Handle session approval
        if status == ApprovalStatus.SKIPPED:
            self._session_approved.add(tool_name)
        
        # Log result
        if self.settings.log_all_requests:
            logger.info(f"Approval result for {tool_name}: {status.value}")
        
        return status
    
    def get_request_history(self) -> List[ApprovalRequest]:
        """Get the history of approval requests."""
        return self._request_history.copy()
    
    def clear_session_approvals(self) -> None:
        """Clear session-level approvals."""
        self._session_approved.clear()


# Global registry instance
_approval_registry: Optional[ToolApprovalRegistry] = None


def get_approval_registry() -> ToolApprovalRegistry:
    """Get or create the global approval registry."""
    global _approval_registry
    if _approval_registry is None:
        _approval_registry = ToolApprovalRegistry()
    return _approval_registry


def reset_approval_registry() -> None:
    """Reset the global approval registry."""
    global _approval_registry
    _approval_registry = None


def requires_approval(
    risk_level: RiskLevel = RiskLevel.MEDIUM,
    message: Optional[str] = None,
    allow_yolo_override: bool = True,
) -> Callable:
    """Decorator to mark a tool as requiring approval.
    
    Usage:
        @requires_approval(risk_level=RiskLevel.HIGH)
        async def delete_file(context: RunContext, path: str) -> str:
            ...
    
    Args:
        risk_level: Risk level of the operation
        message: Custom approval prompt message
        allow_yolo_override: Whether YOLO mode can skip approval
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Store metadata on the function
        func._requires_approval = True
        func._approval_risk_level = risk_level
        func._approval_message = message
        func._allow_yolo_override = allow_yolo_override
        
        # Register with global registry
        registry = get_approval_registry()
        registry.register_tool(
            tool_name=func.__name__,
            requires_approval=True,
            risk_level=risk_level,
            approval_message=message,
            allow_yolo_override=allow_yolo_override,
        )
        
        return func
    
    return decorator


# Pre-configure common dangerous tools
def configure_default_approvals() -> None:
    """Configure default approval requirements for built-in tools."""
    registry = get_approval_registry()
    
    # High-risk file operations
    registry.register_tool(
        "delete_file",
        requires_approval=True,
        risk_level=RiskLevel.HIGH,
        approval_message="Delete a file permanently",
        allow_yolo_override=False,
    )
    
    registry.register_tool(
        "delete_directory",
        requires_approval=True,
        risk_level=RiskLevel.HIGH,
        approval_message="Delete a directory and all contents",
        allow_yolo_override=False,
    )
    
    # Medium-risk operations
    registry.register_tool(
        "run_command",
        requires_approval=True,
        risk_level=RiskLevel.MEDIUM,
        approval_message="Execute a shell command",
    )
    
    registry.register_tool(
        "edit_file",
        requires_approval=True,
        risk_level=RiskLevel.MEDIUM,
        approval_message="Modify file contents",
    )
    
    # Critical operations
    registry.register_tool(
        "modify_system_config",
        requires_approval=True,
        risk_level=RiskLevel.CRITICAL,
        approval_message="Modify system configuration",
        allow_yolo_override=False,
    )
