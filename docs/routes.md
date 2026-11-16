# Model cards and private routes

lanista keeps two kinds of model information apart:

| Kind | File | Public? | Written by |
|---|---|---|---|
| Model knowledge: architecture, params, modalities, capabilities, benchmarks, variant identity | `lanista/data/model_cards.json` (packaged) | yes, in this repo | humans, via PR |
| Access/routing: cost class, per-token price, limits, context overrides for one route | `$XDG_CONFIG_HOME/lanista/routes.local.json` | **no**, host-local | humans, by hand |

`lanista fetch` and the seeders never create or write `routes.local.json`.
The overlay is applied when the index is read, so the index file on disk
stays public-only.

## Model cards (`model_cards.json`)

```json
{
  "schema": 1,
  "models": {
    "<canonical-id>": {
      "display_name": "GLM-5.3",
      "facts": {
        "total_params":  {"value": "753B", "source": "https://...", "as_of": "2026-11-16"},
        "active_params": {"value": null, "status": "unknown"}
      },
      "benchmarks": [{"name": "...", "score": 1.0, "setting": "...", "source": "https://...", "as_of": "..."}],
      "not_same_as": ["<sibling canonical ids>"]
    }
  },
  "variants": {"<runtime-id>": {"canonical": "<canonical-id>", "source": "https://...", "note": "..."}},
  "unproven": {"<runtime-id>": {"candidates": ["..."], "reason": "...", "source": "https://..."}}
}
```

Rules:

- Every fact has `source` (an official vendor page, Hugging Face card or
  paper) and `as_of` (the date the source was read). A fact the source does
  not show is `{"value": null, "status": "unknown"}`. Unknown is never 0.
- Benchmarks are listed only for the exact variant the card describes. Scores
  of a sibling (an older build, a quantized repo) are not copied over.
- A runtime id reaches a canonical id only through `variants`, compared after
  `lanista.aliases.normalize` (case, punctuation, first provider prefix).
  Every token must match, so `-1017`, `-816B-A42B` or `-NVFP4` stay distinct.
  Seat soft-suffix peeling never lands on an id listed here.
- `unproven` documents ids whose identity is not established (for example the
  bare `muse-spark-open`, which hosts may serve as BF16 or NVFP4). They are
  never merged; `lanista doctor` rejects an id that is both proven and unproven.

## Private route overlay (`routes.local.json`)

Path: `$XDG_CONFIG_HOME/lanista/routes.local.json` (default
`~/.config/lanista/routes.local.json`). Example with fake values:
[`routes.local.example.json`](routes.local.example.json).

```json
{
  "schema": 1,
  "routes": {
    "example-gw/glm-5.3": {
      "canonical":           {"value": "glm-5-3", "source_note": "...", "as_of": "2026-01-01"},
      "cost":                {"value": "budget",  "source_note": "...", "as_of": "2026-01-01"},
      "pricing_per_million": {"value": {"input": 0.11, "output": 0.22, "currency": "USD"}, "source_note": "...", "as_of": "..."},
      "limits":              {"value": {"rpm": 10, "tpm": 20000}, "source_note": "...", "as_of": "..."},
      "context_window":      {"value": 65536, "source_note": "...", "as_of": "..."},
      "max_output":          {"value": 8192,  "source_note": "...", "as_of": "..."},
      "modalities":          {"value": {"input": ["text"], "output": ["text"]}, "source_note": "...", "as_of": "..."}
    }
  }
}
```

- The route id is the exact runtime id the harness is started with, provider
  prefix included.
- Every field is optional and is `{value, source_note, as_of}`. A non-null
  value needs `source_note` and `as_of`. `value: null` means unknown.
- `cost` is a class, the same values as vega: `subscription | budget | unknown`.
  A subscription is not a token budget: give it no `pricing_per_million`.
- Unknown fields, bad values, missing notes and unknown top-level keys are
  skipped with a diagnostic. A file that is not valid JSON, has the wrong
  `schema` or no `routes` object disables the whole overlay with one diagnostic.

### Ownership and precedence (shared contract with vega)

- vega `~/.config/vega/lanista/seats.local.json` owns provider + tier → route id.
- `routes.local.json` owns route id → canonical id and the route facts above.
  vega's `canonical` and `cost` in `seats.local.json` are deprecated fallbacks.
- Join key: the route id string, compared exactly. No alias or normalize.
- Precedence per field: `routes.local.json` → public model card → unknown.
  `cost`, `pricing_per_million` and `limits` have no catalog fallback: a
  vendor's public price is a fact about the vendor's own API, never the price
  of some other route. `context_window`, `max_output` and `modalities` fall
  back to the model card of the route's canonical id.
- Each resolved field carries `origin`: `local`, `catalog` or `unknown`.
  Route records carry `visibility: "private-local"`.

### Read API

CLI:

```
lanista --json route <route-id>   # one route; exit 1 when not in the overlay
lanista --json routes             # all routes + overlay status/diagnostics
lanista doctor                    # "route overlay" check: absent / loaded N / warnings
```

`route --json` prints:

```json
{
  "overlay": {"path": "...", "present": true, "loaded": true, "route_count": 3, "diagnostics": []},
  "routes": {
    "example-gw/glm-5.3": {
      "route_id": "example-gw/glm-5.3",
      "visibility": "private-local",
      "canonical": "glm-5-3",
      "has_public_card": true,
      "fields": {
        "cost": {"value": "budget", "source_note": "...", "as_of": "...", "origin": "local"},
        "pricing_per_million": {"value": null, "status": "unknown", "origin": "unknown"},
        "modalities": {"value": {"input": ["text"], "output": ["text"]}, "source": "https://...", "as_of": "...", "origin": "catalog"}
      },
      "overlay_path": "..."
    }
  }
}
```

Python:

```python
from lanista import routes
ov = routes.load_overlay()                       # Overlay(path, present, loaded, routes, diagnostics)
routes.resolve_route("example-gw/glm-5.3", ov)   # dict as above, or None
routes.resolve_all(ov)                           # {route_id: dict}
```

`lanista show <model>` also lists the model card and any private routes whose
canonical id is that model.
