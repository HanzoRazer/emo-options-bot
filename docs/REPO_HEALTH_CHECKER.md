# Repository Health Checker Documentation

## 🔍 **tools/repo_check.ps1 - Comprehensive Repository Diagnostics**

### **Overview**
The repository health checker is a comprehensive PowerShell script that validates the EMO Options Bot repository's health, configuration, and readiness for development or deployment.

### **What It Checks**

#### **🔧 Git Repository Basics**
- ✅ Inside a valid git repository
- ✅ Current branch status and cleanliness  
- ✅ Working tree status (uncommitted changes)
- ✅ Ahead/behind status with remote

#### **🌐 Remote Configuration**
- ✅ Origin remote presence and URL validation
- ✅ Push/fetch remote configuration
- ✅ Expected remote URL validation (if specified)

#### **🏷️ Tag Management**
- ✅ Semver tag validation (`v1.2.3`, `v1.2.3-rc.1`)
- ✅ Latest tag detection
- ✅ Non-semver tag warnings

#### **📁 Required Files**
- ✅ `README.md` - Project documentation
- ✅ `LICENSE` - License information  
- ✅ `.gitignore` - Git ignore patterns
- ✅ `.env.example` - Environment template
- ✅ `CODEOWNERS` - Code review assignments
- ✅ `.github/workflows/ci.yml` - CI/CD pipeline
- ✅ `.github/ISSUE_TEMPLATE/bug_report.yml` - Issue templates
- ✅ `tools/release_check.py` - Phase 3 smoke tests
- ✅ `tools/git_tag_helper.ps1` - Release automation
- ✅ `tools/repo_check.ps1` - This health checker

#### **🐍 Python Configuration**
- ✅ `requirements.txt` - Core dependencies
- ✅ `requirements-ml.txt` - ML dependencies
- 📝 `pyproject.toml` - Project metadata (optional)
- 📝 `mypy.ini` - Type checking config (optional)
- 📝 `ruff.toml` - Linting config (optional)

#### **🧪 Phase 3 System Validation**
- ✅ Python availability check
- ✅ Release check smoke test execution
- ✅ Phase 3 AI trading system validation
- ✅ Order staging functionality test

#### **🐙 GitHub Integration** (via GitHub CLI)
- ✅ Repository visibility and access
- ✅ Default branch validation
- ✅ Workflow list and status
- ✅ Recent run history

### **Usage Examples**

#### **Basic Health Check**
```powershell
pwsh -File tools/repo_check.ps1
```

#### **Strict Validation with Expected Parameters**
```powershell
pwsh -File tools/repo_check.ps1 -ExpectedRemote "https://github.com/HanzoRazer/emo-options-bot.git" -ExpectedBranch "main" -Strict
```

#### **Skip GitHub CLI Checks**
```powershell
pwsh -File tools/repo_check.ps1 -NoGh
```

#### **Cross-Platform (Linux/macOS)**
```bash
./tools/repo_check.sh
```

### **Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ExpectedRemote` | String | "" | Expected GitHub repository URL |
| `ExpectedBranch` | String | "main" | Expected current branch name |
| `Strict` | Switch | False | Fail on warnings (not just errors) |
| `NoGh` | Switch | False | Skip GitHub CLI integration checks |
| `VerboseOutput` | Switch | False | Extra diagnostic information |

### **Exit Codes**

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | ✅ Success | All checks passed |
| 1 | ❌ Failure | Errors detected (or warnings in strict mode) |
| 2 | 🔧 Setup Issue | Git not available or not in repository |

### **Output Format**

```
=== Basics ===
  ✔ Inside a git repository
  ✔ Current branch: main
  ✔ Working tree clean

=== Remotes ===
  ✔ origin remote: https://github.com/HanzoRazer/emo-options-bot.git

=== Tags ===
  ✔ Latest tag: v3.2.0-patch15

=== Required Files ===
  ✔ README.md
  ✔ LICENSE
  ✔ .gitignore
  [... more files ...]

=== Phase 3 Smoke Test ===
  ✔ release_check.py --fast passed

=== GitHub Status (via gh) ===
  ✔ Repository accessible via GitHub CLI
  ✔ Workflows listed

=== Summary ===
  ✔ FAILS: 0
  ✔ WARNS: 0

Result: OK
```

### **Integration with CI/CD**

Add to your GitHub Actions workflow:

```yaml
- name: Repository Health Check
  run: |
    pwsh -File tools/repo_check.ps1 -ExpectedRemote "${{ github.server_url }}/${{ github.repository }}.git" -ExpectedBranch "main" -Strict -NoGh
```

### **Common Warnings and Solutions**

#### **Working Tree Not Clean**
```
! Working tree not clean (uncommitted changes)
```
**Solution**: Commit or stash uncommitted changes

#### **Missing Required File**
```
! Missing: .gitignore
```
**Solution**: Create the missing file

#### **Non-Semver Tags**
```
! Non-semver-ish tags detected: old-tag-format
```
**Solution**: Use `tools/git_tag_helper.ps1` for future tags

#### **Branch Diverged**
```
! Branch diverged (ahead/behind). Consider syncing with remote.
```
**Solution**: `git pull` or `git push` to sync

### **Benefits**

1. **🔍 Comprehensive Validation**: Checks all critical repository components
2. **🚀 CI/CD Ready**: Integrates seamlessly with automated pipelines  
3. **🎯 EMO-Specific**: Validates Phase 3 AI trading system components
4. **🌍 Cross-Platform**: Works on Windows, Linux, and macOS
5. **📊 Clear Reporting**: Color-coded output with actionable messages
6. **⚙️ Configurable**: Flexible parameters for different environments

### **Perfect For**

- **Pre-commit validation** - Ensure repository health before commits
- **CI/CD pipelines** - Automated repository validation
- **Onboarding** - Help new developers verify their setup
- **Release preparation** - Validate repository before releases
- **Health monitoring** - Regular repository maintenance checks

The repository health checker ensures your EMO Options Bot repository maintains professional standards and is always ready for development, collaboration, and deployment! 🚀