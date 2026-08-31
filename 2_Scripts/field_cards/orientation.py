# -*- coding: utf-8 -*-
"""Build a personal orientation guide to the small mammal groups of Central Asia.

This is a learning document for Fay, not manual content. Every number is computed
from species_data.json, and every ecological statement traces to the Plazi/HMW
treatments quoted there. The interpretive prose - what separates the groups, what
it means for trapping - is written here and is synthesis, not quotation.

Usage:  python orientation.py     then open orientation.html
"""
import io, json, re, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA = "species_data.json"
OUT = "orientation.html"

# Order each family sits in. Taken from the HMW volume the treatment came from:
# Vol 6 Lagomorphs and Rodents I, Vol 7 Rodents II, Vol 8 Insectivores.
ORDERS = {
    "Rodentia": ["Sminthidae - birch mice", "Dipodidae - jerboas",
                 "Cricetidae - voles", "Cricetidae - hamsters",
                 "Muridae - mice and rats", "Gerbillinae",
                 "Sciuridae", "Hystricidae"],
    "Eulipotyphla": ["Soricidae - shrews", "Erinaceidae"],
    "Lagomorpha": ["Ochotonidae", "Leporidae"],
}

ORDER_NOTE = {
    "Rodentia": "Rodents. One pair of continuously growing incisors in each jaw, "
                "no canines, a long gap where the canines would be. Everything you "
                "will routinely catch is here.",
    "Eulipotyphla": "Shrews and hedgehogs. Not rodents at all — insectivores with "
                    "many small sharp teeth and a pointed, mobile snout. Distant "
                    "relatives of moles, closer to bats than to mice.",
    "Lagomorpha": "Pikas, hares and rabbits. A second small pair of incisors sits "
                  "directly behind the front pair, which no rodent has.",
}

