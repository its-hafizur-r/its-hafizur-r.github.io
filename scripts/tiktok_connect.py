#!/usr/bin/env python3
"""One-time: swap the code from callback.html for a TikTok refresh token.
Run by the "Connect TikTok" workflow. Writes the token to .new_refresh_token
(never printed) so the workflow can save it as a repo secret."""
import json, os, sys, urllib.parse, urllib.request

code = urllib.parse.unquote(os.environ["CODE"].strip())
manual = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "manual.json")))
redirect = manual["site_url"].rstrip("/") + "/callback.html"
body = urllib.parse.urlencode({
    "client_key": os.environ["TIKTOK_CLIENT_KEY"], "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
    "code": code, "grant_type": "authorization_code", "redirect_uri": redirect}).encode()
req = urllib.request.Request("https://open.tiktokapis.com/v2/oauth/token/", body,
                             {"Content-Type": "application/x-www-form-urlencoded"})
try:
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read())
except urllib.error.HTTPError as e:
    tok = json.loads(e.read() or b"{}")
if "refresh_token" not in tok:
    sys.exit(f"TikTok said: {tok.get('error')} {tok.get('error_description')} "
             "(codes expire after a few minutes and work once; open connect.html again)")
print("::add-mask::" + tok["refresh_token"])
print("::add-mask::" + tok.get("access_token", "x"))
print("Connected. Scopes granted:", tok.get("scope"))
missing = {"user.info.stats", "video.list"} - set((tok.get("scope") or "").split(","))
if missing:
    print("WARNING: missing scopes", missing, "- the sync needs these")
open(os.path.join(os.path.dirname(__file__), "..", ".new_refresh_token"), "w").write(tok["refresh_token"])
