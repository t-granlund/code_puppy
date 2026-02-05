# Deployment Guide: From MVP to Production

This guide covers how the Epistemic Architect outputs a **fully tested, deployment-ready MVP** through the 14-stage pipeline.

## 🎯 Pipeline Output: What You Get

After completing all 14 stages, the Epistemic Architect produces:

```
your-project/
├── BUILD.md                    # Complete build plan with phases/milestones
├── README.md                   # Project documentation
├── epistemic/
│   ├── state.json              # Full epistemic state
│   └── auth-checklist.json     # Verified auth requirements
├── docs/
│   ├── lens-evaluation.md      # 7-lens analysis results
│   ├── gap-analysis.md         # Identified gaps with severity
│   ├── goals-and-gates.md      # Goals that passed quality gates
│   └── improvement-plan.md     # Post-build recommendations
├── specs/
│   ├── api-spec.md             # API specifications
│   ├── data-models.md          # Data structure definitions
│   └── component-spec.md       # Component specifications
├── src/                        # Implemented source code
├── tests/                      # Test suite
├── Dockerfile                  # Container definition (if applicable)
├── docker-compose.yml          # Multi-service orchestration (if applicable)
└── .github/
    └── workflows/
        └── ci.yml              # CI/CD pipeline
```

## 🔐 Pre-Flight Authentication (Stage 7)

Before build execution, Stage 7 ensures all authentication is verified:

### Auth Checklist Format
```json
{
  "requirements": [
    {
      "name": "AWS_ACCESS_KEY_ID",
      "type": "env_var",
      "verified": true,
      "verification_method": "env_check"
    },
    {
      "name": "gh CLI",
      "type": "cli_tool", 
      "verified": true,
      "verification_method": "which gh && gh auth status"
    }
  ],
  "all_verified": true,
  "verified_at": "2026-02-04T10:30:00Z"
}
```

### Supported Auth Types
| Type | Verification Method |
|------|---------------------|
| `env_var` | Check environment variable exists |
| `cli_tool` | Verify CLI tool is installed and authenticated |
| `api_key` | Test API endpoint with key |
| `oauth_token` | Validate token expiration |
| `service_account` | Check credentials file exists |

## 🚀 Deployment Stages

### Development Hosting

For quick iteration and testing:

```bash
# Local development
cd your-project
docker-compose up -d

# Or with uvicorn for Python APIs
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Staging Environment

Verify in staging before production:

1. **Deploy to staging cluster/service**
   ```bash
   # Using Azure Container Apps
   az containerapp up --name myapp-staging --source .
   
   # Using AWS App Runner
   aws apprunner create-service --service-name myapp-staging ...
   
   # Using Railway/Render/Fly.io
   fly deploy --config fly.staging.toml
   ```

2. **Run integration tests**
   ```bash
   pytest tests/integration/ --env=staging
   ```

3. **Verify auth checklist in staging**
   ```bash
   # The epistemic architect can verify staging auth
   code_puppy -a epistemic-architect "verify auth in staging environment"
   ```

### Production Deployment

After staging verification:

1. **Final quality gates**
   - All tests passing
   - Security audit complete (Stage 12)
   - Documentation synced (Stage 13)
   - Auth checklist 100% verified

2. **Deploy to production**
   ```bash
   # CI/CD handles this via .github/workflows/
   git push origin main  # Triggers production deploy
   ```

3. **Monitor with Logfire**
   ```python
   # Telemetry is automatically integrated
   # View at: https://logfire.pydantic.dev/
   ```

## 📊 Logfire Telemetry Integration

The Epistemic Architect logs key events to Logfire for observability:

### Pipeline Events
| Event | When Logged |
|-------|-------------|
| `project_bootstrap.discovery_start` | Begin scanning existing project |
| `project_bootstrap.discovery_complete` | Finished scanning with results |
| `auth_preflight.check_start` | Starting auth verification |
| `auth_preflight.requirement_verified` | Single requirement verified |
| `auth_preflight.all_verified` | All auth requirements verified |
| `ear_phase` | Each EAR pipeline stage transition |

### Example Logfire Queries
```python
# Find all auth failures
logfire.query("auth_preflight.* AND verified=false")

# Track pipeline progression  
logfire.query("ear_phase ORDER BY timestamp")

# Bootstrap resumption patterns
logfire.query("project_bootstrap.* AND resume_stage > 0")
```

## 🔄 Continuous Improvement Loop

After initial deployment, the pipeline enters stages 9-13:

```
Stage 9 (Improvement Audit)
    ↓
Stage 10 (Gap Re-Inspection)
    ↓
Stage 11 (Question Tracking)
    ↓
Stage 12 (Verification Audit)
    ↓
Stage 13 (Documentation Sync)
    ↓
    ↺ Loop back to Stage 9
```

Each loop iteration:
1. Collects evidence from production
2. Analyzes gaps that emerged
3. Updates epistemic state with learnings
4. Verifies all layers still functioning
5. Syncs documentation with reality

## 📋 Production Readiness Checklist

Before going live, verify:

- [ ] All 14 pipeline stages completed
- [ ] Auth checklist 100% verified
- [ ] All tests passing (unit, integration, e2e)
- [ ] Security audit findings addressed
- [ ] Performance benchmarks met
- [ ] Rollback plan documented in BUILD.md
- [ ] Monitoring/alerting configured
- [ ] Documentation up to date
- [ ] Logfire telemetry connected

## 🛠️ Tools Summary

| Tool | Purpose | Stage |
|------|---------|-------|
| `discover_project` | Bootstrap from existing project | Pre-pipeline |
| `get_discovery_state` | Convert to epistemic state | Pre-pipeline |
| `get_resume_questions` | Focused questions only | Pre-pipeline |
| `preflight_auth_check` | Verify all auth requirements | Stage 7 |
| `add_auth_requirement` | Add new auth requirement | Stage 7 |
| `check_wiggum_status` | Track build loop progress | Stage 8+ |
| `complete_wiggum_loop` | Mark milestone complete | Stage 8+ |

## 🔗 Related Documentation

- [EPISTEMIC.md](./EPISTEMIC.md) - Full EAR methodology
- [LOGFIRE-INTEGRATION.md](./LOGFIRE-INTEGRATION.md) - Telemetry setup
- [ROBUSTNESS-INFRASTRUCTURE.md](./ROBUSTNESS-INFRASTRUCTURE.md) - Failover and resilience
- [TEST-COVERAGE-ANALYSIS.md](./TEST-COVERAGE-ANALYSIS.md) - Testing strategy
