# -*- coding: utf-8 -*-
"""Fetch openly licensed animal photographs for the field cards.

Source is iNaturalist, filtered to CC0 and CC-BY only. iNaturalist's DEFAULT
photo licence is CC BY-NC, so the filter is mandatory, not advisory - without it
the stream is overwhelmingly non-commercial and unusable here.

Do not substitute GBIF's `license` parameter for this: it filters the occurrence
record's licence, not the photo's, and returns all-rights-reserved images.

Writes files into images/ and records file, credit, licence and source URL back
into species_data.json. Re-run render_cards.py afterwards.

Usage:  python fetch_photos.py [--force] [--pin "Binomial=obs_id"]
"""
import html
import io, json, os, sys, time, urllib.parse, urllib.request

# Photographer names carry diacritics the Windows console codepage cannot encode.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA = "species_data.json"
IMG_DIR = "images"
API = "https://api.inaturalist.org/v1/observations"
UA = "ZSL-WP4-fieldcards/1.0 (+small mammal protocol, Central Asia)"

# Only these. Anything else cannot go in a redistributable manual.
LICENCES = "cc0,cc-by"
LICENCE_LABEL = {"cc0": "CC0 1.0", "cc-by": "CC BY 4.0"}

# Preferred provenance order: the project countries first, then anywhere.
PLACE_PREF = ["KZ", "KG", "TJ", "TM", "UZ"]

# iNaturalist controlled term 22, "Evidence of Presence". Research grade means the
# community agrees on the identification, NOT that the photo shows an animal - a
# clear photo of footprints is research grade. Without this filter the picker will
# happily ship tracks, scat or bones.
EVIDENCE_TERM = 22
EV_ORGANISM = 24
EV_REJECT = {25: "scat", 26: "track", 27: "bone", 28: "molt", 31: "hair",
             23: "feather", 32: "leafmine", 29: "gall", 30: "egg", 35: "construction"}


def evidence(obs):
    """Return 'organism', a rejection reason, or None when unannotated."""
    for a in obs.get("annotations", []):
        if a.get("controlled_attribute_id") == EVIDENCE_TERM:
            v = a.get("controlled_value_id")
            if v == EV_ORGANISM:
                return "organism"
            if v in EV_REJECT:
                return EV_REJECT[v]
    return None


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def search(name, country=None):
    q = {"taxon_name": name, "photo_license": LICENCES, "quality_grade": "research",
         "order_by": "votes", "per_page": "20", "locale": "en"}
    if country:
        q["place_id"] = ""
        q["country_code"] = country
    try:
        return get_json(API + "?" + urllib.parse.urlencode(q)).get("results", [])
    except Exception as exc:
        print("    search failed (%s): %s" % (country or "worldwide", exc))
        return []


def pick(obs_list):
    """Best observation carrying a genuinely CC0/CC-BY photo.

    Annotated as a whole organism wins. Unannotated is a fallback. Anything
    annotated as track, scat, bone, molt or hair is rejected outright - those
    are perfectly good records and useless as identification photographs.
    """
    best = (None, None, None)
    for obs in obs_list:
        ev = evidence(obs)
        if ev and ev != "organism":
            continue
        for photo in obs.get("photos", []):
            code = (photo.get("license_code") or "").lower()
            if code not in ("cc0", "cc-by"):
                continue
            if ev == "organism":
                return obs, photo, code
            if best[0] is None:
                best = (obs, photo, code)
            break
    return best


def download(photo, dest):
    # iNat serves square/small/medium/large/original from one stem.
    url = photo["url"]
    for size in ("large", "medium"):
        candidate = url.replace("/square.", "/%s." % size)
        try:
            req = urllib.request.Request(candidate, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if len(data) > 5000:
                io.open(dest, "wb").write(data)
                return len(data)
        except Exception:
            continue
    return 0


def parse_pins(argv):
    """--pin "Binomial=obs_id" (repeatable). Forces a specific observation."""
    pins = {}
    for i, a in enumerate(argv):
        if a == "--pin" and i + 1 < len(argv) and "=" in argv[i + 1]:
            k, v = argv[i + 1].split("=", 1)
            pins[k.strip()] = v.strip()
    return pins


def fetch_one(obs_id):
    """Look up a single observation and return its first open-licensed photo."""
    try:
        obs = get_json("https://api.inaturalist.org/v1/observations/%s" % obs_id)["results"][0]
    except Exception as exc:
        print("    could not load observation %s: %s" % (obs_id, exc))
        return None, None, None
    for photo in obs.get("photos", []):
        code = (photo.get("license_code") or "").lower()
        if code in ("cc0", "cc-by"):
            return obs, photo, code
    print("    observation %s has no CC0/CC-BY photo" % obs_id)
    return None, None, None


def main():
    force = "--force" in sys.argv
    pins = parse_pins(sys.argv)
    d = json.load(io.open(DATA, encoding="utf-8"))
    if not os.path.isdir(IMG_DIR):
        os.makedirs(IMG_DIR)

    got, skipped, missing = 0, 0, []
    for sp in d["species"]:
        name = sp["binomial"]
        slug = name.lower().replace(" ", "_")
        dest = os.path.join(IMG_DIR, "%s_animal.jpg" % slug)
        have = sp.get("images", {}).get("animal", {}).get("file")

        pinned = pins.get(name) or pins.get(sp["common"])
        if have and os.path.exists(dest) and not force and not pinned:
            skipped += 1
            continue

        print("%-28s" % name, end=" ")
        obs = photo = code = None

        if pinned:
            obs, photo, code = fetch_one(pinned)
            if photo:
                print("[pinned %s]" % pinned, end=" ")
        # try the project countries first so pictures match what teams will see
        for cc in ([] if photo else PLACE_PREF):
            obs, photo, code = pick(search(name, cc))
            if photo:
                print("[%s]" % cc, end=" ")
                break
            time.sleep(0.6)
        if not photo:
            obs, photo, code = pick(search(name))
            if photo:
                print("[worldwide]", end=" ")

        if not photo:
            # try the synonym the treatment may be filed under
            alt = sp.get("also_known_as")
            if alt:
                obs, photo, code = pick(search(alt))
                if photo:
                    print("[as %s]" % alt, end=" ")

        if not photo:
            print("no CC0/CC-BY photo")
            missing.append(name)
            time.sleep(0.6)
            continue

        size = download(photo, dest)
        if not size:
            print("download failed")
            missing.append(name)
            time.sleep(0.6)
            continue

        user = obs.get("user") or {}
        # iNat returns display names HTML-escaped; unescape once here so the
        # renderer can escape exactly once.
        credit = html.unescape(user.get("name") or user.get("login") or "unknown")
        sp.setdefault("images", {})["animal"] = {
            "file": "%s/%s_animal.jpg" % (IMG_DIR, slug),
            "caption": "%s, %s" % (sp["common"], obs.get("place_guess") or "location not stated"),
            "credit": credit,
            "licence": LICENCE_LABEL.get(code, code),
            "source_url": "https://www.inaturalist.org/observations/%s" % obs.get("id"),
        }
        print("%s  %s  %.0f KB" % (LICENCE_LABEL.get(code, code), credit, size / 1024.0))
        got += 1
        time.sleep(0.8)

    io.open(DATA, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
    print("\nfetched %d, already had %d, no open photo for %d" % (got, skipped, len(missing)))
    if missing:
        print("missing: " + ", ".join(missing))
    print("now run: python render_cards.py")


if __name__ == "__main__":
    main()
