# Connect the TikTok API (one-time setup)

Until this is done, the site still updates every day from your public TikTok profile.
Connecting the API makes the numbers official and more complete (every video, not just the ones the public pages show).

Everything below works on your phone, but steps 1 to 3 are easier on a laptop.
Your site address below is `https://its-hafizur-r.github.io`. If you change it, use the new one everywhere.

## 1. Create a TikTok developer account
1. Go to **developers.tiktok.com** and tap **Log in**. Sign in with your normal TikTok account.
2. Accept the developer terms. Choose **Individual** (not organisation) if asked.

## 2. Create the app
1. Open **Manage apps** and tap **Connect an app** (or **Create app**).
2. Fill in:
   - **App name:** `Hafizur Media Kit`
   - **App icon:** any square image, 1024 x 1024 (your profile photo is fine)
   - **Category:** Lifestyle (or Social)
   - **Description:** `Shows my own TikTok follower count, likes and video stats on my personal media kit website. Read-only.`
   - **Terms of Service URL:** `https://its-hafizur-r.github.io/terms.html`
   - **Privacy Policy URL:** `https://its-hafizur-r.github.io/privacy.html`
   - **Platform:** Web, website `https://its-hafizur-r.github.io`
3. If TikTok asks you to **verify the URL** (URL properties), choose *URL prefix*, download the `.txt` file it gives you, and send it to Claude in the project thread. Claude adds it to the site; then tap **Verify**.

## 3. Add Login Kit and the scopes
1. Under **Products**, add **Login Kit** (and **Display API** if it's listed separately).
2. In Login Kit, set the **Redirect URI** to exactly:
   `https://its-hafizur-r.github.io/callback.html`
3. Under **Scopes**, tick: `user.info.basic`, `user.info.profile`, `user.info.stats`, `video.list`.

## 4. Sandbox now, review later
- **Sandbox (works today):** switch the app to **Sandbox**, open **Target users** and add your own account `@hafizur_r`. Sandbox works straight away for your own account.
- **Production (optional, takes a few days):** tap **Submit for review**. Explain it reads only your own account to show stats on your media kit, and attach a short screen recording of you opening `connect.html`, approving, and the media kit page. Once approved, repeat step 5's keys if TikTok gives you new production ones.

## 5. Put the keys into GitHub
From the app's page, copy the **Client key** and **Client secret**.

1. In your repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**. Add:
   - `TIKTOK_CLIENT_KEY` = the client key
   - `TIKTOK_CLIENT_SECRET` = the client secret
2. Make a GitHub token so the robot can save your TikTok login:
   go to **github.com/settings/personal-access-tokens/new** (fine-grained token)
   - Name: `media kit`, Expiration: 1 year
   - Repository access: **Only select repositories** → `its-hafizur-r.github.io`
   - Permissions → Repository: **Secrets: Read and write**, **Actions: Read and write**
   - Generate, copy it, and add it as another repo secret called `GH_PAT`.
3. Edit `data/manual.json` and paste the client key (not the secret) into `"tiktok_client_key"`. The key isn't secret; it's shown in the TikTok login link anyway.

## 6. Connect
1. Open **https://its-hafizur-r.github.io/connect.html** and tap **Continue with TikTok**. Approve.
2. You land on a page with a code. Tap **Copy code**, then **Open the Connect TikTok workflow**.
3. Tap **Run workflow**, paste the code, and run it. It must be within a few minutes.
4. It saves your login and starts a stats sync. When it finishes, `data/stats.json` shows `"source": "tiktok_api"`.

That's it. The **Sync TikTok stats** workflow runs every morning at 06:17 UK time in winter (07:17 in summer), and you can tap **Run workflow** on it any time for an instant refresh.

## If something breaks
- **Sync fails with a token error:** the login expired (TikTok logins last a year) or was revoked. Do step 6 again.
- **"redirect_uri" error on TikTok:** the Redirect URI in step 3 doesn't exactly match the site address plus `/callback.html`.
- **Missing scopes warning:** tick all four scopes in step 3, then do step 6 again.
