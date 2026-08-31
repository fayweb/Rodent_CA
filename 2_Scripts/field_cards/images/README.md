# Pictures for the field cards

Every card has three picture slots. An empty slot prints the shot to take, so the
cards double as the photographic shot list until the pictures exist.

| Slot | What it holds |
|---|---|
| `animal` | Whole animal in the hand, dorsal view, with a scale bar |
| `detail` | The feature separating this species from its confusion pair |
| `sign` | Burrow entrance, runway, mound or hay pile, with something for scale |

## Adding a picture

1. Put the file in this directory. Name it `<binomial>_<slot>.jpg`, lower case,
   underscores for spaces, e.g. `apodemus_agrarius_animal.jpg`.
2. Add an `images` block to that species in `../species_data.json`:

```json
"images": {
  "animal": {
    "file": "images/apodemus_agrarius_animal.jpg",
    "caption": "Adult in the hand, dorsal stripe visible",
    "credit": "Fay Webster",
    "licence": "CC BY 4.0",
    "source_url": "https://www.inaturalist.org/observations/123456"
  }
}
```

3. Re-run `python render_cards.py`.

`credit` and `licence` are not optional. Every image in the manual carries its
photographer and licence in the caption, and an image without them cannot be
published.

## Where openly licensed pictures exist

**Whole animals — iNaturalist, licence-filtered.** The filter is mandatory:
iNaturalist's default photo licence is CC BY-NC and the unfiltered stream is
overwhelmingly NC. Use

```
https://api.inaturalist.org/v1/observations?taxon_name=Rhombomys%20opimus&photo_license=cc0,cc-by
```

Verified holdings include *Rhombomys opimus* 37 observations (several from
Kazakhstan), *Hemiechinus auritus* 90, *Ochotona rutila* 6 including a CC0 set
near Almaty, *Allactaga major* 4. *Sicista tianshanica* has none.

**Do not use GBIF's `license` parameter as a filter.** It filters the occurrence
record's licence, not the image's, and returns all-rights-reserved photos. Read
`media[].license` per image, or go to iNaturalist directly.

**Anatomical line drawings.** Ellerman, *The Families and Genera of Living
Rodents*, on archive.org, status NOT_IN_COPYRIGHT, roughly 50 figures of skulls
and dentition. Ognev Vol. 4 is CC BY-NC-SA, not public domain, so prefer
Ellerman where it has an equivalent figure.

**Excluded: Animal Diversity Web.** Its own conditions of use state image
licences vary and include all-rights-reserved.

## The two gaps

**Sexing.** No CC0 or CC BY image of adult small-mammal sexing exists — not
scrotal versus abdominal testes, not perforate versus imperforate vagina, not
comparative anogenital distance. The only CC BY figure found shows fetal mice.
This figure has to be drawn de novo or photographed in the field. Do not trace
an existing copyrighted figure: the technique is uncopyrightable, the drawing
is not.

**Field signs.** Almost nothing open exists. The best verified image is a great
gerbil colony near Baikonur on Wikimedia Commons (CC BY-SA 3.0 + GFDL). There
are no open images of runways, latrines or feeding signs for these species.
This is the gap the trip photography fills.

## Closing the loop

Trip photographs uploaded to iNaturalist under a deliberate CC-BY licence become
research-grade records, flow to GBIF, and are then citable in the manual by
download DOI. Agree geoprivacy on trap-site coordinates with partners first.

## Note on publishing

Relative paths work for the local HTML file. If the cards are ever published as
a hosted artifact, images must be uploaded as assets or embedded as data URIs;
relative paths will not resolve.
