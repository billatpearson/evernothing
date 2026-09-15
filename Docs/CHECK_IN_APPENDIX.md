# Check-In Appendix - Definitions & Processes

## Overview
This appendix provides standardized definitions and processes for code check-ins to the EverNothing repository.

## Check-In Types

### 1. Feature Check-In
**Purpose**: Add new functionality to the application

**Requirements**:
- Feature branch created from `main`
- Updated documentation in `Docs/` folder
- New tests added for functionality
- Code reviewed and approved

**Process**:
1. Create feature branch: `git checkout -b feature/feature-name`
2. Implement feature
3. Update docs: `Docs/IMPLEMENTATION_<feature>.md`
4. Run tests: `python test_android.py`
5. Merge to `main`: `git checkout main; git merge feature/feature-name`

### 2. Bug Fix Check-In
**Purpose**: Resolve a known bug or issue

**Requirements**:
- Issue documented in issue tracker
- Reproduction steps provided
- Fix tested on target platforms
- Regression tests added

**Process**:
1. Create bugfix branch: `git checkout -b fix/issue-number-description`
2. Implement fix
3. Document issue and fix in `Docs/HIGH_PRIORITY_FIXES.md`
4. Test on all platforms
5. Merge to `main`

### 3. Hotfix Check-In
**Purpose**: Emergency fix for production issues

**Requirements**:
- Production-impacting issue identified
- Fix deployed to production first
- Follow-up branch created for merge
- Post-mortem documented

**Process**:
1. Deploy fix directly to production
2. Create hotfix branch: `git checkout -b hotfix/issue-number-description`
3. Document incident in `Docs/INCIDENT_<date>.md`
4. Merge to `main` and all release branches

## Code Quality Standards

### 1. Python Code
- Follow PEP 8 style guide
- Type hints required for all functions
- Docstrings required for all modules/classes/functions
- Logging at appropriate levels (DEBUG, INFO, WARNING, ERROR)

### 2. Android Code
- Follow Kotlin style guide
- Use ConstraintLayout for UI
- Proper error handling with user-friendly messages
- Foreground services for long-running operations

### 3. Documentation
- All public APIs documented
- Configuration changes documented
- Database schema changes documented
- Security implications documented

## Check-In Checklist

### Before Check-In
- [ ] Code compiles without errors
- [ ] Tests pass on all platforms
- [ ] Documentation updated
- [ ] No sensitive data in code
- [ ] Environment variables documented in `.env.example`

### After Check-In
- [ ] Changes merged to `main`
- [ ] Tag created for release: `git tag -a v<version> -m "Release v<version>"`
- [ ] Deployment documentation updated
- [ ] Monitoring alerts configured

## Branch Naming Convention

| Branch Type | Prefix | Example |
|-------------|--------|---------|
| Feature | `feature/` | `feature/android-auto-start` |
| Bug Fix | `fix/` | `fix/403-csrf-error` |
| Hotfix | `hotfix/` | `hotfix/critical-login-bug` |
| Release | `release/` | `release/v1.0.0` |
| Development | `dev/` | `dev/android-refactor` |

## Merge Process

### Standard Merge
1. Ensure feature branch is up to date: `git fetch origin; git merge origin/main`
2. Run tests: `pytest`
3. Create merge commit: `git checkout main; git merge --no-ff feature/branch-name`
4. Push to remote: `git push origin main`

### Squash Merge (Preferred for small changes)
1. Squash commits: `git checkout feature/branch-name; git rebase -i main`
2. Run tests
3. Squash merge: `git checkout main; git merge --squash feature/branch-name`
4. Commit with descriptive message
5. Push: `git push origin main`

## Rollback Process

### Quick Rollback
1. Identify problematic commit: `git log --oneline`
2. Create rollback branch: `git checkout -b rollback/<issue>`
3. Revert commit: `git revert <commit-hash>`
4. Test rollback
5. Merge to `main`

### Database Rollback
1. Identify backup: `ls -la Backups/`
2. Restore database: `zcat evernothing_backup_*.db.gz | sqlite3 evernothing.db`
3. Restart application
4. Verify functionality
5. Document incident

## Troubleshooting

### Build Failures
1. Check Gradle cache: `.\gradlew clean --refresh-dependencies`
2. Clear Python cache: `rm -rf __pycache__; rm -rf .pytest_cache`
3. Verify environment: `python -c "import evernothing; print(evernothing.__version__)"`

### Test Failures
1. Run specific test: `python -m pytest test_file.py -v`
2. Enable debug logging: `export FLASK_DEBUG=1`
3. Check database: `sqlite3 evernothing.db "SELECT * FROM table_name;"`

### Deployment Issues
1. Verify environment variables: `cat .env`
2. Check logs: `tail -f evernothing.log`
3. Verify database migration: `python -m evernothing.db.migrate status`

## Related Documents

- [SOLUTIONS_SUMMARY.md](./SOLUTIONS_SUMMARY.md) - Implementation status and documentation
- [SESSION_MANAGEMENT.md](./SESSION_MANAGEMENT.md) - Session management details
- [HIGH_PRIORITY_FIXES.md](./HIGH_PRIORITY_FIXES.md) - Critical fixes and patches
- [RUNBOOK.md](./RUNBOOK.md) - Operations runbook

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-13 | AI Assistant | Initial version with check-in types, standards, and processes |
