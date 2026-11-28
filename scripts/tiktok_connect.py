#!/usr/bin/env python3
"""One-time: swap the code from callback.html for a TikTok refresh token.
Run by the "Connect TikTok" workflow. Writes the token to .new_refresh_token
(never printed) so the workflow can save it as a repo secret."""
import json, os, sys, urllib.parse, urllib.request

code = urllib.parse.unquote(os.environ["CODE"].strip())
manual = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "manual.json")))
redirect = manual["site_url"].rstrip("/") + "/callback.html"
# The client key isn't secret (it's in the TikTok login link), so the one in
# manual.json wins; it must belong to the same app/sandbox as the client secret.
key = manual.get("tiktok_client_key") or os.environ.get("TIKTOK_CLIENT_KEY", "")
if os.environ.get("TIKTOK_CLIENT_KEY") and os.environ["TIKTOK_CLIENT_KEY"].strip() != key:
    print("Note: the TIKTOK_CLIENT_KEY secret differs from tiktok_client_key in manual.json; using manual.json.")
body = urllib.parse.urlencode({
    "client_key": key, "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
    "code": code, "grant_type": "authorization_code", "redirect_uri": redirect}).encode()
req = urllib.request.Request("https://open.tiktokapis.com/v2/oauth/token/", body,
                             {"Content-Type": "application/x-www-form-urlencoded"})
try:
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read())
except urllib.error.HTTPError as e:
    tok = json.loads(e.read() or b"{}")
if "refresh_token" not in tok:
    sys.exit(f"TikTok said: {tok.get('error')} {tok.get('error_description')} "
             "(codes expire after a few minutes and work once; open connect.html again. "
             "If it keeps saying expired, check TIKTOK_CLIENT_SECRET is the Sandbox client secret.)")
print("::add-mask::" + tok["refresh_token"])
print("::add-mask::" + tok.get("access_token", "x"))
print("Connected. Scopes granted:", tok.get("scope"))
missing = {"user.info.stats", "video.list"} - set((tok.get("scope") or "").split(","))
if missing:
    print("WARNING: missing scopes", missing, "- the sync needs these")
open(os.path.join(os.path.dirname(__file__), "..", ".new_refresh_token"), "w").write(tok["refresh_token"])
