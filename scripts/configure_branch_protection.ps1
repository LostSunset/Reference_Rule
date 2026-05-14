# Configure GitHub branch protection for this rule-pack repository.
#
# Intended policy:
# - normal collaborators must use pull requests
# - owner/admins can still push directly
# - conversations must be resolved before merge

param(
  [string]$Repository = "LostSunset/Reference_Rule",
  [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

$Payload = @{
  required_status_checks = $null
  enforce_admins = $false
  required_pull_request_reviews = @{
    required_approving_review_count = 1
    dismiss_stale_reviews = $true
    require_code_owner_reviews = $false
    require_last_push_approval = $false
  }
  restrictions = $null
  required_conversation_resolution = $true
  allow_force_pushes = $false
  allow_deletions = $false
  block_creations = $false
  required_linear_history = $false
  allow_fork_syncing = $true
  lock_branch = $false
} | ConvertTo-Json -Depth 10

$Payload | gh api `
  --method PUT `
  -H "Accept: application/vnd.github+json" `
  -H "X-GitHub-Api-Version: 2022-11-28" `
  "/repos/$Repository/branches/$Branch/protection" `
  --input -

Write-Host "Branch protection configured for $Repository@$Branch"

