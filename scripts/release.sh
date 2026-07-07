#!/usr/bin/env bash
#
# Portalcrane - Release helper
#
# Bumps the frontend version, commits it, creates the matching git tag and
# pushes everything. Because the version bump is committed *before* the tag is
# created, the tag points at the commit that contains the correct version — so
# the release built from that tag always matches the tag name.
#
# Usage:
#   scripts/release.sh <version|patch|minor|major> [--no-push]
#
# Examples:
#   scripts/release.sh 3.7.1        # explicit version
#   scripts/release.sh patch        # 3.7.0 -> 3.7.1 (from latest git tag)
#   scripts/release.sh minor        # 3.7.0 -> 3.8.0
#   scripts/release.sh major        # 3.7.0 -> 4.0.0
#   scripts/release.sh patch --no-push   # create commit + tag locally only
#
set -euo pipefail

# ── Locate the repo root so the script works from anywhere ────────────────────
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

FRONTEND_DIR="frontend"

# ── Parse arguments ───────────────────────────────────────────────────────────
if [ $# -lt 1 ]; then
  echo "Usage: scripts/release.sh <version|patch|minor|major> [--no-push]" >&2
  exit 1
fi

BUMP="$1"
PUSH=1
if [ "${2:-}" = "--no-push" ]; then
  PUSH=0
fi

# ── Compute the target version ────────────────────────────────────────────────
# The latest *git tag* is the source of truth for releases (frontend/package.json
# has historically drifted from it).
latest_tag="$(git tag --list --sort=-v:refname | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | head -1 || true)"
latest_tag="${latest_tag:-0.0.0}"

case "$BUMP" in
  patch | minor | major)
    IFS='.' read -r major minor patch <<<"$latest_tag"
    case "$BUMP" in
      major) major=$((major + 1)); minor=0; patch=0 ;;
      minor) minor=$((minor + 1)); patch=0 ;;
      patch) patch=$((patch + 1)) ;;
    esac
    VERSION="${major}.${minor}.${patch}"
    ;;
  *)
    # Explicit version — strip an optional leading "v".
    VERSION="${BUMP#v}"
    ;;
esac

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Invalid version '$VERSION' (expected semver X.Y.Z)" >&2
  exit 1
fi

# ── Safety checks ─────────────────────────────────────────────────────────────
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Working tree is not clean — commit or stash your changes first." >&2
  git status --short >&2
  exit 1
fi

if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
  echo "❌ Tag '$VERSION' already exists." >&2
  exit 1
fi

echo "🔖 Releasing version $VERSION (latest tag was $latest_tag)"

# ── Bump the frontend version (no tag created by npm — we tag ourselves) ──────
npm --prefix "$FRONTEND_DIR" version "$VERSION" --no-git-tag-version >/dev/null
echo "✅ Bumped $FRONTEND_DIR/package.json to $VERSION"

# ── Commit, tag ───────────────────────────────────────────────────────────────
git add "$FRONTEND_DIR/package.json" "$FRONTEND_DIR/package-lock.json"
git commit -m "chore(release): $VERSION"
git tag "$VERSION"
echo "✅ Committed bump and created tag $VERSION"

# ── Push (unless --no-push) ───────────────────────────────────────────────────
if [ "$PUSH" -eq 1 ]; then
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git push origin "$branch"
  git push origin "$VERSION"
  echo "🚀 Pushed $branch and tag $VERSION"
else
  echo "ℹ️  Skipped push (--no-push). Run: git push origin HEAD $VERSION"
fi
