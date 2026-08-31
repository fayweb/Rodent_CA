# -*- coding: utf-8 -*-
"""Render Merke field cards from species_data.json.

Two-part card by design:
  1. Facts table  - measurements/activity/burrow dimensions. Safe to publish as is.
  2. Source block - Plazi/HMW text quoted verbatim, clearly delimited so it can be
                    deleted and replaced with protocol prose before publication.
"""
import io, json, html, sys

DATA = "species_data.json"
OUT = "merke_cards.html"
OUT_FIELD = "merke_cards_field.html"

# Sections a field card keeps. Everything else - Food and Feeding, Breeding,
# Home range and social organisation - is reference reading, not trap-line
# reading, and lives in the full version only.
FIELD_SECTIONS = ["Habitat", "Activity patterns", "Burrow"]
FIELD = False

# H. B. Sherman Traps model tiers, from the manufacturer's own compare-traps page
# (shermantraps.com/compare-traps/). Dimensions and target animals are the
# manufacturer's; assigning a Central Asian species to a tier is our judgement and
# is shown on the card so it can be checked.
TIERS = {
    "small":  ("Small",  "SFA / SNA, 2 x 2.5 x 6.5 in (5.1 x 6.4 x 16.5 cm)",
               "mice, shrews, voles"),
    "medium": ("Medium", "LFAHD / LFATDG, 3 x 3.5 x 9 in (7.6 x 8.9 x 22.9 cm)",
               "chipmunks, rats, flying squirrels"),
    "large":  ("Large",  "XLKR / XLKSD, 3 x 3.5 x 13 in (7.6 x 8.9 x 33 cm)",
               "kangaroo rats, ground squirrels, squirrels"),
    "too_large": ("Too large", "no Sherman model fits",
                  "record the sighting or sign; do not expect a capture"),
}

# Above this mass no Sherman model in the range is appropriate. The largest model
# is offered for ground squirrels, so the ceiling sits above them and below marmots.
TOO_LARGE_G = 1500


def hi(s):
    """Return (low, high) ints from a '90-120' style range string."""
    try:
        parts = [int(x) for x in str(s).replace("–", "-").split("-") if x.strip().isdigit()]
        return (parts[0], parts[-1]) if parts else (None, None)
    except Exception:
        return (None, None)


def sherman_tier(sp):
    """Map a species to a manufacturer trap tier.

    Body size sets the default; body_type can override it. Jerboas are mapped to
    the large tier because the manufacturer lists kangaroo rats there, and a
    saltatorial animal needs the length its hind legs and tail demand.
    """
    if sp.get("sherman_tier"):
        return sp["sherman_tier"], sp.get("sherman_basis", "set manually")

    wt_hi = hi(sp["measurements"].get("weight_g", ""))[1]
    if wt_hi and wt_hi > TOO_LARGE_G:
        return "too_large", "reaches %d g, well above the largest model's intended animals" % wt_hi

    if sp.get("body_type") == "saltatorial":
        return "large", ("bipedal hopper; manufacturer places kangaroo rats, "
                         "the closest body type it names, in this tier")

    hb = hi(sp["measurements"]["head_body_mm"])[1]
    wt = hi(sp["measurements"].get("weight_g", ""))[1]
    if hb is None:
        return "unknown", "no head-body figure"
    basis = "head-body to %d mm, to %s g" % (hb, wt if wt else "?")
    if hb <= 110 and (wt or 0) <= 45:
        return "small", basis
    if hb <= 200 and (wt or 0) <= 350:
        return "medium", basis
    return "large", basis


def diel_class(sp):
    a = sp["activity_class"].lower()
    if "diurnal" in a and "nocturnal" not in a and "crepuscular" not in a:
        return "day"
    if "diurnal" in a or "day" in a:
        return "both"
    return "night"


