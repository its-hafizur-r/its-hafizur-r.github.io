# hafizur_r: link in bio + media kit

- **Home (link in bio):** `index.html`, the page to put in your TikTok bio.
- **Media kit:** `media-kit.html`, linked from the top button on the home page.

Free hosting on GitHub Pages. Stats refresh every day by themselves.

## Change things (works from your phone)
Everything you'd want to change is in **`data/manual.json`**. Open it on github.com or in the GitHub app, tap the pencil, edit, then **Commit changes**. The site updates in about a minute.

| You want to change | Edit this in `manual.json` |
| --- | --- |
| Colour scheme | `"theme"`: `sunset`, `midnight`, `minimal` or `matcha` |
| Buttons on the home page | `"bio_links"` (add, remove or reorder) |
| Bio, intro, location, email | `"tagline"`, `"intro"`, `"location"`, `"email"` |
| Audience numbers | `"audience"` (copy from TikTok Studio once a month) |
| Content types, brands, collab options | `"pillars"`, `"brands"`, `"services"` |
| How averages are worked out | `"stats_settings"` |

Don't edit `data/stats.json`; the robot overwrites it daily.
Custom colours and layout live in `style.css` (colours are at the top).

## How the stats work
`.github/workflows/sync-stats.yml` runs `scripts/sync_tiktok.py` every day:
- With the TikTok API connected (see **SETUP-TIKTOK.md**) it uses the official TikTok Display API.
- Until then it reads your public TikTok profile.

It writes followers, total likes, video count, average views and likes, engagement rate
((likes + comments + shares) ÷ views over videos from the last 30 days, the same window the weekly stats report uses),
and your top videos with thumbnails.

## Changing the web address
The site is at `https://its-hafizur-r.github.io`. To use a custom domain, add it under
**Settings → Pages → Custom domain**, then update `"site_url"` in `manual.json` and the
TikTok app's URLs and Redirect URI.
