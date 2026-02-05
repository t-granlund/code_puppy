"""Pre-Flight Authentication System for Epistemic Architect.

This module provides infrastructure for detecting, tracking, and verifying
authentication requirements before autonomous (wiggum) execution can begin.

The Pre-Flight system:
1. Detects auth requirements from project specs (what CLIs, APIs, services needed)
2. Creates a structured checklist of credentials/permissions
3. Guides users through authentication setup
4. Verifies all auth requirements are satisfied before Phase 2
5. Supports dynamic agent/tool creation for custom auth flows

Authentication Categories:
- CLI_AUTH: Azure CLI, AWS CLI, gcloud, etc.
- API_KEY: Static API keys for services
- OAUTH_APP: Custom app registrations (Azure AD, Google, etc.)
- BROWSER_SESSION: Services requiring browser login (no API access)
- DATABASE: Database connection strings
- SERVICE_PRINCIPAL: Automated identity for CI/CD
- CERTIFICATE: mTLS or certificate-based auth

Usage:
    # During Phase 1, detect requirements from specs
    requirements = detect_auth_requirements(epistemic_state)
    
    # Create checklist
    checklist = create_preflight_checklist(requirements)
    
    # During Phase 1 interview, guide user through setup
    # ... user completes auth setup ...
    
    # Before Phase 2, verify all requirements met
    result = verify_preflight_checklist(checklist)
    if result.all_passed:
        # Safe to proceed with /wiggum
    else:
        # Block and show what's missing
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# 🔥 LOGFIRE TELEMETRY SUPPORT
# =============================================================================

def _log_preflight_event(event_type: str, **kwargs) -> None:
    """Log a Pre-Flight Auth telemetry event to Logfire.
    
    Pattern follows ralph_loop.py for consistent observability.
    Fails silently if Logfire is not available.
    """
    try:
        import logfire
        logfire.info(f"Pre-flight auth: {event_type}", **kwargs)
    except Exception:
        pass


# =============================================================================
# 🔐 AUTHENTICATION CATEGORY DEFINITIONS
# =============================================================================


class AuthCategory(str, Enum):
    """Categories of authentication requirements."""
    
    CLI_AUTH = "cli_auth"  # Azure CLI, AWS CLI, gcloud, kubectl
    API_KEY = "api_key"  # Static API keys (OPENAI_API_KEY, etc.)
    OAUTH_APP = "oauth_app"  # Custom app registration (Azure AD, Google)
    BROWSER_SESSION = "browser_session"  # Manual browser login required
    DATABASE = "database"  # Database connection strings
    SERVICE_PRINCIPAL = "service_principal"  # Automated identity
    CERTIFICATE = "certificate"  # mTLS or cert-based auth
    SSH_KEY = "ssh_key"  # SSH key for git, servers
    CUSTOM = "custom"  # Project-specific auth


class AuthStatus(str, Enum):
    """Status of an authentication requirement."""
    
    NOT_CHECKED = "not_checked"
    CHECKING = "checking"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"
    MISSING = "missing"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"


class AuthPriority(str, Enum):
    """Priority level for auth requirements."""
    
    CRITICAL = "critical"  # Blocks all work
    HIGH = "high"  # Blocks most work
    MEDIUM = "medium"  # Blocks some features
    LOW = "low"  # Nice to have, fallback available


# =============================================================================
# 🔑 AUTH REQUIREMENT MODELS
# =============================================================================


class AuthRequirement(BaseModel):
    """A single authentication requirement for the project."""
    
    id: str = Field(description="Unique identifier (e.g., 'azure-cli', 'graph-api')")
    name: str = Field(description="Human-readable name")
    category: AuthCategory
    priority: AuthPriority = AuthPriority.HIGH
    
    # What this auth is for
    purpose: str = Field(description="Why this auth is needed")
    used_by: List[str] = Field(default_factory=list, description="Milestones/features using this")
    
    # How to verify
    verification_command: Optional[str] = Field(
        default=None, 
        description="CLI command to verify (e.g., 'az account show')"
    )
    verification_env_var: Optional[str] = Field(
        default=None,
        description="Environment variable to check"
    )
    verification_file: Optional[str] = Field(
        default=None,
        description="File path to check exists"
    )
    verification_url: Optional[str] = Field(
        default=None,
        description="URL to test connectivity"
    )
    
    # Required permissions/scopes
    required_permissions: List[str] = Field(
        default_factory=list,
        description="Specific permissions needed (e.g., 'User.Read', 'admin:org')"
    )
    
    # Setup instructions
    setup_instructions: str = Field(
        default="",
        description="How to set up this authentication"
    )
    setup_url: Optional[str] = Field(
        default=None,
        description="Documentation URL for setup"
    )
    
    # Browser automation fallback
    browser_automation_possible: bool = Field(
        default=False,
        description="Can use browser automation if CLI/API unavailable"
    )
    browser_automation_agent: Optional[str] = Field(
        default=None,
        description="Agent to invoke for browser automation"
    )
    
    # Current status
    status: AuthStatus = AuthStatus.NOT_CHECKED
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # User info (for Azure/Microsoft)
    user_upn: Optional[str] = Field(default=None, description="User Principal Name")
    user_object_id: Optional[str] = Field(default=None, description="Azure AD Object ID")
    tenant_id: Optional[str] = Field(default=None, description="Azure Tenant ID")
    subscription_id: Optional[str] = Field(default=None, description="Azure Subscription ID")


class AuthRequirementResult(BaseModel):
    """Result of checking a single auth requirement."""
    
    requirement_id: str
    status: AuthStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PreflightChecklist(BaseModel):
    """Complete pre-flight authentication checklist."""
    
    project_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    requirements: List[AuthRequirement] = Field(default_factory=list)
    
    # Summary
    total_requirements: int = 0
    passed_requirements: int = 0
    failed_requirements: int = 0
    missing_requirements: int = 0
    
    # Overall status
    all_critical_passed: bool = False
    all_high_passed: bool = False
    ready_for_phase2: bool = False
    
    def update_summary(self) -> None:
        """Recalculate summary statistics."""
        self.total_requirements = len(self.requirements)
        self.passed_requirements = sum(1 for r in self.requirements if r.status == AuthStatus.PASSED)
        self.failed_requirements = sum(1 for r in self.requirements if r.status == AuthStatus.FAILED)
        self.missing_requirements = sum(1 for r in self.requirements if r.status == AuthStatus.MISSING)
        
        critical = [r for r in self.requirements if r.priority == AuthPriority.CRITICAL]
        high = [r for r in self.requirements if r.priority == AuthPriority.HIGH]
        
        self.all_critical_passed = all(r.status == AuthStatus.PASSED for r in critical)
        self.all_high_passed = all(r.status == AuthStatus.PASSED for r in high)
        self.ready_for_phase2 = self.all_critical_passed and self.all_high_passed
        
        self.updated_at = datetime.now(timezone.utc)


class PreflightVerificationResult(BaseModel):
    """Result of running the complete pre-flight check."""
    
    checklist_id: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    results: List[AuthRequirementResult] = Field(default_factory=list)
    
    all_passed: bool = False
    critical_passed: bool = False
    high_passed: bool = False
    ready_for_phase2: bool = False
    
    blocking_requirements: List[str] = Field(default_factory=list)
    warning_requirements: List[str] = Field(default_factory=list)
    
    summary_message: str = ""


# =============================================================================
# 🔍 AUTH REQUIREMENT DETECTION
# =============================================================================


# Common patterns that indicate auth requirements
AUTH_DETECTION_PATTERNS: Dict[str, Dict[str, Any]] = {
    # Azure
    "azure": {
        "keywords": ["azure", "az cli", "azure functions", "app service", "cosmos", "blob storage"],
        "requirement": {
            "id": "azure-cli",
            "name": "Azure CLI Authentication",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.CRITICAL,
            "purpose": "Deploy and manage Azure resources",
            "verification_command": "az account show --output json",
            "setup_instructions": "Run 'az login' to authenticate with your Azure account",
            "setup_url": "https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli",
        }
    },
    "graph-api": {
        "keywords": ["microsoft graph", "graph api", "microsoft 365", "sharepoint", "teams api"],
        "requirement": {
            "id": "graph-api",
            "name": "Microsoft Graph API Access",
            "category": AuthCategory.OAUTH_APP,
            "priority": AuthPriority.CRITICAL,
            "purpose": "Access Microsoft 365 data and services",
            "required_permissions": ["User.Read", "offline_access"],
            "setup_instructions": "Create an Azure AD app registration with Graph API permissions",
            "setup_url": "https://docs.microsoft.com/en-us/graph/auth-register-app-v2",
            "browser_automation_possible": True,
        }
    },
    # AWS
    "aws": {
        "keywords": ["aws", "lambda", "s3", "dynamodb", "cloudformation", "cdk"],
        "requirement": {
            "id": "aws-cli",
            "name": "AWS CLI Authentication",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.CRITICAL,
            "purpose": "Deploy and manage AWS resources",
            "verification_command": "aws sts get-caller-identity --output json",
            "setup_instructions": "Run 'aws configure' or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY",
            "setup_url": "https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html",
        }
    },
    # Google Cloud
    "gcloud": {
        "keywords": ["gcp", "google cloud", "firebase", "cloud run", "cloud functions"],
        "requirement": {
            "id": "gcloud-cli",
            "name": "Google Cloud CLI Authentication",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.CRITICAL,
            "purpose": "Deploy and manage Google Cloud resources",
            "verification_command": "gcloud auth list --format=json",
            "setup_instructions": "Run 'gcloud auth login' to authenticate",
            "setup_url": "https://cloud.google.com/sdk/docs/authorizing",
        }
    },
    # Kubernetes
    "kubernetes": {
        "keywords": ["kubernetes", "k8s", "kubectl", "helm", "aks", "eks", "gke"],
        "requirement": {
            "id": "kubectl",
            "name": "Kubernetes Cluster Access",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.HIGH,
            "purpose": "Deploy and manage Kubernetes workloads",
            "verification_command": "kubectl cluster-info",
            "setup_instructions": "Configure kubectl with cluster credentials",
            "setup_url": "https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/",
        }
    },
    # GitHub
    "github": {
        "keywords": ["github actions", "github api", "github app", "gh cli"],
        "requirement": {
            "id": "github-cli",
            "name": "GitHub CLI Authentication",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.HIGH,
            "purpose": "Manage GitHub repositories and workflows",
            "verification_command": "gh auth status",
            "verification_env_var": "GITHUB_TOKEN",
            "setup_instructions": "Run 'gh auth login' or set GITHUB_TOKEN",
            "setup_url": "https://cli.github.com/manual/gh_auth_login",
        }
    },
    # Database
    "postgresql": {
        "keywords": ["postgresql", "postgres", "psql", "pg_"],
        "requirement": {
            "id": "postgresql",
            "name": "PostgreSQL Database Connection",
            "category": AuthCategory.DATABASE,
            "priority": AuthPriority.HIGH,
            "purpose": "Connect to PostgreSQL database",
            "verification_env_var": "DATABASE_URL",
            "setup_instructions": "Set DATABASE_URL environment variable with connection string",
        }
    },
    # Docker
    "docker": {
        "keywords": ["docker", "container registry", "acr", "ecr", "gcr"],
        "requirement": {
            "id": "docker",
            "name": "Docker/Container Registry Access",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.HIGH,
            "purpose": "Build and push container images",
            "verification_command": "docker info",
            "setup_instructions": "Start Docker daemon and authenticate to registry",
        }
    },
    # Terraform
    "terraform": {
        "keywords": ["terraform", "infrastructure as code", "iac"],
        "requirement": {
            "id": "terraform",
            "name": "Terraform CLI",
            "category": AuthCategory.CLI_AUTH,
            "priority": AuthPriority.HIGH,
            "purpose": "Provision infrastructure",
            "verification_command": "terraform version",
            "setup_instructions": "Install Terraform and configure provider credentials",
            "setup_url": "https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli",
        }
    },
}


def detect_auth_requirements_from_text(text: str) -> List[AuthRequirement]:
    """Detect authentication requirements from project description text.
    
    Args:
        text: Project description, specs, or requirements text
        
    Returns:
        List of detected AuthRequirement objects
    """
    text_lower = text.lower()
    detected: List[AuthRequirement] = []
    seen_ids: set = set()
    
    for pattern_name, pattern_data in AUTH_DETECTION_PATTERNS.items():
        keywords = pattern_data["keywords"]
        if any(kw in text_lower for kw in keywords):
            req_data = pattern_data["requirement"].copy()
            if req_data["id"] not in seen_ids:
                detected.append(AuthRequirement(**req_data))
                seen_ids.add(req_data["id"])
    
    # Log detection results to Logfire
    _log_preflight_event(
        "requirements_detected",
        count=len(detected),
        categories=[r.category.value for r in detected],
        text_length=len(text),
    )
    
    return detected


def detect_auth_from_epistemic_state(state_path: Path) -> List[AuthRequirement]:
    """Detect auth requirements from an epistemic state file.
    
    Reads epistemic/state.json and analyzes:
    - Assumptions about infrastructure
    - Constraints mentioning services
    - Goals requiring external services
    
    Args:
        state_path: Path to epistemic/state.json
        
    Returns:
        List of detected AuthRequirement objects
    """
    if not state_path.exists():
        return []
    
    try:
        with open(state_path) as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    
    # Combine all text fields for analysis
    text_parts = []
    
    # Check assumptions
    for assumption in state.get("assumptions", []):
        if isinstance(assumption, dict):
            text_parts.append(assumption.get("text", ""))
        elif isinstance(assumption, str):
            text_parts.append(assumption)
    
    # Check constraints
    for constraint in state.get("hard_constraints", []) + state.get("soft_constraints", []):
        if isinstance(constraint, dict):
            text_parts.append(constraint.get("text", ""))
        elif isinstance(constraint, str):
            text_parts.append(constraint)
    
    # Check goals
    for goal in state.get("approved_goals", []) + state.get("goals", []):
        if isinstance(goal, dict):
            text_parts.append(goal.get("description", ""))
        elif isinstance(goal, str):
            text_parts.append(goal)
    
    combined_text = " ".join(text_parts)
    return detect_auth_requirements_from_text(combined_text)


# =============================================================================
# ✅ AUTH VERIFICATION
# =============================================================================


def verify_cli_command(command: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify a CLI command succeeds.
    
    Args:
        command: CLI command to run
        
    Returns:
        Tuple of (success, message, details)
    """
    try:
        # Check if the command exists first
        cmd_parts = command.split()
        cmd_name = cmd_parts[0]
        
        if not shutil.which(cmd_name):
            return False, f"Command '{cmd_name}' not found. Please install it.", {}
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            # Try to parse JSON output
            details = {}
            try:
                if result.stdout.strip():
                    details = json.loads(result.stdout)
            except json.JSONDecodeError:
                details = {"output": result.stdout[:500]}
            
            return True, "Authentication verified", details
        else:
            return False, f"Command failed: {result.stderr[:200]}", {}
            
    except subprocess.TimeoutExpired:
        return False, "Command timed out", {}
    except Exception as e:
        return False, f"Error: {str(e)}", {}


