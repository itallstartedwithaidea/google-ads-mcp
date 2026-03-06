# Connecting to Google Ads API

Five steps to get your credentials. Takes about 20 minutes.

## Step 1: Get a Developer Token

1. Sign into [Google Ads](https://ads.google.com)
2. Go to **Tools & Settings → Setup → API Center**
   - Direct URL: `https://ads.google.com/aw/apicenter`
3. If you don't see API Center, you need a **Manager (MCC) account** — create one at [ads.google.com/home/tools/manager-accounts](https://ads.google.com/home/tools/manager-accounts/)
4. Copy your **Developer Token** — it looks like `aBcDeFgHiJkLmNoPqRs`
5. Your token starts with **Test Account** access. This is fine for development. Apply for **Basic** or **Standard** access when you're ready for production.

## Step 2: Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Ads API**:
   - Navigate to **APIs & Services → Library**
   - Search for "Google Ads API" → click **Enable**
4. Create OAuth credentials:
   - Go to **APIs & Services → Credentials**
   - Click **+ Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: anything (e.g. "Google Ads MCP")
   - Click **Create**
5. Copy the **Client ID** and **Client Secret**
   - Client ID looks like: `123456789-abcdefg.apps.googleusercontent.com`
   - Client Secret looks like: `GOCSPX-abcdefghijklmnop`

## Step 3: Get a Refresh Token

1. Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
2. Click the **gear icon** (top right) → check **Use your own OAuth credentials**
3. Paste your **Client ID** and **Client Secret** from Step 2
4. In the left panel, find **Google Ads API v23** and select `https://www.googleapis.com/auth/adwords`
5. Click **Authorize APIs** → sign in with the Google account that has access to your Ads accounts
6. Click **Exchange authorization code for tokens**
7. Copy the **Refresh Token** — it looks like `1//0abCdEfGhIjKlMnOpQrStUvWxYz...`

> The refresh token does not expire unless you revoke it or change your password. Store it securely.

## Step 4: Find your Account / MCC ID

- **Single account**: Your customer ID is the 10-digit number shown in the top-right of Google Ads (e.g. `123-456-7890`)
- **MCC (Manager account)**: Use the MCC's customer ID as `GOOGLE_ADS_LOGIN_CUSTOMER_ID`. Individual sub-account IDs are passed per-tool call as `customer_id`.

## Step 5: Create your credentials file

Create a file called `google-ads.yaml`:

```yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID.apps.googleusercontent.com
client_secret: GOCSPX-YOUR_CLIENT_SECRET
refresh_token: 1//YOUR_REFRESH_TOKEN
login_customer_id: "1234567890"  # MCC ID without dashes, quoted
```

Then point your `.env` at it:

```bash
GOOGLE_ADS_CREDENTIALS=/path/to/google-ads.yaml
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
```

## Verify it works

```bash
python scripts/validate.py
```

You should see:

```
✓ Credentials loaded
✓ API connection successful
✓ Found N accessible accounts
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `DEVELOPER_TOKEN_NOT_APPROVED` | Your token is test-only. Either use a test account or apply for Basic access. |
| `OAUTH_TOKEN_INVALID` | Refresh token expired or revoked. Redo Step 3. |
| `CUSTOMER_NOT_FOUND` | Wrong `login_customer_id`. Make sure it's your MCC ID without dashes. |
| `USER_PERMISSION_DENIED` | The Google account you authorized doesn't have access to this Ads account. |
| `AUTHORIZATION_ERROR` | Check that Google Ads API is enabled in Cloud Console (Step 2.3). |
