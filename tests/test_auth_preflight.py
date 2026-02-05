"""Tests for auth preflight verification system."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from code_puppy.tools.auth_preflight import (
    AUTH_DETECTION_PATTERNS,
    AuthCategory,
    AuthPriority,
    AuthRequirement,
    AuthRequirementResult,
    AuthStatus,
    PreflightChecklist,
    PreflightVerificationResult,
    create_preflight_checklist,
    detect_auth_requirements_from_text,
    load_checklist,
    save_checklist,
    verify_cli_command,
    verify_env_var,
    verify_file_exists,
    verify_preflight_checklist,
    verify_single_requirement,
)


class TestAuthEnums:
    """Tests for auth-related enums."""

    def test_auth_category_values(self):
        """Test AuthCategory enum has expected values."""
        assert AuthCategory.CLI_AUTH.value == "cli_auth"
        assert AuthCategory.API_KEY.value == "api_key"
        assert AuthCategory.OAUTH_APP.value == "oauth_app"
        assert AuthCategory.BROWSER_SESSION.value == "browser_session"
        assert AuthCategory.DATABASE.value == "database"
        assert AuthCategory.SERVICE_PRINCIPAL.value == "service_principal"
        assert AuthCategory.CERTIFICATE.value == "certificate"
        assert AuthCategory.SSH_KEY.value == "ssh_key"
        assert AuthCategory.CUSTOM.value == "custom"

    def test_auth_status_values(self):
        """Test AuthStatus enum has expected values."""
        assert AuthStatus.NOT_CHECKED.value == "not_checked"
        assert AuthStatus.CHECKING.value == "checking"
        assert AuthStatus.PASSED.value == "passed"
        assert AuthStatus.FAILED.value == "failed"
        assert AuthStatus.EXPIRED.value == "expired"
        assert AuthStatus.MISSING.value == "missing"
        assert AuthStatus.INSUFFICIENT_PERMISSIONS.value == "insufficient_permissions"

    def test_auth_priority_values(self):
        """Test AuthPriority enum has expected values."""
        assert AuthPriority.CRITICAL.value == "critical"
        assert AuthPriority.HIGH.value == "high"
        assert AuthPriority.MEDIUM.value == "medium"
        assert AuthPriority.LOW.value == "low"


class TestAuthRequirement:
    """Tests for AuthRequirement model."""

    def test_create_requirement(self):
        """Test creating an auth requirement."""
        req = AuthRequirement(
            id="test-auth",
            name="Test Authentication",
            category=AuthCategory.API_KEY,
            purpose="Test auth requirement",
            priority=AuthPriority.HIGH,
        )
        assert req.id == "test-auth"
        assert req.name == "Test Authentication"
        assert req.category == AuthCategory.API_KEY
        assert req.status == AuthStatus.NOT_CHECKED
        assert req.priority == AuthPriority.HIGH
        assert req.required_permissions == []
        assert req.verification_command is None

    def test_requirement_with_verification(self):
        """Test requirement with verification settings."""
        req = AuthRequirement(
            id="az-cli",
            name="Azure CLI",
            category=AuthCategory.CLI_AUTH,
            purpose="Azure CLI authentication",
            priority=AuthPriority.CRITICAL,
            verification_command="az account show",
            verification_env_var="AZURE_SUBSCRIPTION_ID",
        )
        assert req.verification_command == "az account show"
        assert req.verification_env_var == "AZURE_SUBSCRIPTION_ID"

    def test_requirement_serialization(self):
        """Test requirement can be serialized."""
        req = AuthRequirement(
            id="test",
            name="Test",
            category=AuthCategory.API_KEY,
            purpose="Test purpose",
        )
        data = req.model_dump()
        assert data["id"] == "test"
        assert data["category"] == "api_key"


class TestPreflightChecklist:
    """Tests for PreflightChecklist model."""

    def test_create_empty_checklist(self):
        """Test creating an empty checklist."""
        checklist = PreflightChecklist(
            project_name="Test Project",
        )
        assert checklist.project_name == "Test Project"
        assert checklist.requirements == []
        assert checklist.ready_for_phase2 is False

    def test_add_requirement_to_checklist(self):
        """Test adding a requirement to checklist."""
        checklist = PreflightChecklist(
            project_name="Test Project",
        )
        req = AuthRequirement(
            id="test-auth",
            name="Test Auth",
            category=AuthCategory.API_KEY,
            purpose="Test",
            priority=AuthPriority.HIGH,
        )
        checklist.requirements.append(req)
        assert len(checklist.requirements) == 1

    def test_checklist_update_summary(self):
        """Test checklist summary update."""
        checklist = PreflightChecklist(
            project_name="Test",
            requirements=[
                AuthRequirement(
                    id="passed",
                    name="Passed",
                    category=AuthCategory.API_KEY,
                    purpose="Test",
                    priority=AuthPriority.HIGH,
                    status=AuthStatus.PASSED,
                ),
                AuthRequirement(
                    id="failed",
                    name="Failed",
                    category=AuthCategory.CLI_AUTH,
                    purpose="Test",
                    priority=AuthPriority.CRITICAL,
                    status=AuthStatus.FAILED,
                ),
            ],
        )
        checklist.update_summary()
        
        assert checklist.total_requirements == 2
        assert checklist.passed_requirements == 1
        assert checklist.failed_requirements == 1
        assert checklist.all_critical_passed is False
        assert checklist.ready_for_phase2 is False

    def test_checklist_serialization(self):
        """Test checklist can be serialized to JSON."""
        checklist = PreflightChecklist(
            project_name="Test Project",
            requirements=[
                AuthRequirement(
                    id="test-auth",
                    name="Test Auth",
                    category=AuthCategory.API_KEY,
                    purpose="Test",
                    priority=AuthPriority.HIGH,
                )
            ],
        )
        data = checklist.model_dump()
        assert data["project_name"] == "Test Project"
        assert len(data["requirements"]) == 1


class TestChecklistSaveLoad:
    """Tests for saving and loading checklists."""

    def test_save_and_load_checklist(self):
        """Test saving and loading checklist from file."""
        checklist = PreflightChecklist(
            project_name="Test Project",
            requirements=[
                AuthRequirement(
                    id="azure-cli",
                    name="Azure CLI",
                    category=AuthCategory.CLI_AUTH,
                    purpose="Azure CLI auth",
                    priority=AuthPriority.CRITICAL,
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "auth_checklist.json"
            save_checklist(checklist, path)

            assert path.exists()

            loaded = load_checklist(path)
            assert loaded is not None
            assert loaded.project_name == checklist.project_name
            assert len(loaded.requirements) == 1
            assert loaded.requirements[0].id == "azure-cli"

    def test_load_nonexistent_returns_none(self):
        """Test loading nonexistent file returns None."""
        result = load_checklist(Path("/nonexistent/path/checklist.json"))
        assert result is None


class TestDetectAuthRequirements:
    """Tests for auth requirement detection from text."""

    def test_detect_azure_cli(self):
        """Test detecting Azure CLI requirement."""
        text = "Deploy to Azure App Service using az commands"
        reqs = detect_auth_requirements_from_text(text)

        azure_req = next((r for r in reqs if r.id == "azure-cli"), None)
        assert azure_req is not None
        assert azure_req.category == AuthCategory.CLI_AUTH
        assert azure_req.priority == AuthPriority.CRITICAL

    def test_detect_graph_api(self):
        """Test detecting Graph API requirement."""
        text = "Use Microsoft Graph API to access Teams data"
        reqs = detect_auth_requirements_from_text(text)

        graph_req = next((r for r in reqs if r.id == "graph-api"), None)
        assert graph_req is not None

    def test_detect_github(self):
        """Test detecting GitHub CLI requirement."""
        text = "Create GitHub Actions workflow for CI/CD"
        reqs = detect_auth_requirements_from_text(text)

        gh_req = next((r for r in reqs if r.id == "github-cli"), None)
        assert gh_req is not None
        assert gh_req.category == AuthCategory.CLI_AUTH

    def test_detect_aws(self):
        """Test detecting AWS CLI requirement."""
        text = "Deploy Lambda function to AWS"
        reqs = detect_auth_requirements_from_text(text)

        aws_req = next((r for r in reqs if r.id == "aws-cli"), None)
        assert aws_req is not None

    def test_detect_kubernetes(self):
        """Test detecting Kubernetes requirement."""
        text = "Deploy pods to Kubernetes cluster using kubectl"
        reqs = detect_auth_requirements_from_text(text)

        k8s_req = next((r for r in reqs if r.id == "kubectl"), None)
        assert k8s_req is not None

    def test_detect_postgresql(self):
        """Test detecting PostgreSQL requirement."""
        text = "Store data in PostgreSQL database"
        reqs = detect_auth_requirements_from_text(text)

        pg_req = next((r for r in reqs if r.id == "postgresql"), None)
        assert pg_req is not None
        assert pg_req.category == AuthCategory.DATABASE

    def test_detect_docker(self):
        """Test detecting Docker requirement."""
        text = "Build and push Docker container image"
        reqs = detect_auth_requirements_from_text(text)

        docker_req = next((r for r in reqs if r.id == "docker"), None)
        assert docker_req is not None

    def test_detect_terraform(self):
        """Test detecting Terraform requirement."""
        text = "Use Terraform for infrastructure as code"
        reqs = detect_auth_requirements_from_text(text)

        tf_req = next((r for r in reqs if r.id == "terraform"), None)
        assert tf_req is not None

    def test_detect_multiple_requirements(self):
        """Test detecting multiple requirements from complex text."""
        text = """
        Build an Azure web app that uses Microsoft Graph API 
        for Teams integration. Deploy with GitHub Actions 
        and store data in PostgreSQL.
        """
        reqs = detect_auth_requirements_from_text(text)

        assert len(reqs) >= 4
        ids = [r.id for r in reqs]
        assert "azure-cli" in ids
        assert "graph-api" in ids
        assert "github-cli" in ids
        assert "postgresql" in ids

    def test_detect_empty_text(self):
        """Test detection returns empty for unrelated text."""
        text = "Just a simple Python script with no external dependencies"
        reqs = detect_auth_requirements_from_text(text)
        assert len(reqs) == 0

    def test_detect_case_insensitive(self):
        """Test detection is case insensitive."""
        text1 = "Deploy to AZURE"
        text2 = "deploy to azure"

        reqs1 = detect_auth_requirements_from_text(text1)
        reqs2 = detect_auth_requirements_from_text(text2)

        assert len(reqs1) > 0
        assert len(reqs2) > 0


class TestVerificationFunctions:
    """Tests for individual verification functions."""

    @patch("subprocess.run")
    def test_verify_cli_command_success(self, mock_run):
        """Test CLI verification succeeds."""
        mock_run.return_value = MagicMock(returncode=0, stdout="{}")
        success, message, details = verify_cli_command("az account show")

        assert success is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_verify_cli_command_failure(self, mock_run):
        """Test CLI verification fails on error."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Not logged in", stdout="")
        success, message, details = verify_cli_command("az account show")

        assert success is False
        assert "Not logged in" in message

    @patch("subprocess.run")
    def test_verify_cli_command_timeout(self, mock_run):
        """Test CLI verification handles timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("az", 30)
        success, message, details = verify_cli_command("az account show")

        assert success is False
        assert "timed out" in message.lower()

    @patch.dict("os.environ", {"TEST_VAR": "test_value"})
    def test_verify_env_var_exists(self):
        """Test env var verification when var exists."""
        success, message, details = verify_env_var("TEST_VAR")
        assert success is True

    @patch.dict("os.environ", {}, clear=True)
    def test_verify_env_var_missing(self):
        """Test env var verification when var missing."""
        success, message, details = verify_env_var("MISSING_VAR")
        assert success is False
        assert "not set" in message.lower() or "not found" in message.lower()

    def test_verify_file_exists_true(self):
        """Test file verification when file exists."""
        with tempfile.NamedTemporaryFile() as f:
            success, message, details = verify_file_exists(f.name)
            assert success is True

    def test_verify_file_exists_false(self):
        """Test file verification when file missing."""
        success, message, details = verify_file_exists("/nonexistent/path/file.txt")
        assert success is False


class TestVerifySingleRequirement:
    """Tests for single requirement verification."""

    @patch("code_puppy.tools.auth_preflight.verify_cli_command")
    def test_verify_with_command(self, mock_verify):
        """Test verification using CLI command."""
        mock_verify.return_value = (True, "Logged in", {"user": "test@example.com"})
        
        req = AuthRequirement(
            id="test-cli",
            name="Test CLI",
            category=AuthCategory.CLI_AUTH,
            purpose="Test",
            verification_command="test-cli status",
        )
        
        result = verify_single_requirement(req)
        assert result.status == AuthStatus.PASSED
        mock_verify.assert_called_once_with("test-cli status")

    @patch("code_puppy.tools.auth_preflight.verify_env_var")
    def test_verify_with_env_var(self, mock_verify):
        """Test verification using env var."""
        mock_verify.return_value = (True, "Variable set", {"value_length": 32})
        
        req = AuthRequirement(
            id="test-key",
            name="Test API Key",
            category=AuthCategory.API_KEY,
            purpose="Test",
            verification_env_var="TEST_API_KEY",
        )
        
        result = verify_single_requirement(req)
        assert result.status == AuthStatus.PASSED

    def test_verify_no_method_returns_not_checked(self):
        """Test requirement with no verification method."""
        req = AuthRequirement(
            id="manual",
            name="Manual Auth",
            category=AuthCategory.BROWSER_SESSION,
            purpose="Test",
        )
        
        result = verify_single_requirement(req)
        assert result.status == AuthStatus.NOT_CHECKED
        assert "manual" in result.message.lower()


class TestPreflightChecklistVerification:
    """Tests for full checklist verification."""

    @patch("code_puppy.tools.auth_preflight.verify_single_requirement")
    def test_verify_checklist_all_pass(self, mock_verify):
        """Test checklist verification when all pass."""
        mock_verify.return_value = AuthRequirementResult(
            requirement_id="test",
            status=AuthStatus.PASSED,
            message="OK",
        )

        checklist = PreflightChecklist(
            project_name="Test",
            requirements=[
                AuthRequirement(
                    id="test-auth",
                    name="Test Auth",
                    category=AuthCategory.CLI_AUTH,
                    purpose="Test",
                    priority=AuthPriority.CRITICAL,
                )
            ],
        )

        result = verify_preflight_checklist(checklist)
        assert result.all_passed is True
        assert result.ready_for_phase2 is True

    @patch("code_puppy.tools.auth_preflight.verify_single_requirement")
    def test_verify_checklist_with_failures(self, mock_verify):
        """Test checklist verification with failures."""
        mock_verify.return_value = AuthRequirementResult(
            requirement_id="test",
            status=AuthStatus.FAILED,
            message="Not logged in",
        )

        checklist = PreflightChecklist(
            project_name="Test",
            requirements=[
                AuthRequirement(
                    id="azure-cli",
                    name="Azure CLI",
                    category=AuthCategory.CLI_AUTH,
                    purpose="Test",
                    priority=AuthPriority.CRITICAL,
                )
            ],
        )

        result = verify_preflight_checklist(checklist)
        assert result.all_passed is False
        assert len(result.blocking_requirements) >= 1

    def test_verify_checklist_updates_status(self):
        """Test that verification updates requirement status."""
        with tempfile.NamedTemporaryFile() as f:
            checklist = PreflightChecklist(
                project_name="Test",
                requirements=[
                    AuthRequirement(
                        id="test-file",
                        name="Test File",
                        category=AuthCategory.CERTIFICATE,
                        purpose="Test",
                        priority=AuthPriority.HIGH,
                        verification_file=f.name,
                    )
                ],
            )

            result = verify_preflight_checklist(checklist)
            req = checklist.requirements[0]
            assert req.status == AuthStatus.PASSED


class TestCreatePreflightChecklist:
    """Tests for create_preflight_checklist function."""

    def test_create_checklist_basic(self):
        """Test creating a basic checklist."""
        reqs = [
            AuthRequirement(
                id="test",
                name="Test",
                category=AuthCategory.API_KEY,
                purpose="Test",
            )
        ]
        
        checklist = create_preflight_checklist("My Project", reqs)
        
        assert checklist.project_name == "My Project"
        assert len(checklist.requirements) == 1
        assert checklist.total_requirements == 1

    def test_create_empty_checklist(self):
        """Test creating an empty checklist."""
        checklist = create_preflight_checklist("Empty Project", [])
        
        assert checklist.project_name == "Empty Project"
        assert len(checklist.requirements) == 0
        assert checklist.ready_for_phase2 is True  # No requirements means ready


class TestAuthDetectionPatterns:
    """Tests for the AUTH_DETECTION_PATTERNS configuration."""

    def test_all_patterns_have_keywords(self):
        """Test all patterns have keywords defined."""
        for name, pattern in AUTH_DETECTION_PATTERNS.items():
            assert "keywords" in pattern, f"Pattern {name} missing keywords"
            assert len(pattern["keywords"]) > 0, f"Pattern {name} has empty keywords"

    def test_all_patterns_have_requirement(self):
        """Test all patterns have requirement defined."""
        for name, pattern in AUTH_DETECTION_PATTERNS.items():
            assert "requirement" in pattern, f"Pattern {name} missing requirement"
            req = pattern["requirement"]
            assert "id" in req, f"Pattern {name} missing id"
            assert "name" in req, f"Pattern {name} missing name"
            assert "category" in req, f"Pattern {name} missing category"


class TestIntegration:
    """Integration tests for the auth preflight system."""

    def test_full_workflow(self):
        """Test complete workflow: detect -> create checklist -> save -> load."""
        # Step 1: Detect requirements from project description
        project_desc = """
        Build a Teams dashboard that reads data from Microsoft Graph API
        and displays it in a React frontend. Deploy to Azure Static Web Apps.
        """
        reqs = detect_auth_requirements_from_text(project_desc)
        assert len(reqs) >= 2

        # Step 2: Create checklist
        checklist = create_preflight_checklist("Teams Dashboard", reqs)
        assert checklist.total_requirements == len(reqs)

        # Step 3: Save and reload
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checklist.json"
            save_checklist(checklist, path)
            loaded = load_checklist(path)

            assert loaded is not None
            assert loaded.project_name == "Teams Dashboard"
            assert len(loaded.requirements) == len(reqs)

    def test_checklist_ready_when_empty(self):
        """Test checklist is ready when no requirements."""
        checklist = create_preflight_checklist("Simple Project", [])

        result = verify_preflight_checklist(checklist)
        assert result.all_passed is True
        assert result.ready_for_phase2 is True

    @patch("code_puppy.tools.auth_preflight.verify_single_requirement")
    def test_critical_failure_blocks_phase2(self, mock_verify):
        """Test that critical requirement failure blocks Phase 2."""
        # Critical auth fails
        mock_verify.return_value = AuthRequirementResult(
            requirement_id="critical-auth",
            status=AuthStatus.FAILED,
            message="Not logged in",
        )

        checklist = PreflightChecklist(
            project_name="Test",
            requirements=[
                AuthRequirement(
                    id="critical-auth",
                    name="Critical Auth",
                    category=AuthCategory.CLI_AUTH,
                    purpose="Required auth",
                    priority=AuthPriority.CRITICAL,
                ),
            ],
        )

        result = verify_preflight_checklist(checklist)
        assert result.ready_for_phase2 is False
        assert result.critical_passed is False
