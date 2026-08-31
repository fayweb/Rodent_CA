# -*- coding: utf-8 -*-
"""Build a contact sheet for checking and swapping the field card photographs.

The API can tell us a photo is licensed and, when annotated, that it shows a whole
organism rather than tracks or scat. It cannot tell us the photo is any good. This
renders every chosen image beside the other open-licensed candidates so a human can
judge, and prints the command to swap one.

Usage:  python review_photos.py          then open photo_review.html
        python fetch_photos.py --pin "Allactaga major=232452773"
"""
import io, json, sys, time, urllib.parse, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA = "species_data.json"
OUT = "photo_review.html"
API = "https://api.inaturalist.org/v1/observations"
UA = {"User-Agent": "ZSL-WP4-fieldcards/1.0"}
EVL = {24: "organism", 25: "scat", 26: "track", 27: "bone", 28: "molt",
       31: "hair", 23: "feather"}
PLACES = ["KZ", "KG", "TJ", "TM", "UZ", None]


def gj(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30).read().decode())


def evidence(obs):
    for a in obs.get("annotations", []):
        if a.get("controlled_attribute_id") == 22:
            return EVL.get(a.get("controlled_value_id"), "other")
    return None


def candidates(name, limit=6):
    """Every open-licensed observation we could have used, best-annotated first."""
    seen, out = set(), []
    for cc in PLACES:
        q = {"taxon_name": name, "photo_license": "cc0,cc-by",
             "quality_grade": "research", "per_page": "20"}
        if cc:
            q["country_code"] = cc
        try:
            res = gj(API + "?" + urllib.parse.urlencode(q)).get("results", [])
        except Exception:
            res = []
        for o in res:
            if o["id"] in seen:
                continue
            for p in o.get("photos", []):
                if (p.get("license_code") or "").lower() in ("cc0", "cc-by"):
                    seen.add(o["id"])
                    out.append({
                        "id": o["id"], "ev": evidence(o), "cc": cc or "worldwide",
                        "url": p["url"].replace("/square.", "/medium."),
                        "lic": p["license_code"].upper(),
                        "who": (o.get("user") or {}).get("name")
                               or (o.get("user") or {}).get("login") or "unknown",
                        "where": o.get("place_guess") or "",
                    })
                    break
        time.sleep(0.4)
        if len(out) >= limit:
            break
    return out[:limit]


CSS = """
:root{--paper:#FBFAF8;--card:#fff;--ink:#16211D;--mut:#5C6763;--faint:#8A938F;
--line:#DDE3E0;--zsl:#00694E;--zsl-tint:#E9F1EE;--alert:#9A3B12;--alert-tint:#FBEDE5;
--sans:"PT Sans","Segoe UI",system-ui,sans-serif;--serif:"PT Serif",Georgia,serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1512;
--card:#18201D;--ink:#E7ECE9;--mut:#A3AEA9;--faint:#7C8783;--line:#2C3733;
--zsl:#5FBFA1;--zsl-tint:#0E2C23;--alert:#E08A5A;--alert-tint:#2E1B10}}
:root[data-theme="dark"]{--paper:#0F1512;--card:#18201D;--ink:#E7ECE9;--mut:#A3AEA9;
--faint:#7C8783;--line:#2C3733;--zsl:#5FBFA1;--zsl-tint:#0E2C23;--alert:#E08A5A;
--alert-tint:#2E1B10}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 var(--sans)}
.wrap{max-width:1100px;margin:0 auto;padding:28px 20px 70px;display:flex;
flex-direction:column;gap:22px}
h1{font-family:var(--serif);font-size:27px;margin:0 0 6px;color:var(--zsl)}
.lede{color:var(--mut);max-width:66ch;margin:0}
.row{background:var(--card);border:1px solid var(--line);border-radius:5px;padding:18px 20px}
.row h2{font-family:var(--serif);font-size:19px;margin:0 0 2px}
.row .sci{font-family:var(--serif);font-style:italic;color:var(--mut);font-size:14px;margin:0 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}
figure{margin:0;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--paper)}
figure.chosen{border:2px solid var(--zsl)}
figure img{display:block;width:100%;height:150px;object-fit:cover;background:var(--zsl-tint)}
figcaption{padding:7px 9px;font-size:12px;line-height:1.35;color:var(--mut)}
.badge{display:inline-block;font-size:10.5px;font-weight:700;text-transform:uppercase;
letter-spacing:.05em;padding:2px 6px;border-radius:3px;margin-bottom:4px}
.b-chosen{background:var(--zsl-tint);color:var(--zsl)}
.b-organism{background:var(--zsl-tint);color:var(--zsl)}
.b-none{background:var(--alert-tint);color:var(--alert)}
.oid{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:var(--faint)}
.warn{background:var(--alert-tint);border-left:3px solid var(--alert);padding:12px 16px;
border-radius:0 4px 4px 0;font-size:14px}
code{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;background:var(--zsl-tint);
padding:1px 5px;border-radius:3px}
a{color:var(--zsl)}
"""


def main():
    only_flagged = "--flagged" in sys.argv
    d = json.load(io.open(DATA, encoding="utf-8"))
    o = ['<title>Photo Review</title>',
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2'
         '?family=PT+Sans:wght@400;700&family=PT+Serif:ital@0;1&display=swap">',
         '<style>%s</style>' % CSS, '<div class="wrap">',
         '<div><h1>Photo review</h1><p class="lede">The chosen image is outlined in '
         'green. Everything beside it was also available and openly licensed. '
         'Badges show iNaturalist\'s evidence annotation: <b>organism</b> is verified '
         'as a whole animal, <b>unannotated</b> means nobody has said what it shows, '
         'so it could be tracks or scat.</p></div>',
         '<div class="warn">To swap one, note its observation id and run<br>'
         '<code>python fetch_photos.py --pin "Allactaga major=232452773"</code><br>'
         'then <code>python render_cards.py</code>.</div>']

    for sp in d["species"]:
        cur = sp.get("images", {}).get("animal")
        if not cur:
            continue
        cur_id = cur["source_url"].rsplit("/", 1)[-1]
        cands = candidates(sp["binomial"])
        cur_ev = next((c["ev"] for c in cands if str(c["id"]) == cur_id), None)
        if only_flagged and cur_ev == "organism":
            continue

        o.append('<div class="row"><h2>%s</h2><p class="sci">%s</p><div class="grid">'
                 % (sp["common"], sp["binomial"]))
        o.append('<figure class="chosen"><img src="%s" alt="current">'
                 '<figcaption><span class="badge b-chosen">In use</span><br>%s<br>'
                 '<span class="oid">obs %s</span></figcaption></figure>'
                 % (cur["file"], cur["credit"], cur_id))
        for c in cands:
            if str(c["id"]) == cur_id:
                continue
            cls = "b-organism" if c["ev"] == "organism" else "b-none"
            lab = c["ev"] or "unannotated"
            o.append('<figure><img src="%s" loading="lazy" alt="%s">'
                     '<figcaption><span class="badge %s">%s</span><br>%s<br>'
                     '<span class="oid">obs %s · %s</span> '
                     '<a href="https://www.inaturalist.org/observations/%s">open</a>'
                     '</figcaption></figure>'
                     % (c["url"], lab, cls, lab, c["who"], c["id"], c["cc"], c["id"]))
        o.append('</div></div>')
        print("  %s (%d alternatives)" % (sp["common"], max(0, len(cands) - 1)))

    o.append('</div>')
    io.open(OUT, "w", encoding="utf-8").write("\n".join(o))
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