def verify_env_var(var_name: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify an environment variable is set.
    
    Args:
        var_name: Name of environment variable
        
    Returns:
        Tuple of (success, message, details)
    """
    value = os.environ.get(var_name)
    if value:
        # Mask the value for security
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        return True, f"Environment variable set", {"masked_value": masked}
    else:
        return False, f"Environment variable '{var_name}' not set", {}


def verify_file_exists(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify a file exists.
    
    Args:
        file_path: Path to file
        
    Returns:
        Tuple of (success, message, details)
    """
    path = Path(file_path).expanduser()
    if path.exists():
        return True, f"File exists", {"path": str(path)}
    else:
        return False, f"File not found: {file_path}", {}


def verify_single_requirement(req: AuthRequirement) -> AuthRequirementResult:
    """Verify a single authentication requirement.
    
    Args:
        req: The requirement to verify
        
    Returns:
        AuthRequirementResult with status and details
    """
    # Log verification start
    _log_preflight_event(
        "verification_start",
        requirement_id=req.id,
        requirement_name=req.name,
        category=req.category.value,
        priority=req.priority.value,
    )
    
    # Try verification methods in order of preference
    if req.verification_command:
        success, message, details = verify_cli_command(req.verification_command)
        status = AuthStatus.PASSED if success else AuthStatus.FAILED
        
        # Extract user info from Azure/AWS/GCP responses
        if success and details:
            if "user" in details:
                user = details["user"]
                if isinstance(user, dict):
                    req.user_upn = user.get("name") or user.get("userPrincipalName")
                    req.user_object_id = user.get("objectId")
            if "tenantId" in details:
                req.tenant_id = details["tenantId"]
            if "id" in details and "subscriptions" in str(details.get("id", "")):
                # Azure subscription ID extraction
                pass
        
        result = AuthRequirementResult(
            requirement_id=req.id,
            status=status,
            message=message,
            details=details,
        )
        _log_preflight_event(
            "verification_complete",
            requirement_id=req.id,
            status=status.value,
            method="cli_command",
        )
        return result
    
    if req.verification_env_var:
        success, message, details = verify_env_var(req.verification_env_var)
        status = AuthStatus.PASSED if success else AuthStatus.MISSING
        
        result = AuthRequirementResult(
            requirement_id=req.id,
            status=status,
            message=message,
            details=details,
        )
        _log_preflight_event(
            "verification_complete",
            requirement_id=req.id,
            status=status.value,
            method="env_var",
        )
        return result
    
    if req.verification_file:
        success, message, details = verify_file_exists(req.verification_file)
        status = AuthStatus.PASSED if success else AuthStatus.MISSING
        
        result = AuthRequirementResult(
            requirement_id=req.id,
            status=status,
            message=message,
            details=details,
        )
        _log_preflight_event(
            "verification_complete",
            requirement_id=req.id,
            status=status.value,
            method="file_check",
        )
        return result
    
    # No verification method - mark as not checked
    result = AuthRequirementResult(
        requirement_id=req.id,
        status=AuthStatus.NOT_CHECKED,
        message="No verification method available - manual verification required",
        details={},
    )
    _log_preflight_event(
        "verification_complete",
        requirement_id=req.id,
        status="not_checked",
        method="none",
    )
    return result


def verify_preflight_checklist(checklist: PreflightChecklist) -> PreflightVerificationResult:
    """Verify all requirements in a pre-flight checklist.
    
    Args:
        checklist: The checklist to verify
        
    Returns:
        PreflightVerificationResult with all results
    """
    # Log checklist verification start
    _log_preflight_event(
        "checklist_verification_start",
        project_name=checklist.project_name,
        requirement_count=len(checklist.requirements),
    )
    
    results: List[AuthRequirementResult] = []
    blocking: List[str] = []
    warnings: List[str] = []
    
    for req in checklist.requirements:
        result = verify_single_requirement(req)
        results.append(result)
        
        # Update requirement status
        req.status = result.status
        req.last_checked = result.checked_at
        if result.status == AuthStatus.FAILED:
            req.error_message = result.message
        
        # Track blocking/warning requirements
        if result.status != AuthStatus.PASSED:
            if req.priority in (AuthPriority.CRITICAL, AuthPriority.HIGH):
                blocking.append(f"{req.name}: {result.message}")
            else:
                warnings.append(f"{req.name}: {result.message}")
    
    # Update checklist summary
    checklist.update_summary()
    
    # Build result
    all_passed = len(blocking) == 0 and len(warnings) == 0
    critical_passed = checklist.all_critical_passed
    high_passed = checklist.all_high_passed
    ready = checklist.ready_for_phase2
    
    if ready:
        summary = "✅ All authentication requirements verified. Ready for Phase 2 (wiggum mode)."
    elif critical_passed:
        summary = f"⚠️ Critical requirements passed, but {len(blocking)} high-priority issues remain."
    else:
        summary = f"❌ {len(blocking)} blocking authentication requirements not satisfied."
    
    # Log checklist verification complete
    _log_preflight_event(
        "checklist_verification_complete",
        project_name=checklist.project_name,
        all_passed=all_passed,
        critical_passed=critical_passed,
        ready_for_phase2=ready,
        blocking_count=len(blocking),
        warning_count=len(warnings),
    )
    
    return PreflightVerificationResult(
        checklist_id=checklist.project_name,
        results=results,
        all_passed=all_passed,
        critical_passed=critical_passed,
        high_passed=high_passed,
        ready_for_phase2=ready,
        blocking_requirements=blocking,
        warning_requirements=warnings,
        summary_message=summary,
    )


# =============================================================================
# 📋 CHECKLIST MANAGEMENT
# =============================================================================


def create_preflight_checklist(
    project_name: str,
    requirements: List[AuthRequirement],
) -> PreflightChecklist:
    """Create a pre-flight checklist from detected requirements.
    
    Args:
        project_name: Name of the project
        requirements: List of auth requirements
        
    Returns:
        PreflightChecklist ready for verification
    """
    checklist = PreflightChecklist(
        project_name=project_name,
        requirements=requirements,
    )
    checklist.update_summary()
    return checklist


def save_checklist(checklist: PreflightChecklist, path: Path) -> None:
    """Save checklist to JSON file.
    
    Args:
        checklist: The checklist to save
        path: Path to save to (typically epistemic/auth-checklist.json)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(checklist.model_dump_json(indent=2))


def load_checklist(path: Path) -> Optional[PreflightChecklist]:
    """Load checklist from JSON file.
    
    Args:
        path: Path to load from
        
    Returns:
        PreflightChecklist or None if not found
    """
    if not path.exists():
        return None
    
    try:
        with open(path) as f:
            data = json.load(f)
        return PreflightChecklist.model_validate(data)
    except (json.JSONDecodeError, IOError):
        return None


# =============================================================================
# 🛠️ TOOL REGISTRATION FOR AGENTS
# =============================================================================


def register_preflight_check(agent) -> None:
    """Register the preflight authentication check tool with an agent."""
    from pydantic_ai import RunContext
    
    @agent.tool
    def preflight_auth_check(
        context: RunContext,  # noqa: ARG001
        project_path: str = ".",
    ) -> Dict[str, Any]:
        """Run pre-flight authentication verification for the project.
        
        This tool checks all detected authentication requirements to ensure
        the project is ready for autonomous (wiggum) execution.
        
        Call this at the END of Phase 1, before suggesting /wiggum mode.
        
        Args:
            project_path: Path to project root (default: current directory)
            
        Returns:
            Dict with:
                - ready_for_phase2: bool - Can proceed with /wiggum
                - requirements_count: int - Total requirements detected
                - passed_count: int - Requirements that passed
                - blocking: list - Issues that block Phase 2
                - warnings: list - Non-blocking issues
                - summary: str - Human-readable summary
                - checklist_path: str - Path to saved checklist
        """
        project = Path(project_path)
        state_path = project / "epistemic" / "state.json"
        checklist_path = project / "epistemic" / "auth-checklist.json"
        
        # Load or create checklist
        checklist = load_checklist(checklist_path)
        
        if checklist is None:
            # Detect requirements from epistemic state
            requirements = detect_auth_from_epistemic_state(state_path)
            
            if not requirements:
                return {
                    "ready_for_phase2": True,
                    "requirements_count": 0,
                    "passed_count": 0,
                    "blocking": [],
                    "warnings": [],
                    "summary": "No authentication requirements detected. Ready for Phase 2.",
                    "checklist_path": None,
                }
            
            checklist = create_preflight_checklist(
                project_name=project.name,
                requirements=requirements,
            )
        
        # Run verification
        result = verify_preflight_checklist(checklist)
        
        # Save updated checklist
        save_checklist(checklist, checklist_path)
        
        return {
            "ready_for_phase2": result.ready_for_phase2,
            "requirements_count": len(checklist.requirements),
            "passed_count": checklist.passed_requirements,
            "blocking": result.blocking_requirements,
            "warnings": result.warning_requirements,
            "summary": result.summary_message,
            "checklist_path": str(checklist_path),
        }


def register_add_auth_requirement(agent) -> None:
    """Register tool to manually add auth requirements."""
    from pydantic_ai import RunContext
    
    @agent.tool
    def add_auth_requirement(
        context: RunContext,  # noqa: ARG001
        requirement_id: str,
        name: str,
        category: str,
        purpose: str,
        priority: str = "high",
        verification_command: Optional[str] = None,
        verification_env_var: Optional[str] = None,
        setup_instructions: str = "",
        project_path: str = ".",
    ) -> Dict[str, Any]:
        """Add a custom authentication requirement to the pre-flight checklist.
        
        Use this when you detect a service/integration that needs credentials
        but isn't automatically detected.
        
        Args:
            requirement_id: Unique ID (e.g., 'stripe-api', 'sendgrid')
            name: Human-readable name
            category: One of: cli_auth, api_key, oauth_app, browser_session, database
            purpose: Why this auth is needed
            priority: One of: critical, high, medium, low
            verification_command: CLI command to verify (optional)
            verification_env_var: Env var to check (optional)
            setup_instructions: How to set up this auth
            project_path: Path to project root
            
        Returns:
            Dict with success status and updated checklist info
        """
        project = Path(project_path)
        checklist_path = project / "epistemic" / "auth-checklist.json"
        
        # Load or create checklist
        checklist = load_checklist(checklist_path)
        if checklist is None:
            checklist = PreflightChecklist(project_name=project.name)
        
        # Check if already exists
        existing_ids = {r.id for r in checklist.requirements}
        if requirement_id in existing_ids:
            return {
                "success": False,
                "message": f"Requirement '{requirement_id}' already exists",
            }
        
        # Create new requirement
        try:
            cat = AuthCategory(category)
            pri = AuthPriority(priority)
        except ValueError as e:
            return {
                "success": False,
                "message": f"Invalid category or priority: {e}",
            }
        
        req = AuthRequirement(
            id=requirement_id,
            name=name,
            category=cat,
            priority=pri,
            purpose=purpose,
            verification_command=verification_command,
            verification_env_var=verification_env_var,
            setup_instructions=setup_instructions,
        )
        
        checklist.requirements.append(req)
        checklist.update_summary()
        save_checklist(checklist, checklist_path)
        
        return {
            "success": True,
            "message": f"Added requirement '{name}'",
            "total_requirements": checklist.total_requirements,
        }


def register_auth_preflight_tools(agent) -> None:
    """Register all pre-flight authentication tools with an agent."""
    register_preflight_check(agent)
    register_add_auth_requirement(agent)