CSS = """
/* Arial throughout, black and white, so it prints anywhere. Photographs are the
   only colour on the page. Where colour previously carried meaning it is now
   carried by fill density: solid black is the strongest signal, mid grey next,
   outline weakest. */
:root{
  --paper:#fff; --card:#fff; --ink:#000; --mut:#3d3d3d; --faint:#6b6b6b;
  --line:#000; --rule:#c9c9c9; --wash:#f2f2f2; --mid:#d8d8d8;
  --sans:Arial,Helvetica,"Liberation Sans",sans-serif;
  --serif:Arial,Helvetica,"Liberation Sans",sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0d0d0d; --card:#141414; --ink:#f2f2f2; --mut:#c2c2c2; --faint:#8f8f8f;
  --line:#f2f2f2; --rule:#3a3a3a; --wash:#1c1c1c; --mid:#2e2e2e;
}}
:root[data-theme="dark"]{
  --paper:#0d0d0d; --card:#141414; --ink:#f2f2f2; --mut:#c2c2c2; --faint:#8f8f8f;
  --line:#f2f2f2; --rule:#3a3a3a; --wash:#1c1c1c; --mid:#2e2e2e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:15px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:820px;margin:0 auto;padding:26px 18px 60px;
  display:flex;flex-direction:column;gap:22px}

.masthead{border-bottom:3px solid var(--ink);padding-bottom:12px}
.masthead h1,h1{font-size:26px;line-height:1.15;margin:0 0 6px;font-weight:700;
  text-wrap:balance;letter-spacing:-.01em}
.masthead p,.lede{margin:0;color:var(--mut);font-size:13.5px;max-width:64ch}

.banner{background:var(--wash);border:1px solid var(--line);border-left:6px solid var(--ink);
  padding:12px 16px;font-size:13.5px;line-height:1.45}
.banner b{font-weight:700}

.card,.sec{background:var(--card);border:1px solid var(--line);
  padding:20px 22px;page-break-after:always;display:flex;flex-direction:column}
.sec{page-break-after:auto}
.card:last-child{page-break-after:auto}

h2{font-size:20px;line-height:1.2;margin:0;font-weight:700;text-wrap:balance}
h3{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--faint);
  font-weight:700;margin:20px 0 6px}
.sci{font-style:italic;color:var(--mut);font-size:14.5px;margin:2px 0 0}
.aka{color:var(--faint);font-size:12.5px;margin:2px 0 0}
p{max-width:66ch}

.tags{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
.tag{font-size:11.5px;font-weight:700;padding:3px 9px;border:1px solid var(--ink);
  letter-spacing:.02em;text-transform:uppercase}
.t-grp{background:transparent;color:var(--ink)}
.t-here{background:transparent;color:var(--mut);border-color:var(--rule)}
.t-day{background:var(--ink);color:var(--paper)}
.t-both{background:var(--mid);color:var(--ink)}
.t-night{background:transparent;color:var(--ink)}

.scroll{overflow-x:auto;margin:0 0 2px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule);vertical-align:top}
th{background:var(--wash);color:var(--ink);font-size:10.5px;font-weight:700;
  text-transform:uppercase;letter-spacing:.07em;border-bottom:2px solid var(--ink)}
tr:last-child td{border-bottom:none}
td.n{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}

.sec-label,.sec>div.sec,.card .sec{}
div.sec{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--faint);
  font-weight:700;margin:18px 0 6px;border:none;padding:0;background:none;display:block}
.verdict{font-weight:700}
.v-small,.v-medium,.v-large{color:var(--ink)}
.v-too_large,.v-unknown{color:var(--faint)}
.note{font-size:11.5px;color:var(--faint);margin:5px 0 0;max-width:64ch}

.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.fig{margin:0;border:1px solid var(--rule);overflow:hidden;background:var(--paper);
  display:flex;flex-direction:column}
.fig img{display:block;width:100%;height:auto}
.fig figcaption{padding:6px 8px;font-size:11.5px;line-height:1.35;color:var(--mut);
  display:flex;flex-direction:column;gap:2px}
.fig .credit{font-size:10.5px;color:var(--faint)}
.fig .credit a{color:var(--faint)}
.fig.empty{border-style:dashed}
.ph{padding:14px 10px;min-height:92px;display:flex;flex-direction:column;
  justify-content:center;gap:5px;text-align:center}
.phlab{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.09em}
.phbrief{font-size:11.5px;line-height:1.35;color:var(--faint)}

.quoted{border:1px solid var(--rule);border-left:4px solid var(--mut);
  background:var(--wash);padding:12px 15px;margin-top:4px}
.qhead{font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:var(--faint);
  font-weight:700;margin-bottom:9px}
.qh{font-weight:700;font-size:12.5px;margin:12px 0 2px}
.qh:first-of-type{margin-top:0}
.qt{font-size:13.5px;line-height:1.45;color:var(--mut);margin:0;max-width:68ch}
.cite{font-size:11.5px;color:var(--faint);margin-top:11px;padding-top:8px;
  border-top:1px solid var(--rule)}
.cite a{color:var(--mut)}

.check,.trap{background:transparent;border:1px solid var(--ink);border-left:6px solid var(--ink);
  padding:10px 14px;margin-top:14px;font-size:12.5px}
.check b,.trap .k{font-weight:700}
.check ul{margin:5px 0 0 17px;padding:0}
.check li+li{margin-top:4px}
.trap p{margin:0;max-width:64ch}
.k{font-weight:700}

a:focus-visible{outline:2px solid var(--ink);outline-offset:2px}

@media print{
  :root{--paper:#fff;--card:#fff;--ink:#000;--mut:#2b2b2b;--faint:#5a5a5a;
        --line:#000;--rule:#bbb;--wash:#f4f4f4;--mid:#dcdcdc}
  body{background:#fff;color:#000;font-size:10.5pt}
  .wrap{max-width:none;padding:0;gap:0}
  .card,.sec{border:none;padding:0 0 8px;margin:0}
  .masthead{page-break-after:avoid}
  .quoted,.check,.trap,.banner,.fig,table{break-inside:avoid}
  .fig.empty{display:none}          /* blank photo slots waste paper */
  .figs{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}

  /* Backgrounds are off by default when printing, so carry the activity
     distinction in border weight, which always prints. */
  .tag{background:transparent!important;color:#000!important}
  .t-day{border:2.5px solid #000!important;font-weight:700}
  .t-both{border:1.5px solid #000!important}
  .t-night{border:1px solid #777!important;color:#333!important}
  .t-grp,.t-here{border:1px solid #bbb!important;color:#333!important}
  th{background:transparent!important;border-bottom:2px solid #000!important}
  .quoted,.banner{background:transparent!important}
  .banner{border:1.5px solid #000!important;border-left:6px solid #000!important}
  a{text-decoration:none;color:#000}
  .field body{font-size:9.5pt}
  .field .card{padding:0 0 4px}
  .field div.sec{margin:12px 0 4px}
  .field .quoted{padding:9px 12px}
}
"""

