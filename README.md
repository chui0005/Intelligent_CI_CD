# Intelligent CI/CD with AI Code Quality & Security Scanning

This demo repo shows a full CI/CD story arc:
1. `intentionally-bad` branch fails CI due to lint, security scanning, dependency scan, and AI review gate.
2. `main` (fixed state) passes CI after secure refactoring.

## Repository file tree

```text
.
├── .env.example
├── .github
│   └── workflows
│       ├── ci.yml
│       └── codeql.yml
├── AGENTS.md
├── README.md
├── app
│   ├── main.py
│   ├── security.py
│   └── utils.py
├── pyproject.toml
├── requirements.txt
├── scripts
│   ├── make_bad_changes.sh
│   └── make_fix_changes.sh
└── tests
    └── test_main.py
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run tools locally

```bash
ruff check .
pytest
bandit -r app -ll -f txt
pip-audit -r requirements.txt --ignore-vuln GHSA-7f5h-v6xp-fcq8
```

## GitHub secret for AI gate

Set repository secret:
- Name: `OPENAI_API_KEY`
- Value: your OpenAI API key

Without this secret, `ai-review-gate` job will not run successfully.

## CI pipeline behavior

Workflow: `.github/workflows/ci.yml`
- Trigger: `pull_request` and push to `main`
- Jobs:
  - `lint`: Ruff
  - `tests`: pytest
  - `bandit`: static security checks
  - `dependency-scan`: pip-audit
  - `ai-review-gate`: Codex action on PRs only, reads `AGENTS.md`, outputs markdown + JSON, fails when:
    - `overall_risk_score >= 6`, or
    - any finding severity is `HIGH`

Optional security workflow: `.github/workflows/codeql.yml`.

Artifact note:
- `artifacts/` is CI-generated at runtime (`mkdir -p artifacts` in workflow) and does not need to be committed.
- Review outputs are uploaded as a GitHub Actions artifact (`codex-ai-review`).
- Dependency scan currently ignores `GHSA-7f5h-v6xp-fcq8` in CI because available FastAPI versions in this demo constrain Starlette to `<0.49.0`.

## Branch simulation for demo

Target model:
- `main` = fixed secure code (expected passing CI)
- `intentionally-bad` = vulnerable baseline (expected failing CI)

Use these exact commands:

```bash
# Start from fixed main state
git checkout -B main
git add .
git commit -m "feat: fixed secure FastAPI CI/CD demo"

# Create intentionally bad branch from main and inject issues
git checkout -b intentionally-bad
./scripts/make_bad_changes.sh
git add .
git commit -m "feat: intentionally vulnerable baseline for CI failure demo"
git push -u origin intentionally-bad

# Create PR intentionally-bad -> main (expected FAIL)
# Use GitHub UI or gh CLI

# Create fix branch from intentionally-bad and restore secure state
git checkout -b fix-from-bad
./scripts/make_fix_changes.sh
git add .
git commit -m "fix: remediate security and quality issues"
git push -u origin fix-from-bad

# Create PR fix-from-bad -> main (expected PASS)
```

## What fails in intentionally-bad

- Ruff: style/quality issues in `app/main.py`.
- Bandit: hardcoded secret, shell command execution, injection-prone patterns.
- pip-audit: vulnerable dependency (`jinja2==2.10`), while CI ignores only `GHSA-7f5h-v6xp-fcq8`.
- AI gate: flags high-risk findings and likely score >= 6.

## Short expected output snippets

Ruff example:
```text
F401 [*] ... imported but unused
```

Bandit example:
```text
B602 subprocess_popen_with_shell_equals_true
B105 hardcoded_password_string
```

pip-audit example:
```text
Found 1 known vulnerability in 1 package
```

AI gate example:
```json
{
  "overall_risk_score": 9,
  "findings": [
    {"severity": "HIGH", "category": "command-injection"}
  ]
}
```
