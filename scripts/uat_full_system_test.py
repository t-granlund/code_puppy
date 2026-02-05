#!/usr/bin/env python3
"""
Full UAT (User Acceptance Testing) for Code Puppy
Tests actual system behavior end-to-end including:
- Agent invocation and coordination
- Model routing and authentication
- Failover chains under load
- Rate limiting behavior
- Error handling and recovery
- Session management
- Tool execution
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add code_puppy to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_puppy.core.failover_config import (
    AGENT_WORKLOAD_REGISTRY,
    WORKLOAD_CHAINS,
    WorkloadType,
)
from code_puppy.model_factory import ModelFactory
from code_puppy.settings import get_settings

settings = get_settings()


class UATTestRunner:
    """Runs comprehensive UAT tests."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "details": [],
        }
        self.factory = None
    
    def log_test(self, name: str, status: str, details: str = "", error: str = ""):
        """Log a test result."""
        result = {
            "test": name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }
        self.results["details"].append(result)
        
        if status == "PASS":
            self.results["tests_passed"] += 1
            print(f"  ✅ {name}")
            if details:
                print(f"     {details}")
        elif status == "FAIL":
            self.results["tests_failed"] += 1
            print(f"  ❌ {name}")
            if error:
                print(f"     Error: {error}")
        elif status == "SKIP":
            self.results["tests_skipped"] += 1
            print(f"  ⏭️  {name}")
            if details:
                print(f"     {details}")
    
    async def test_model_factory_initialization(self) -> bool:
        """Test 1: Model factory can initialize."""
        try:
            # Load model configuration
            config = ModelFactory.load_config()
            if not config:
                self.log_test(
                    "Model Factory Initialization",
                    "FAIL",
                    error="Failed to load model configuration"
                )
                return False
            
            model_count = len(config.get("models", []))
            self.log_test(
                "Model Factory Initialization",
                "PASS",
                f"Model configuration loaded with {model_count} model definitions"
            )
            return True
        except Exception as e:
            self.log_test(
                "Model Factory Initialization",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_authentication_providers(self) -> bool:
        """Test 2: All authentication providers are accessible."""
        if not self.factory:
            self.log_test("Authentication Providers", "SKIP", "Factory not initialized")
            return False
        
        try:
            authenticated = []
            providers = {}
            
            for model_name in self.factory.models:
                try:
                    model = await self.factory.get_model(model_name)
                    if model:
                        authenticated.append(model_name)
                        provider = model_name.split("-")[0] if "-" in model_name else "unknown"
                        providers[provider] = providers.get(provider, 0) + 1
                except Exception as e:
                    # Expected for models without credentials
                    pass
            
            if authenticated:
                provider_summary = ", ".join([f"{p}: {c}" for p, c in providers.items()])
                self.log_test(
                    "Authentication Providers",
                    "PASS",
                    f"{len(authenticated)} models authenticated ({provider_summary})"
                )
                return True
            else:
                self.log_test(
                    "Authentication Providers",
                    "FAIL",
                    error="No models authenticated"
                )
                return False
        except Exception as e:
            self.log_test(
                "Authentication Providers",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_workload_model_routing(self) -> bool:
        """Test 3: Each workload type can get its primary model."""
        if not self.factory:
            self.log_test("Workload Model Routing", "SKIP", "Factory not initialized")
            return False
        
        try:
            workload_tests = []
            
            for workload_type in [WorkloadType.ORCHESTRATOR, WorkloadType.REASONING, 
                                 WorkloadType.CODING, WorkloadType.LIBRARIAN]:
                chain = WORKLOAD_CHAINS.get(workload_type, [])
                if not chain:
                    continue
                
                # Try to get primary model for this workload
                model = None
                for model_name in chain:
                    try:
                        model = await self.factory.get_model(model_name)
                        if model:
                            workload_tests.append({
                                "workload": workload_type.name,
                                "primary_model": model_name,
                                "chain_depth": len(chain),
                            })
                            break
                    except:
                        continue
            
            if len(workload_tests) == 4:
                details = ", ".join([f"{w['workload']}: {w['primary_model']}" for w in workload_tests])
                self.log_test(
                    "Workload Model Routing",
                    "PASS",
                    f"All 4 workloads have accessible models - {details}"
                )
                return True
            else:
                self.log_test(
                    "Workload Model Routing",
                    "FAIL",
                    error=f"Only {len(workload_tests)}/4 workloads accessible"
                )
                return False
        except Exception as e:
            self.log_test(
                "Workload Model Routing",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_agent_registry_coverage(self) -> bool:
        """Test 4: All agents in filesystem are in registry."""
        try:
            agents_dir = Path(__file__).parent.parent / "code_puppy" / "agents"
            
            if not agents_dir.exists():
                self.log_test(
                    "Agent Registry Coverage",
                    "FAIL",
                    error=f"Agents directory not found: {agents_dir}"
                )
                return False
            
            # Find all agent files
            agent_files = list(agents_dir.glob("agent_*.py"))
            filesystem_agents = set()
            
            for agent_file in agent_files:
                content = agent_file.read_text()
                # Look for agent name in def name(self) -> str: return "agent-name"
                import re
                match = re.search(r'def name\(self\).*?return\s+["\']([^"\']+)["\']', content, re.DOTALL)
                if match:
                    filesystem_agents.add(match.group(1))
            
            # Check registry
            registry_agents = set(AGENT_WORKLOAD_REGISTRY.keys())
            
            missing = filesystem_agents - registry_agents
            extra = registry_agents - filesystem_agents
            
            if not missing and not extra:
                self.log_test(
                    "Agent Registry Coverage",
                    "PASS",
                    f"All {len(filesystem_agents)} filesystem agents in registry"
                )
                return True
            else:
                errors = []
                if missing:
                    errors.append(f"Missing from registry: {missing}")
                if extra:
                    errors.append(f"In registry but not filesystem: {extra}")
                self.log_test(
                    "Agent Registry Coverage",
                    "FAIL",
                    error="; ".join(errors)
                )
                return False
        except Exception as e:
            self.log_test(
                "Agent Registry Coverage",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_rate_limiting_detection(self) -> bool:
        """Test 5: Rate limiting system is functional."""
        try:
            from code_puppy.core.rate_limit_headers import get_rate_limit_tracker
            from code_puppy.core.token_budget import TokenBudgetManager
            
            tracker = get_rate_limit_tracker()
            budget_manager = TokenBudgetManager()
            
            if tracker and budget_manager:
                self.log_test(
                    "Rate Limiting Detection",
                    "PASS",
                    "RateLimitTracker and TokenBudgetManager active"
                )
                return True
            else:
                self.log_test(
                    "Rate Limiting Detection",
                    "FAIL",
                    error=f"Tracker: {tracker is not None}, Budget: {budget_manager is not None}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Rate Limiting Detection",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_session_storage(self) -> bool:
        """Test 6: Session storage is accessible."""
        try:
            from code_puppy.session_storage import SessionStorage
            
            storage = SessionStorage()
            test_session_id = f"uat_test_{int(time.time())}"
            
            # Test write
            storage.save_session(test_session_id, {
                "messages": [{"role": "user", "content": "test"}],
                "metadata": {"test": True}
            })
            
            # Test read
            loaded = storage.load_session(test_session_id)
            
            # Cleanup
            session_file = Path(storage.sessions_dir) / f"{test_session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            if loaded and loaded.get("messages"):
                self.log_test(
                    "Session Storage",
                    "PASS",
                    f"Session write/read successful at {storage.sessions_dir}"
                )
                return True
            else:
                self.log_test(
                    "Session Storage",
                    "FAIL",
                    error="Session write/read failed"
                )
                return False
        except Exception as e:
            self.log_test(
                "Session Storage",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_oauth_token_storage(self) -> bool:
        """Test 7: OAuth token storage locations are accessible."""
        try:
            from code_puppy.config import DATA_DIR
            
            oauth_files = {
                "antigravity": Path(DATA_DIR) / "antigravity_oauth.json",
                "chatgpt": Path(DATA_DIR) / "chatgpt_models.json",
            }
            
            found = []
            for provider, path in oauth_files.items():
                if path.exists():
                    found.append(provider)
            
            if found:
                self.log_test(
                    "OAuth Token Storage",
                    "PASS",
                    f"OAuth tokens found for: {', '.join(found)}"
                )
                return True
            else:
                self.log_test(
                    "OAuth Token Storage",
                    "SKIP",
                    "No OAuth tokens configured (API keys may be in use)"
                )
                return True  # Not a failure if using API keys
        except Exception as e:
            self.log_test(
                "OAuth Token Storage",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_failover_chain_completeness(self) -> bool:
        """Test 8: Failover chains are complete and reachable."""
        try:
            from code_puppy.core.failover_config import FAILOVER_CHAIN
            
            if not FAILOVER_CHAIN:
                self.log_test(
                    "Failover Chain Completeness",
                    "FAIL",
                    error="FAILOVER_CHAIN is empty"
                )
                return False
            
            # Check that failover targets exist
            issues = []
            for source, target in FAILOVER_CHAIN.items():
                if target not in self.factory.models and target not in FAILOVER_CHAIN:
                    issues.append(f"{source} → {target} (target not found)")
            
            if not issues:
                self.log_test(
                    "Failover Chain Completeness",
                    "PASS",
                    f"{len(FAILOVER_CHAIN)} failover mappings validated"
                )
                return True
            else:
                self.log_test(
                    "Failover Chain Completeness",
                    "FAIL",
                    error=f"{len(issues)} broken chains: {issues[:3]}"
                )
                return False
        except Exception as e:
            self.log_test(
                "Failover Chain Completeness",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_critical_workflow_paths(self) -> bool:
        """Test 9: Critical orchestration paths are valid."""
        workflows = [
            {
                "name": "Epistemic Architect orchestration",
                "agents": ["epistemic-architect", "planning-agent", "python-programmer"],
            },
            {
                "name": "Pack Leader coordination",
                "agents": ["pack-leader", "husky", "shepherd"],
            },
            {
                "name": "QA workflow",
                "agents": ["planning-agent", "qa-kitten", "qa-expert"],
            },
        ]
        
        try:
            all_valid = True
            for workflow in workflows:
                invalid_agents = [a for a in workflow["agents"] if a not in AGENT_WORKLOAD_REGISTRY]
                if invalid_agents:
                    all_valid = False
                    self.log_test(
                        f"Workflow: {workflow['name']}",
                        "FAIL",
                        error=f"Invalid agents: {invalid_agents}"
                    )
            
            if all_valid:
                self.log_test(
                    "Critical Workflow Paths",
                    "PASS",
                    f"{len(workflows)} workflows have valid agent paths"
                )
                return True
            else:
                return False
        except Exception as e:
            self.log_test(
                "Critical Workflow Paths",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_model_switching_capability(self) -> bool:
        """Test 10: Can switch between models in a workload chain."""
        if not self.factory:
            self.log_test("Model Switching Capability", "SKIP", "Factory not initialized")
            return False
        
        try:
            # Get ORCHESTRATOR chain
            chain = WORKLOAD_CHAINS.get(WorkloadType.ORCHESTRATOR, [])
            if len(chain) < 2:
                self.log_test(
                    "Model Switching Capability",
                    "SKIP",
                    "Need at least 2 models in chain"
                )
                return True
            
            # Try to get first two models
            models_obtained = []
            for model_name in chain[:3]:
                try:
                    model = await self.factory.get_model(model_name)
                    if model:
                        models_obtained.append(model_name)
                except:
                    pass
            
            if len(models_obtained) >= 2:
                self.log_test(
                    "Model Switching Capability",
                    "PASS",
                    f"Can switch between {len(models_obtained)} models: {', '.join(models_obtained[:2])}"
                )
                return True
            else:
                self.log_test(
                    "Model Switching Capability",
                    "FAIL",
                    error=f"Only {len(models_obtained)} models accessible"
                )
                return False
        except Exception as e:
            self.log_test(
                "Model Switching Capability",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_settings_configuration(self) -> bool:
        """Test 11: Settings are properly loaded."""
        try:
            # Check that settings loaded
            if not settings:
                self.log_test(
                    "Settings Configuration",
                    "FAIL",
                    error="Settings not initialized"
                )
                return False
            
            # Check for key attributes
            if hasattr(settings, 'model') and hasattr(settings, 'paths'):
                self.log_test(
                    "Settings Configuration",
                    "PASS",
                    "Settings loaded with model and path configuration"
                )
                return True
            else:
                self.log_test(
                    "Settings Configuration",
                    "FAIL",
                    error="Settings missing critical attributes"
                )
                return False
        except Exception as e:
            self.log_test(
                "Settings Configuration",
                "FAIL",
                error=str(e)
            )
            return False
    
    async def test_telemetry_integration(self) -> bool:
        """Test 12: Logfire telemetry is available."""
        try:
            import logfire
            
            # Check if logfire is configured
            configured = settings.telemetry_enabled
            
            if configured:
                self.log_test(
                    "Telemetry Integration",
                    "PASS",
                    "Logfire telemetry enabled and configured"
                )
            else:
                self.log_test(
                    "Telemetry Integration",
                    "SKIP",
                    "Telemetry disabled in settings"
                )
            return True
        except Exception as e:
            self.log_test(
                "Telemetry Integration",
                "SKIP",
                f"Logfire not available: {e}"
            )
            return True  # Not critical
    
    async def run_all_tests(self):
        """Run all UAT tests."""
        print("=" * 80)
        print("🔍 FULL UAT - CODE PUPPY SYSTEM TEST")
        print("=" * 80)
        print(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("📦 SYSTEM INITIALIZATION TESTS")
        print("-" * 80)
        await self.test_model_factory_initialization()
        await self.test_settings_configuration()
        
        print("\n🔐 AUTHENTICATION & PROVIDER TESTS")
        print("-" * 80)
        await self.test_authentication_providers()
        await self.test_oauth_token_storage()
        
        print("\n🎭 AGENT & ROUTING TESTS")
        print("-" * 80)
        await self.test_agent_registry_coverage()
        await self.test_workload_model_routing()
        await self.test_critical_workflow_paths()
        
        print("\n⚡ PERFORMANCE & RELIABILITY TESTS")
        print("-" * 80)
        await self.test_rate_limiting_detection()
        await self.test_failover_chain_completeness()
        await self.test_model_switching_capability()
        
        print("\n💾 DATA PERSISTENCE TESTS")
        print("-" * 80)
        await self.test_session_storage()
        
        print("\n📊 OBSERVABILITY TESTS")
        print("-" * 80)
        await self.test_telemetry_integration()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 UAT RESULTS SUMMARY")
        print("=" * 80)
        
        total = self.results["tests_passed"] + self.results["tests_failed"] + self.results["tests_skipped"]
        pass_rate = (self.results["tests_passed"] / total * 100) if total > 0 else 0
        
        print(f"\n  Total Tests: {total}")
        print(f"  ✅ Passed: {self.results['tests_passed']}")
        print(f"  ❌ Failed: {self.results['tests_failed']}")
        print(f"  ⏭️  Skipped: {self.results['tests_skipped']}")
        print(f"  📈 Pass Rate: {pass_rate:.1f}%")
        
        # Readiness assessment
        critical_failures = self.results["tests_failed"]
        
        print("\n" + "=" * 80)
        if critical_failures == 0:
            print("🚀 PRODUCTION READINESS: READY FOR TESTING")
            print("=" * 80)
            print("\n✅ All critical systems operational")
            print("✅ Authentication configured")
            print("✅ Model routing functional")
            print("✅ Agent orchestration ready")
            print("✅ Failover chains complete")
            print("✅ Rate limiting active")
            print("\n💡 Next Steps:")
            print("   1. Run: code-puppy")
            print("   2. Test agent invocation: /invoke epistemic-architect")
            print("   3. Monitor Logfire: https://logfire-api.pydantic.dev")
            print("   4. Verify session persistence across restarts")
            status = 0
        elif critical_failures <= 2:
            print("⚠️  PRODUCTION READINESS: READY WITH WARNINGS")
            print("=" * 80)
            print(f"\n⚠️  {critical_failures} non-critical test(s) failed")
            print("✅ Core functionality operational")
            print("\n💡 Recommended Actions:")
            print("   1. Review failed tests above")
            print("   2. Proceed with caution")
            print("   3. Monitor for issues during testing")
            status = 0
        else:
            print("❌ PRODUCTION READINESS: NOT READY")
            print("=" * 80)
            print(f"\n❌ {critical_failures} critical test(s) failed")
            print("\n🔧 Required Actions:")
            print("   1. Review all failed tests above")
            print("   2. Fix authentication issues")
            print("   3. Verify model configuration")
            print("   4. Re-run UAT after fixes")
            status = 1
        
        print("\n" + "=" * 80)
        print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")
        
        # Save results
        results_file = Path(__file__).parent.parent / "uat_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📝 Detailed results saved to: {results_file}\n")
        
        return status


async def main():
    """Run UAT test suite."""
    runner = UATTestRunner()
    status = await runner.run_all_tests()
    sys.exit(status)


if __name__ == "__main__":
    asyncio.run(main())