# Written for this guide. Facts behind each are in the quoted treatments.
PROFILE = {
    "Dipodidae - jerboas": {
        "what": "Bipedal desert hoppers. The most distinctive animals you will handle.",
        "tell": "The hind foot settles it. At a mean of 61 mm it is two to four times "
                "longer than anything else of similar body size, and the tail is longer "
                "than the head and body with a tuft at the tip. They stand and move on "
                "the hind legs.",
        "eco": "Desert and semi-desert, each species tied to a particular substrate — "
               "loose sand, hard soil, clay or gravel. Burrows are simple, usually with "
               "the main entrance plugged from inside, so you are looking for a soil or "
               "sand plug rather than an open hole. Most keep separate short night-shelter "
               "burrows scattered across the home range.",
        "trap": "All hibernate, so the September window is closing: most go down from "
                "mid-to-late October, but Allactaga major and Pygeretmus pumilio can start "
                "at the end of September. They emerge on a tight schedule after sunset and "
                "in autumn may be active for only an hour. They need the longest Sherman.",
    },
    "Sminthidae - birch mice": {
        "what": "Tiny long-tailed climbers of the mountain meadows. Their own family, "
                "not jerboas, despite once being lumped with them.",
        "tell": "Smallest thing you will catch after the shrews, at 7 to 13 g, with a "
                "tail about 1.7 times the head and body — proportionally the longest tail "
                "of any group here.",
        "eco": "Foothill to subalpine, densest at the upper forest limit. Agile climbers "
               "that nest in decaying stumps as well as underground. Diet leans towards "
               "insects and snails, shifting to seeds and berries into autumn.",
        "trap": "Two things matter. Adults enter hibernation in August, so in September "
                "you will almost certainly be handling juveniles only. And after a cold "
                "night they are found curled and apparently dead but revive when warmed "
                "in the hand — do not record a torpid one as a mortality.",
    },
    "Gerbillinae": {
        "what": "Gerbils and jirds. Desert specialists, and the group carrying the most "
                "public health weight in Kazakhstan.",
        "tell": "Tail about as long as the head and body, hind foot around 36 mm, soles "
                "often furred. Larger and longer-footed than the true mice they otherwise "
                "resemble.",
        "eco": "Sandy and clay desert, strongly associated with shrub cover — burrows go "
               "in at the base of bushes and under roots. Burrow systems are the largest "
               "and most structured of any group here, with separate nest and food-storage "
               "chambers and multiple entrances. They cache heavily.",
        "trap": "The great gerbil is diurnal and most active at dawn, which an "
                "overnight-only line misses almost entirely. Jirds are mostly nocturnal "
                "but the Libyan jird feeds by day in parts of its range. None hibernate.",
    },
    "Muridae - mice and rats": {
        "what": "True mice and rats. The family you already know from house mice.",
        "tell": "Tail roughly equal to head and body, large ears, pointed face, hind foot "
                "around 25 mm — shorter than a gerbil of the same body length.",
        "eco": "The broadest habitat range of any group, from forest edge to arable land "
               "to inside buildings. Burrows are simple and shallow compared with gerbils. "
               "Mostly omnivorous with seeds dominating.",
        "trap": "Apodemus agrarius is the important one for your schedule: diurnal or "
                "crepuscular, and among the most frequently recorded species near Merke. "
                "Brown rats are neophobic and may avoid a new trap for a night or two, "
                "which argues for pre-baiting. The three Apodemus-type mice are hard to "
                "separate in the hand, so photograph the dorsal stripe, ear and hind foot.",
    },
    "Cricetidae - voles": {
        "what": "Voles and mole voles. Grazers of the grass and rock.",
        "tell": "Blunt rounded face, small ears often buried in fur, and a short tail — "
                "under a third of the head and body, the clearest single difference from "
                "a mouse.",
        "eco": "Grassland, alpine meadow and talus. Two quite different lifestyles sit "
               "here: Microtus and Lasiopodomys dig shallow tunnel systems with many "
               "entrances and cut surface runways; Alticola does not dig at all and lives "
               "in rock fissures; Ellobius is fully fossorial and rarely surfaces.",
        "trap": "The group most poorly served by an overnight line — Microtus arvalis is "
                "crepuscular and diurnal, Alticola is diurnal with peaks at 05:00–07:00 "
                "and 18:00–20:00, and Lasiopodomys shifts towards daytime activity "
                "specifically in autumn. All are folivores, so a seed bait is a poor "
                "match. Ellobius may not enter a surface trap at all.",
    },
    "Cricetidae - hamsters": {
        "what": "Dwarf hamsters. Small, solitary hoarders.",
        "tell": "Short tail like a vole but a sharper face and visible ears, plus cheek "
                "pouches. Tail length separates the two species: 19–39 mm in the grey "
                "dwarf hamster, 35–48 mm in the long-tailed.",
        "eco": "Arid grassland, steppe and piedmont semi-desert. Burrows have dedicated "
               "storage chambers — the grey dwarf hamster stockpiles 400–500 g of food — "
               "and both build surface hay piles in late summer.",
        "trap": "Neither hibernates, so both are available all September. Mostly nocturnal "
                "and crepuscular, though the grey dwarf hamster is sometimes active by day "
                "even in cold weather. Omnivorous, so the standard bait suits them well.",
    },
    "Sciuridae": {
        "what": "Ground squirrels and marmots. Diurnal, social, and mostly asleep when "
                "you arrive.",
        "tell": "No confusion possible on size. Marmots reach 4–6.5 kg; the yellow ground "
                "squirrel 273 g to over a kilogram.",
        "eco": "Open steppe and mountain meadow. Colonial, with conspicuous burrow mounds "
               "that animals sit on to watch, and whistled alarm calls.",
        "trap": "Effectively unavailable in September. Yellow ground squirrel adults begin "
                "hibernating in late July, marmots are underground for seven to eight "
                "months. Marmots fit no Sherman. Their burrow systems are on the cards so "
                "you do not mistake them for a target species' sign.",
    },
    "Soricidae - shrews": {
        "what": "Shrews. Not rodents — insectivores with a metabolism that makes them the "
                "biggest welfare risk in the trap line.",
        "tell": "Tiny, 6 to 12 g, with a long pointed mobile snout, minute eyes and no "
                "rodent gnawing teeth. Tail around half the head and body.",
        "eco": "Grass and scrub near water, and readily inside buildings and yurts. "
               "Insect and invertebrate feeders that hunt continuously.",
        "trap": "The lesser white-toothed shrew eats over its own body weight daily and "
                "starves fast in a trap; seed bait does not feed it, which is why the "
                "cookie's tinned sprats matter. Crocidura is mostly nocturnal but Sorex "
                "tundrensis is active day and night. Short check intervals are a welfare "
                "requirement, not a preference.",
    },
    "Erinaceidae": {
        "what": "The long-eared hedgehog. Spiny, nocturnal, and at the top of the size range.",
        "tell": "Unmistakable. Ears conspicuously long for a hedgehog, up to 60 mm.",
        "eco": "Dry riverbeds, dunes and shrub valleys, often close to human settlement. "
               "Digs a short burrow with a single opening under a bush.",
        "trap": "At 230–400 g it is at or beyond the top of the largest Sherman. An "
                "omnivore that can go weeks without food, and enters torpor opportunistically "
                "in any season.",
    },
    "Ochotonidae": {
        "what": "The Turkestan red pika. A lagomorph, not a rodent.",
        "tell": "No visible tail at all, round ears, and a second pair of incisors behind "
                "the first. Nothing else here looks like it.",
        "eco": "Talus and rock crevice specialist between 1800 and 3700 m. Does not burrow. "
               "Cuts and stacks hay piles of 0.3 to 2 kg, sometimes 3 to 8 kg, in crevices.",
        "trap": "Diurnal, active sunrise to dusk, and available through September — hay "
                "hoarding runs until then, so the piles are a reliable sign. Set at crevices "
                "and talus edges rather than at burrow entrances, because there are none.",
    },
    "Hystricidae": {
        "what": "The Indian crested porcupine. Present, relevant, and not catchable.",
        "tell": "Quills.",
        "eco": "Steppe and desert margin. Digs extensive burrow systems with tunnels over "
               "10 m long, used by family groups for decades.",
        "trap": "Fits no Sherman. It is on the cards because its burrow systems are large "
                "and can be mistaken for a target species' sign, and because the quills are "
                "a safety matter.",
    },
    "Leporidae": {
        "what": "The tolai hare. Also present, also not catchable.",
        "tell": "Size, ears of 80–120 mm, and a hind foot over 110 mm.",
        "eco": "Grassland and mountain steppe. Does not burrow — rests in a surface scrape "
               "called a form, and follows fixed foraging routes.",
        "trap": "Fits no Sherman. Its runs are easily mistaken for rodent runways, which is "
                "the reason it earns a card.",
    },
}


