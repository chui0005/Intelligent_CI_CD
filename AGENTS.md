# AGENTS Instructions

## Review Guidelines
Use these rules for CI AI review outputs.

### Severity model
- `HIGH`: hardcoded secrets, command injection, SQL/NoSQL injection patterns, authentication bypass, remote code execution patterns.
- `MEDIUM`: missing or weak input validation, sensitive-data logging, weak crypto/auth patterns, missing auth on dangerous routes.
- `LOW`: style issues, maintainability concerns, minor refactor opportunities.

### Required output contract
- Always return:
  - Markdown summary for humans.
  - JSON with:
    - `findings[]` objects: `{id, title, file, line_range, severity, category, description, suggested_fix}`
    - `overall_risk_score` from 0 to 10.
- Every finding must reference precise file path and line range.
- Suggested fixes must be concrete and implementation-ready.

### Risk scoring guidance
- Start from 0.
- Add +4 for each confirmed `HIGH` finding.
- Add +2 for each `MEDIUM` finding.
- Add +1 for each `LOW` finding.
- Cap final score at 10.