MEAS = [("head_body_mm", "Head-body", "mm"), ("tail_mm", "Tail", "mm"),
        ("ear_mm", "Ear", "mm"), ("hindfoot_mm", "Hind foot", "mm"),
        ("weight_g", "Weight", "g")]

# Three image slots per card. An empty slot renders as the shot to take, so the
# card doubles as the photographic shot list until the picture exists.
IMG_SLOTS = [
    ("animal", "Whole animal",
     "In the hand, dorsal view, whole animal in frame with a scale bar."),
    ("detail", "Diagnostic detail",
     "The feature that separates this species from its confusion pair, with a scale bar."),
    ("sign", "Burrow or field sign",
     "Burrow entrance, runway, mound or hay pile, with a scale object for size."),
]


def figures(sp):
    """Image strip. Filled slots show the picture; empty slots show what to shoot."""
    e = html.escape
    imgs = sp.get("images", {})
    o = ['<div class="sec">Pictures</div><div class="figs">']
    for key, label, default_brief in IMG_SLOTS:
        img = imgs.get(key)
        brief = sp.get("shot_list", {}).get(key, default_brief)
        if img and img.get("file"):
            cap = img.get("caption", label)
            credit = img.get("credit", "")
            lic = img.get("licence", "")
            src = img.get("source_url", "")
            meta = " · ".join(x for x in [credit, lic] if x)
            if src:
                meta = '<a href="%s">%s</a>' % (e(src), e(meta or "source"))
            else:
                meta = e(meta)
            o.append('<figure class="fig"><img src="%s" alt="%s">'
                     '<figcaption>%s<span class="credit">%s</span></figcaption></figure>'
                     % (e(img["file"]), e(cap), e(cap), meta))
        else:
            o.append('<figure class="fig empty"><div class="ph">'
                     '<span class="phlab">%s</span><span class="phbrief">%s</span>'
                     '</div></figure>' % (e(label), e(brief)))
    o.append('</div>')
    return "\n".join(o)