def hi(s):
    p = [int(x) for x in re.split(r"[-–]", str(s)) if x.strip().isdigit()]
    return (p[0], p[-1]) if p else (None, None)


def mid(s):
    lo, h = hi(s)
    return (lo + h) / 2.0 if lo is not None else None


def stats(sp_list):
    hbs, ratios, hfs, wts = [], [], [], []
    for s in sp_list:
        m = s["measurements"]
        hb, tl, hf, wt = (mid(m.get("head_body_mm")), mid(m.get("tail_mm")),
                          mid(m.get("hindfoot_mm")), mid(m.get("weight_g")))
        if hb: hbs.append(hb)
        if hb and tl: ratios.append(tl / hb)
        if hf: hfs.append(hf)
        if wt: wts.append(wt)
    avg = lambda v: sum(v) / len(v) if v else None
    return avg(hbs), avg(ratios), avg(hfs), avg(wts)


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
}
"""


def main():
    d = json.load(io.open(DATA, encoding="utf-8"))
    fam = defaultdict(list)
    for s in d["species"]:
        fam[s["group"]].append(s)

    o = ['<title>Small Mammals of Central Asia</title>',
         '?family=PT+Sans:ital,wght@0,400;0,700;1,400&family=PT+Serif:ital,wght@0,400;0,700;1,400'
         '&display=swap">',
         '<style>%s</style>' % CSS, '<div class="wrap">']

    o.append('<header class="masthead"><h1>Small mammals of Central Asia</h1>'
             '<p class="lede">An orientation to the groups you are trapping at Merke: how '
             'they are related, how to tell them apart in the hand, how they live, and what '
             'each difference means for a trap line. Measurements are computed from the '
             '%d species on the field cards; the ecology traces to the same CC0 treatments. '
             'The interpretation is written for this guide.</p></header>' % len(d["species"]))

    # --- the tree -------------------------------------------------------
    o.append('<section class="sec"><h2>Three orders, twelve groups</h2>'
             '<p>Everything you will handle sits in one of three orders. Only the first '
             'contains rodents, and the distinction matters more than it sounds: a shrew '
             'is no more a rodent than a hedgehog is, and it will die in a trap far faster '
             'than a mouse will.</p>')
    for order, fams in ORDERS.items():
        present = [f for f in fams if f in fam]
        if not present:
            continue
        n = sum(len(fam[f]) for f in present)
        o.append('<div class="order"><p class="order-h">%s <span style="color:var(--faint);'
                 'font-size:14px;font-family:var(--sans)">%d species</span></p>'
                 '<p class="order-n">%s</p><div class="fams">' % (order, n, ORDER_NOTE[order]))
        for f in present:
            genera = sorted({s["binomial"].split()[0] for s in fam[f]})
            o.append('<div class="fam"><b>%s</b> <span>%s</span></div>'
                     % (f.split(" - ")[0], ", ".join(genera)))
        o.append('</div></div>')
    o.append('</section>')

    # --- the shape key --------------------------------------------------
    o.append('<section class="sec"><h2>Placing an animal by shape alone</h2>'
             '<p>Tail length relative to head and body separates the groups more cleanly '
             'than anything else, and you can judge it by eye before reaching for callipers. '
             'Hind foot then splits the two long-tailed groups. These figures are the mean '
             'across the species in each group.</p><div class="scroll"><table>'
             '<tr><th>Group</th><th>Tail ÷ head-body</th><th>Head-body</th>'
             '<th>Hind foot</th><th>Weight</th></tr>')
    rows = []
    for f, sp in fam.items():
        hb, ratio, hf, wt = stats(sp)
        rows.append((ratio if ratio else -1, f, hb, ratio, hf, wt))
    for _, f, hb, ratio, hf, wt in sorted(rows, reverse=True):
        bar = ('<span class="bar" style="width:%dpx"></span>' % int((ratio or 0) * 46)) if ratio else ""
        o.append('<tr><td>%s</td><td class="n">%s%s</td><td class="n">%s</td>'
                 '<td class="n">%s</td><td class="n">%s</td></tr>'
                 % (f, bar, ("%.2f" % ratio) if ratio else "no tail",
                    ("%.0f mm" % hb) if hb else "—",
                    ("%.0f mm" % hf) if hf else "—",
                    ("%.0f g" % wt) if wt else "—"))
    o.append('</table></div>'
             '<p style="margin-top:14px"><span class="k">How to read it.</span> Above 1.0 the '
             'tail is longer than the body: jerboas and birch mice, told apart by hind foot — '
             'about 61 mm against 18 mm. Around 0.9 the tail roughly equals the body: gerbils '
             'and true mice, again split by hind foot, 36 mm against 25 mm. Below 0.35 the tail '
             'is short: voles, hamsters and ground squirrels. Around 0.45 with a pointed snout '
             'and a body under 12 g, it is a shrew. No tail at all means pika.</p></section>')

    # --- profiles -------------------------------------------------------
    o.append('<section class="sec"><h2>The groups</h2>')
    order_seq = [f for fams in ORDERS.values() for f in fams if f in fam]
    for f in order_seq:
        p = PROFILE.get(f)
        if not p:
            continue
        genera = sorted({s["binomial"].split()[0] for s in fam[f]})
        o.append('<div class="prof"><h2>%s</h2><p class="gen">%s · %d species on the cards</p>'
                 % (f.split(" - ")[0], ", ".join(genera), len(fam[f])))
        o.append('<p>%s</p>' % p["what"])
        o.append('<h3>Knowing it in the hand</h3><p>%s</p>' % p["tell"])
        o.append('<h3>How it lives</h3><p>%s</p>' % p["eco"])
        o.append('<div class="trap"><p><span class="k">For the trap line.</span> %s</p></div>'
                 % p["trap"])
        o.append('</div>')
    o.append('</section>')


    # --- home range against the grid ------------------------------------
    GRID = 90 * 90  # a 10 x 10 grid at 10 m spacing spans 90 m
    o.append('<section class="sec"><h2>Home range against your grid</h2>'
             '<p>A 10 by 10 grid at 10 m spacing spans 90 m, so it covers '
             '<b>8,100 m&sup2;, about 0.81 ha</b>. Whether that is a large sample or a '
             'pinprick depends entirely on how far the animal moves, and the range across '
             'these species is enormous. The figures are quoted on each card; the '
             'comparison below is arithmetic done here.</p><div class="scroll"><table>'
             '<tr><th>Species</th><th>Home range</th><th>Against the grid</th>'
             '<th>Traps inside one range</th></tr>')
    hr_rows = []
    for s in d["species"]:
        hr = s.get("home_range_m2")
        if hr:
            hr_rows.append(((hr[0] + hr[1]) / 2.0, s, hr))
    for midv, s, hr in sorted(hr_rows, key=lambda r: r[0]):
        ratio = GRID / midv
        rel = ("grid is %.0f&times; the range" % ratio) if ratio >= 1               else ("range is %.0f&times; the grid" % (1 / ratio))
        traps = midv / 100.0
        o.append('<tr><td><b>%s</b></td><td class="n">%s&ndash;%s m&sup2;</td>'
                 '<td>%s</td><td class="n">%s</td></tr>'
                 % (s["common"], format(hr[0], ","), format(hr[1], ","), rel,
                    ("%.0f" % traps) if traps >= 1 else "fewer than 1"))
    o.append('</table></div>'
             '<div class="trap"><p><span class="k">What this means.</span> For a vole, a '
             'pika or a striped field mouse the grid spans six to fifteen home ranges, so '
             'it samples a population and every animal has several traps available. For a '
             "great jerboa the whole grid sits inside a single animal&rsquo;s range, a hundred "
             "times over — you are not sampling a population, you are sampling one or two "
             "individuals&rsquo; living space. The same grid is a different instrument depending "
             'on which animal walks into it, which is worth holding onto when the grid and '
             'transect results are compared.</p></div></section>')

    # --- social organisation --------------------------------------------
    o.append('<section class="sec"><h2>Solitary, family or colonial</h2>'
             '<p>This is the biology underneath the difference between working a burrow '
             'colony and running a grid. A grid laid over a colonial species samples the '
             'colony rather than the population; a grid over a solitary species with a '
             'large range may sample almost nobody.</p><div class="scroll"><table>'
             '<tr><th>Species</th><th>Group</th><th>Social organisation</th></tr>')
    for s in sorted(d["species"], key=lambda x: (x.get("social") or "zz", x["common"])):
        soc = s.get("social")
        if not soc or soc == "Not stated":
            continue
        o.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>'
                 % (s["common"], s["group"].split(" - ")[0], soc))
    o.append('</table></div></section>')

    # --- activity comparison --------------------------------------------
    o.append('<section class="sec"><h2>When each group is awake</h2>'
             '<p>This is the axis that decides whether your traps are open at the right '
             'hours, and it does not follow the family tree — diurnal and nocturnal habits '
             'sit side by side within the same group.</p><div class="scroll"><table>'
             '<tr><th>Species</th><th>Group</th><th>Activity</th><th>September</th></tr>')
    for s in sorted(d["species"], key=lambda x: (x["group"], x["common"])):
        o.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (s["common"], s["group"].split(" - ")[0],
                    s["activity_class"], s["september"]))
    o.append('</table></div></section>')

    o.append('<p class="foot">Built from species_data.json. Ecological statements trace to '
             'Plazi taxonomic treatments (CC0) extracted from the Handbook of the Mammals of '
             'the World; per-species DOIs are on the field cards. Measurements are means '
             'across each group and are for orientation, not identification — use the '
             'per-species ranges on the cards for that.</p>')
    o.append('</div>')
    io.open(OUT, "w", encoding="utf-8").write("\n".join(o))
    print("wrote %s — %d groups, %d species" % (OUT, len(fam), len(d["species"])))


if __name__ == "__main__":
    main()
