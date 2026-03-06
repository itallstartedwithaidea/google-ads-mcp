# Publishing to PyPI

Releases use **PyPI Trusted Publishing** — no API tokens needed.

## How it works

1. You create a GitHub Release (e.g. tag `v0.3.0`)
2. The `publish.yml` workflow triggers automatically
3. It builds the package with `python -m build`
4. PyPI's trusted publisher verifies the GitHub Actions OIDC token
5. Package is published to PyPI as `googleadsagent-mcp`

## One-time PyPI setup

Before your first publish, register the trusted publisher on PyPI:

1. Go to [pypi.org](https://pypi.org) and sign in (or create an account)
2. Go to **Your projects** → **Publishing** → **Add a new pending publisher**
3. Fill in:
   - **PyPI project name**: `googleadsagent-mcp`
   - **Owner**: `itallstartedwithaidea`
   - **Repository**: `google-ads-mcp`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Click **Add**

## One-time GitHub setup

Create the `pypi` environment in your repo:

1. Go to **Settings → Environments → New environment**
2. Name it `pypi`
3. Optionally add deployment protection rules (e.g. require approval)

## Creating a release

1. Update the version in `pyproject.toml`:
   ```toml
   version = "0.3.0"
   ```
2. Commit and push
3. Go to **Releases → Draft a new release**
4. Tag: `v0.3.0` (create new tag)
5. Title: `v0.3.0`
6. Describe what changed
7. Click **Publish release**

The workflow runs automatically. Check the **Actions** tab for status.

## Version scheme

Follow [semver](https://semver.org):
- `0.x.y` — pre-1.0 development (current)
- Bump minor (`0.3.0` → `0.4.0`) for new tools or features
- Bump patch (`0.3.0` → `0.3.1`) for bug fixes