def card(sp):
    e = html.escape
    o = ['<div class="card">']
    o.append('<h2>%s</h2>' % e(sp["common"]))
    o.append('<p class="sci">%s</p>' % e(sp["binomial"]))
    if sp.get("also_known_as"):
        o.append('<p class="aka">Also listed as <i>%s</i></p>' % e(sp["also_known_as"]))

    o.append('<div class="tags">')
    o.append('<span class="tag t-grp">%s</span>' % e(sp["group"]))
    o.append('<span class="tag t-here">%s</span>' % e(sp["merke_status"]))
    o.append('<span class="tag t-%s">%s</span>' % (diel_class(sp), e(sp["activity_class"])))
    o.append('</div>')

    m = sp["measurements"]
    o.append('<div class="sec">Measurements</div><div class="scroll"><table><tr>')
    o.append("".join('<th>%s</th>' % lbl for _, lbl, _ in MEAS))
    o.append('</tr><tr>')
    o.append("".join('<td class="n">%s %s</td>' % (e(m.get(k, "—")), u) for k, _, u in MEAS))
    o.append('</tr></table></div>')

    o.append('<div class="sec">When to trap</div><div class="scroll"><table>')
    o.append('<tr><th>Activity</th><th>Emerges</th><th>September at Merke</th></tr>')
    o.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr></table></div>' % (
        e(sp["activity_class"]), e(sp["emerges"]), e(sp["september"])))

    tier, basis = sherman_tier(sp)
    label, dims, targets = TIERS.get(tier, ("Unknown", "—", "—"))
    o.append('<div class="sec">Which Sherman</div><div class="scroll"><table>')
    o.append('<tr><th>Tier</th><th>Model and size</th><th>Manufacturer lists</th></tr>')
    o.append('<tr><td class="verdict v-%s">%s</td><td>%s</td><td>%s</td></tr></table></div>'
             % (tier, e(label), e(dims), e(targets)))
    o.append('<p class="note">Assigned on %s. Tiers and dimensions are the '
             'manufacturer\'s; placing this species in one is our judgement.</p>' % e(basis))

    o.append(figures(sp))

    o.append('<div class="sec">Source text</div><div class="quoted">')
    o.append('<div class="qhead">Quoted verbatim — replace with protocol prose before publication</div>')
    items = sp["quotes"].items()
    if FIELD:
        items = [(k, sp["quotes"][k]) for k in FIELD_SECTIONS if k in sp["quotes"]]
    for h, t in items:
        o.append('<div class="qh">%s</div><p class="qt">%s</p>' % (e(h), e(t)))
    o.append('<div class="cite">%s. Plazi treatment, <a href="%s">%s</a>, licence %s.</div>'
             % (e(sp["citation"]), e(sp["zenodo"]), e(sp["doi"]), e(sp["licence"])))
    o.append('</div>')

    if sp.get("ocr_check"):
        o.append('<div class="check"><b>Check against the printed page before field use</b><ul>')
        o.extend('<li>%s</li>' % e(c) for c in sp["ocr_check"])
        o.append('</ul></div>')

    o.append('</div>')
    return "\n".join(o)


DIEL_LABEL = {"day": "Day", "both": "Day and night", "night": "Night"}


