# GitHub Actions Setup

This document explains how to set up the automated fantasy league stats update workflow.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret** and add each of the following:

### Secrets to Add

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `LEAGUE_ID` | Your ESPN Fantasy League ID | `123456` |
| `YEAR` | The fantasy season year | `2024` |
| `ESPN_S2` | ESPN authentication cookie (for private leagues) | `AEBxxx...` |
| `SWID` | ESPN SWID cookie (for private leagues) | `{XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` |

### How to Find ESPN Authentication Cookies

For private leagues, you need to obtain the `ESPN_S2` and `SWID` cookies:

1. Log in to your ESPN Fantasy Basketball league in your browser
2. Open Browser Developer Tools (F12 or right-click > Inspect)
3. Go to the **Application** or **Storage** tab
4. Navigate to **Cookies** > `https://fantasy.espn.com`
5. Find and copy the values for:
   - `espn_s2` (copy the entire value)
   - `SWID` (copy the entire value including the curly braces)

**Note**: These cookies expire periodically, so you'll need to update them in GitHub Secrets when they do.

## Workflow Details

The workflow (`.github/workflows/update-stats.yml`) will:

1. **Trigger**:
   - Automatically runs daily at 2 AM PST (10 AM UTC)
   - Can be manually triggered from the Actions tab

2. **Process**:
   - Sets up Python environment
   - Installs dependencies
   - Creates `settings.py` with your secrets
   - Runs `generate_stats.py`
   - Copies `output/league_stats.html` to `index.html`
   - Commits and pushes changes (only if there are updates)

3. **Permissions**:
   - Requires `contents: write` permission (already configured in the workflow)

## Manual Trigger

To manually trigger the workflow:

1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. Select **Update Fantasy League Stats** from the workflows list
4. Click **Run workflow** > **Run workflow**

## Viewing the Results

After the workflow runs, the updated `index.html` will be available:
- In your repository's main branch
- If you have GitHub Pages enabled, it will be live at your GitHub Pages URL

## Troubleshooting

If the workflow fails:

1. Check the Actions logs for error messages
2. Verify all four secrets are correctly set
3. Ensure your ESPN cookies haven't expired (re-copy from browser if needed)
4. Verify your league ID and year are correct
