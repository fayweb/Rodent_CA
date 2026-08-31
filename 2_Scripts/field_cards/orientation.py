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
:root{--paper:#FBFAF8;--card:#fff;--ink:#16211D;--mut:#5C6763;--faint:#8A938F;
--line:#DDE3E0;--rule:#EEF1EF;--zsl:#00694E;--zsl-tint:#E9F1EE;--zsl-deep:#004F3A;
--alert:#9A3B12;--alert-tint:#FBEDE5;--calm:#3A3F6B;--calm-tint:#ECEDF5;
--serif:"PT Serif",Georgia,serif;--sans:"PT Sans","Segoe UI",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1512;
--card:#18201D;--ink:#E7ECE9;--mut:#A3AEA9;--faint:#7C8783;--line:#2C3733;--rule:#232D29;
--zsl:#5FBFA1;--zsl-tint:#0E2C23;--zsl-deep:#8FD6BE;--alert:#E08A5A;--alert-tint:#2E1B10;
--calm:#A2A7DA;--calm-tint:#1A1D33}}
:root[data-theme="dark"]{--paper:#0F1512;--card:#18201D;--ink:#E7ECE9;--mut:#A3AEA9;
--faint:#7C8783;--line:#2C3733;--rule:#232D29;--zsl:#5FBFA1;--zsl-tint:#0E2C23;
--zsl-deep:#8FD6BE;--alert:#E08A5A;--alert-tint:#2E1B10;--calm:#A2A7DA;--calm-tint:#1A1D33}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16.5px/1.6 var(--sans)}
.wrap{max-width:860px;margin:0 auto;padding:36px 20px 90px;display:flex;
flex-direction:column;gap:34px}
.masthead{border-bottom:3px solid var(--zsl);padding-bottom:16px}
h1{font-family:var(--serif);font-size:33px;line-height:1.12;margin:0 0 8px;
color:var(--zsl-deep);text-wrap:balance}
.lede{margin:0;color:var(--mut);max-width:64ch}
h2{font-family:var(--serif);font-size:24px;margin:0 0 4px;text-wrap:balance}
h3{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--faint);
font-weight:700;margin:22px 0 7px}
p{max-width:66ch}
.sec{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:26px 28px}
.order{margin-bottom:26px}
.order:last-child{margin-bottom:0}
.order-h{font-family:var(--serif);font-size:20px;color:var(--zsl-deep);margin:0 0 3px}
.order-n{margin:0 0 12px;color:var(--mut);font-size:14.5px;max-width:64ch}
.fams{display:flex;flex-wrap:wrap;gap:8px}
.fam{font-size:13px;padding:5px 11px;border-radius:3px;background:var(--zsl-tint);
color:var(--zsl-deep);border:1px solid transparent}
.fam b{font-weight:700}
.fam span{color:var(--mut);font-weight:400}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14.5px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
th{background:var(--zsl-tint);color:var(--zsl-deep);font-size:11.5px;font-weight:700;
text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--zsl)}
tr:last-child td{border-bottom:none}
td.n{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}
.bar{display:inline-block;height:9px;border-radius:2px;background:var(--zsl);
vertical-align:middle;margin-right:7px;min-width:2px}
.prof{border-top:2px solid var(--zsl);padding-top:18px;margin-top:26px}
.prof:first-of-type{margin-top:0}
.prof h2{color:var(--ink)}
.prof .gen{color:var(--mut);font-size:14px;font-style:italic;margin:0 0 14px}
.k{font-weight:700;color:var(--zsl-deep)}
.trap{background:var(--alert-tint);border-left:3px solid var(--alert);
border-radius:0 4px 4px 0;padding:12px 16px;margin-top:12px;font-size:15px}
.trap p{margin:0;max-width:64ch}
.trap .k{color:var(--alert)}
.foot{color:var(--faint);font-size:13.5px;max-width:66ch}
"""


def main():
    d = json.load(io.open(DATA, encoding="utf-8"))
    fam = defaultdict(list)
    for s in d["species"]:
        fam[s["group"]].append(s)

    o = ['<title>Small Mammals of Central Asia</title>',
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2'
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