def summary(species):
    """Overview page: what is catchable at Merke in September, and when."""
    e = html.escape
    o = ['<div class="card">']
    o.append('<h2>September at Merke — what is catchable, and when</h2>')

    o.append('<div class="banner"><b>Traps run through the day, checked twice: dawn and '
             'midday.</b> Much of this community is active while an overnight-only line is shut. '
             'The species below marked Day or Day and night are the reason for the second check. '
             'Shade every trap that stays set through the day.</div>')

    active_day = [s for s in species if diel_class(s) in ("day", "both")
                  and sherman_tier(s)[0] != "too_large"]
    asleep = [s for s in species if s["september"].split(".")[0].strip().lower()
              in ("largely unavailable", "going underground", "juveniles only", "marginal")]

    o.append('<div class="sec">Active while the traps are closed</div><div class="scroll"><table>')
    o.append('<tr><th>Species</th><th>Group</th><th>Active</th><th>Emerges</th><th>Trap</th></tr>')
    for s in sorted(active_day, key=lambda x: (diel_class(x) != "day", x["common"])):
        tier = sherman_tier(s)[0]
        o.append('<tr><td><b>%s</b><br><i style="color:var(--mut)">%s</i></td><td>%s</td>'
                 '<td class="verdict t-%s">%s</td><td>%s</td><td>%s</td></tr>'
                 % (e(s["common"]), e(s["binomial"]), e(s["group"].split(" - ")[0]),
                    diel_class(s), e(DIEL_LABEL[diel_class(s)]), e(s["emerges"]),
                    e(TIERS[tier][0])))
    o.append('</table></div>')

    o.append('<div class="sec">Reduced or gone by September</div><div class="scroll"><table>')
    o.append('<tr><th>Species</th><th>Status in September</th></tr>')
    for s in sorted(asleep, key=lambda x: x["common"]):
        o.append('<tr><td><b>%s</b><br><i style="color:var(--mut)">%s</i></td><td>%s</td></tr>'
                 % (e(s["common"]), e(s["binomial"]), e(s["september"])))
    o.append('</table></div>')

    o.append('<div class="check"><b>Bait: one size does not fit this community</b><ul>'
             '<li>Shrews are insectivores. The lesser white-toothed shrew eats over 100% of its '
             'body weight daily, so a seed bait does not feed it and it starves quickly in a trap. '
             'An animal-protein component and a short check interval both matter.</li>'
             '<li>Voles and the dwarf fat-tailed jerboa are folivores, eating green material '
             'rather than seed.</li>'
             '<li>The eastern mole vole eats underground tubers and rarely comes to the surface '
             'at all.</li>'
             '<li>Brown rats are neophobic and may avoid a new trap for a night or two, which '
             'argues for pre-baiting.</li></ul></div>')

    o.append('</div>')
    return "\n".join(o)


def main():
    global FIELD
    FIELD = "--field" in sys.argv
    out = OUT_FIELD if FIELD else OUT
    d = json.load(io.open(DATA, encoding="utf-8"))
    o = ['<title>%s</title>' % ("Merke Field Cards" if FIELD else "Merke Small Mammal Cards"),
         '<style>%s</style>' % CSS,
         '<div class="wrap%s">' % (" field" if FIELD else "")]
    o.append('<header class="masthead"><h1>Merke small mammal cards</h1>'
             '<p>Merke State Regional Nature Park, Zhambyl Region, Kazakhstan. '
             'September 2026 trapping season. %d species covering everything in the region '
             'that could enter a Sherman trap, plus the larger animals whose sign is easily '
             'confused with theirs.</p></header>' % len(d["species"]))
    o.append('<div class="banner"><b>Trip draft.</b> '
             'Boxed source text is quoted verbatim from Plazi treatments on Zenodo (CC0), '
             'extracted from the Handbook of the Mammals of the World. It is cited but not yet '
             'rewritten into protocol voice; before publication each boxed block is replaced. '
             'Plazi OCR loses decimal points, so any figure flagged for checking must be verified '
             'against the printed page before it is relied on in the field.</div>')
    o.append(summary(d["species"]))
    o.extend(card(sp) for sp in d["species"])
    o.append('</div>')
    io.open(out, "w", encoding="utf-8").write("\n".join(o))
    keys = FIELD_SECTIONS if FIELD else None
    words = sum(len(" ".join(
        sp["quotes"][k] for k in (keys or list(sp["quotes"]))
        if k in sp["quotes"]).split()) for sp in d["species"]) / float(len(d["species"]))
    print("wrote %s (%d cards, mean %d quoted words each)" % (out, len(d["species"]), words))


if __name__ == "__main__":
    main()
