#!/usr/bin/env python3
"""Refresh data/stats.json for the media kit. Standard library only.

Two sources, picked automatically:
  * TikTok Display API  - used when TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET and
                          TIKTOK_REFRESH_TOKEN are set (GitHub repo secrets).
  * Public profile pages - fallback until the TikTok app is approved.

Writes:
  data/stats.json          numbers the page shows
  data/videos.json         cache of per-video stats (public mode)
  assets/covers/<id>.jpg   thumbnails for the top videos
  .new_refresh_token       only if TikTok handed back a new refresh token
                           (the workflow saves it as a secret, then deletes it)
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, "data", "manual.json")
STATS = os.path.join(ROOT, "data", "stats.json")
CACHE = os.path.join(ROOT, "data", "videos.json")
COVERS = os.path.join(ROOT, "assets", "covers")
API = "https://open.tiktokapis.com/v2"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def http(url, data=None, headers=None, tries=3):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code < 500 or i == tries - 1:
                raise RuntimeError(f"HTTP {e.code} for {url.split('?')[0]}: {body}")
        except urllib.error.URLError:
            if i == tries - 1:
                raise
        time.sleep(3 * (i + 1))


# ------------------------------------------------------------------ API source
class TikTokAPI:
    name = "tiktok_api"

    def __init__(self, key, secret, refresh):
        body = urllib.parse.urlencode({
            "client_key": key, "client_secret": secret,
            "grant_type": "refresh_token", "refresh_token": refresh}).encode()
        tok = json.loads(http(f"{API}/oauth/token/", body,
                              {"Content-Type": "application/x-www-form-urlencoded"}))
        if "access_token" not in tok:
            sys.exit(f"TikTok token refresh failed: {tok.get('error')} {tok.get('error_description')}")
        self.token = tok["access_token"]
        new = tok.get("refresh_token")
        if new and new != refresh:
            with open(os.path.join(ROOT, ".new_refresh_token"), "w") as f:
                f.write(new)

    def _call(self, path, fields, body=None):
        url = f"{API}{path}?fields={fields}"
        h = {"Authorization": f"Bearer {self.token}"}
        data = None
        if body is not None:
            h["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        out = json.loads(http(url, data, h))
        err = out.get("error", {})
        if err.get("code") not in (None, "ok"):
            sys.exit(f"TikTok API error on {path}: {err}")
        return out["data"]

    def profile(self):
        u = self._call("/user/info/", "display_name,avatar_url,follower_count,"
                       "following_count,likes_count,video_count")["user"]
        return {"followers": u.get("follower_count", 0), "following": u.get("following_count", 0),
                "likes": u.get("likes_count", 0), "videos": u.get("video_count", 0),
                "avatar_url": u.get("avatar_url")}

    def videos(self, limit=200):
        fields = ("id,title,video_description,create_time,cover_image_url,share_url,"
                  "view_count,like_count,comment_count,share_count")
        out, cursor = [], None
        while len(out) < limit:
            body = {"max_count": 20}
            if cursor:
                body["cursor"] = cursor
            d = self._call("/video/list/", fields, body)
            for v in d.get("videos", []):
                out.append({
                    "id": v["id"],
                    "title": (v.get("title") or v.get("video_description") or "")[:140],
                    "created": int(v.get("create_time", 0)),
                    "views": v.get("view_count", 0), "likes": v.get("like_count", 0),
                    "comments": v.get("comment_count", 0), "shares": v.get("share_count", 0),
                    "cover_src": v.get("cover_image_url"),
                    "url": v.get("share_url")})
            if not d.get("has_more"):
                break
            cursor = d.get("cursor")
        return out

    def query(self, ids):
        fields = ("id,title,video_description,create_time,cover_image_url,share_url,"
                  "view_count,like_count,comment_count,share_count")
        out = []
        for i in range(0, len(ids), 20):
            d = self._call("/video/query/", fields, {"filters": {"video_ids": ids[i:i + 20]}})
            for v in d.get("videos", []):
                out.append({
                    "id": v["id"], "title": (v.get("title") or v.get("video_description") or "")[:140],
                    "created": int(v.get("create_time", 0)), "views": v.get("view_count", 0),
                    "likes": v.get("like_count", 0), "comments": v.get("comment_count", 0),
                    "shares": v.get("share_count", 0), "cover_src": v.get("cover_image_url"),
                    "url": v.get("share_url")})
        return out


# --------------------------------------------------------------- public source
class PublicPages:
    """Only pages anyone can open without signing in."""
    name = "public_profile"

    def __init__(self, handle):
        self.handle = handle

    def _scope(self, url):
        html = http(url, headers={"Accept-Language": "en-GB,en;q=0.9"}).decode("utf-8", "replace")
        m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.S)
        return json.loads(m.group(1)).get("__DEFAULT_SCOPE__", {}) if m else {}

    def profile(self):
        d = self._scope(f"https://www.tiktok.com/@{self.handle}")
        info = d["webapp.user-detail"]["userInfo"]
        s = info.get("statsV2") or info["stats"]
        return {"followers": int(s["followerCount"]), "following": int(s["followingCount"]),
                "likes": int(s["heartCount"]), "videos": int(s["videoCount"]),
                "avatar_url": info.get("user", {}).get("avatarLarger")}

    def _recent_ids(self):
        try:
            html = http(f"https://www.tiktok.com/embed/@{self.handle}").decode("utf-8", "replace")
            return set(re.findall(r'"id":"(7\d{18})"', html))
        except Exception as e:  # noqa: BLE001
            print("  embed list failed:", e)
            return set()

    def videos(self, limit=200, extra=()):
        cache = load(CACHE, {"seed_ids": [], "videos": {}})
        ids = set(cache.get("seed_ids", [])) | set(cache.get("videos", {})) | self._recent_ids()
        ids = sorted(ids, reverse=True)[:limit]
        ids = list(dict.fromkeys(list(extra) + ids))
        for vid in ids:
            time.sleep(1.2)
            try:
                d = self._scope(f"https://www.tiktok.com/@{self.handle}/video/{vid}")
            except Exception as e:  # noqa: BLE001
                print("  skip", vid, e)
                continue
            it = d.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct")
            if not it or (it.get("author") or {}).get("uniqueId", "").lower() != self.handle.lower():
                continue
            s = it.get("statsV2") or it["stats"]
            v = it.get("video", {})
            cache["videos"][vid] = {
                "id": vid, "title": it.get("desc", "")[:140], "created": int(it["createTime"]),
                "views": int(s["playCount"]), "likes": int(s["diggCount"]),
                "comments": int(s["commentCount"]), "shares": int(s["shareCount"]),
                "cover_src": v.get("cover") or v.get("originCover"),
                "url": f"https://www.tiktok.com/@{self.handle}/video/{vid}"}
        save(CACHE, cache)
        return list(cache["videos"].values())


# ------------------------------------------------------------------- the maths
def summarise(videos, days, min_videos, skip_days, now):
    """Videos posted in the last `days` days (leaving out ones younger than
    `skip_days`, which are still gaining views). If that is fewer than
    `min_videos`, use the latest `min_videos` videos instead."""
    cutoff = now - skip_days * 86400
    settled = sorted((v for v in videos if v["created"] <= cutoff),
                     key=lambda v: v["created"], reverse=True)
    in_window = [v for v in settled if v["created"] >= now - days * 86400]
    settled = in_window if len(in_window) >= min_videos else settled[:min_videos]
    n = len(settled)
    if not n:
        return None
    tot = {k: sum(v[k] for v in settled) for k in ("views", "likes", "comments", "shares")}
    eng = tot["likes"] + tot["comments"] + tot["shares"]
    return {
        "videos_counted": n,
        "window_days": days,
        "avg_views": round(tot["views"] / n),
        "avg_likes": round(tot["likes"] / n),
        "avg_comments": round(tot["comments"] / n),
        "avg_shares": round(tot["shares"] / n),
        "engagement_rate": round(100 * eng / tot["views"], 2) if tot["views"] else 0,
        "from": dt.date.fromtimestamp(settled[-1]["created"]).isoformat(),
        "to": dt.date.fromtimestamp(settled[0]["created"]).isoformat(),
    }


def fetch_cover(src, dest):
    try:
        data = http(src, headers={"Referer": "https://www.tiktok.com/"}, tries=2)
        if len(data) > 1000:
            with open(dest, "wb") as f:
                f.write(data)
            return True
    except Exception as e:  # noqa: BLE001
        print("  cover failed:", str(e)[:120])
    return os.path.exists(dest)


def main():
    manual = load(MANUAL, {})
    cfg = manual.get("stats_settings", {})
    handle = manual.get("handle", "hafizur_r")
    key, secret, refresh = (os.environ.get(k, "").strip() for k in
                            ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"))
    src = TikTokAPI(key, secret, refresh) if key and secret and refresh else PublicPages(handle)
    print("source:", src.name)

    old = load(STATS, {})
    now = time.time()
    featured_ids = []
    for f in manual.get("featured_videos", []):
        m = re.search(r"(\d{17,20})", str(f))
        if m:
            featured_ids.append(m.group(1))
    profile = src.profile()
    videos = src.videos(extra=featured_ids) if isinstance(src, PublicPages) else src.videos(limit=2000)
    by_id = {str(v["id"]): v for v in videos}
    missing = [i for i in featured_ids if i not in by_id]
    if missing and isinstance(src, TikTokAPI):
        for v in src.query(missing):
            by_id[str(v["id"])] = v
    print(f"  profile ok, {len(videos)} videos")

    recent = summarise(videos, int(cfg.get("window_days", 30)), int(cfg.get("min_videos", 8)),
                       int(cfg.get("skip_newer_than_days", 2)), now)

    os.makedirs(COVERS, exist_ok=True)

    def tile(v):
        rel = f"assets/covers/{v['id']}.jpg"
        has = fetch_cover(v["cover_src"], os.path.join(ROOT, rel)) if v.get("cover_src") \
            else os.path.exists(os.path.join(ROOT, rel))
        return ({k: v[k] for k in ("id", "title", "views", "likes", "comments", "shares", "created")}
                | {"url": v.get("url") or f"https://www.tiktok.com/@{handle}/video/{v['id']}",
                   "cover": rel if has else None})

    top = sorted(videos, key=lambda v: v["views"], reverse=True)[:int(cfg.get("top_videos", 9))]
    top_out = [tile(v) for v in top]
    featured_out = [tile(by_id[i]) for i in featured_ids if i in by_id]
    keep = {f"{v['id']}.jpg" for v in top} | {f"{i}.jpg" for i in featured_ids}
    for f in os.listdir(COVERS):
        if f.endswith(".jpg") and f not in keep:
            os.remove(os.path.join(COVERS, f))

    avatar = os.path.join(ROOT, "assets", "avatar.jpg")
    if profile.get("avatar_url"):
        fetch_cover(profile["avatar_url"], avatar)

    total_views = sum(v["views"] for v in videos)
    stats = {
        "_note": "Written by scripts/sync_tiktok.py every day. Don't edit by hand; edit manual.json instead.",
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": src.name,
        "profile": {k: profile[k] for k in ("followers", "following", "likes", "videos")}
        | {"total_views": total_views,
           # True only when every video on the account was counted (API mode).
           "total_views_complete": len(videos) >= profile["videos"]},
        "recent": recent or old.get("recent"),
        "top_videos": top_out,
        "featured": featured_out,
    }
    save(STATS, stats)
    print(json.dumps(stats["profile"]), json.dumps(stats["recent"]))


if __name__ == "__main__":
    main()
