"""Builds media-kit/<key>/index.html for every kit in data/manual.json from media-kit.html.

Run after changing media-kit.html or adding a kit: python3 scripts/make_kits.py
"""
import json, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
manual = json.loads((root / "data/manual.json").read_text())
base = (root / "media-kit.html").read_text()
for key, kit in (manual.get("kits") or {}).items():
    label = kit.get("label", key)
    html = (base
            .replace("<head>", '<head>\n<base href="/">', 1)
            .replace('<body data-page="kit">', f'<body data-page="kit" data-kit="{key}">', 1)
            .replace("<title>Media kit ·", f"<title>{label} media kit ·", 1)
            .replace('content="Media kit ·', f'content="{label} media kit ·', 1)
            .replace(">Media kit</div>", f">Media kit · {label}</div>", 1))
    out = root / "media-kit" / key / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print("wrote", out.relative_to(root))
