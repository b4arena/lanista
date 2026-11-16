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
- Every field is optional and is `{value, source_note, as_of}`.
  `source_note` and `as_of` must be non-empty strings when present; `as_of`
  is an ISO date (`YYYY-MM-DD`). A non-null value needs both.
- **Absent vs null.** A field that is absent inherits from the public model
  card where that is allowed (see precedence). A field set to
  `{"value": null}` masks the card: it stays unknown with `origin: local`.
  Use it when the route is known to differ but the real value is not known.

| Field | `value` type | Allowed content |
|---|---|---|
| `canonical` | string | a canonical id (ideally one with a model card) |
| `cost` | string | `subscription`, `budget`, `unknown` |
| `pricing_per_million` | object | keys `input`, `output` (finite number >= 0 or null), optional `currency` (non-empty string) |
| `limits` | object | keys `rpm`, `tpm` (finite number >= 0 or null) |
| `context_window`, `max_output` | integer | > 0 |
| `modalities` | object | keys `input`, `output`; each a non-empty list of `text`, `image`, `audio`, `video`, `file` |
| `capabilities` | object | keys `reasoning`, `function_calling`, `vision`, `json`, `structured_output`, `streaming`, `prompt_caching`; each `true`, `false` or `null` |

- `cost` is a class, the same values as vega. A subscription is not a token
  budget: give it no `pricing_per_million`.
- Typos (`inpt`, `rmp`, `funcion_calling`), unknown fields, bad values and bad
  provenance are skipped with a diagnostic; the rest of the route still loads.
  A file that is not valid JSON, has the wrong `schema` or no `routes` object
  disables the whole overlay with one diagnostic.

### Ownership and precedence (shared contract with vega)

- vega `~/.config/vega/lanista/seats.local.json` owns provider + tier → route id.
- `routes.local.json` owns route id → canonical id and the route facts above.
  vega's `canonical` and `cost` in `seats.local.json` are deprecated fallbacks.
- Join key: the route id string, compared exactly. No alias or normalize.
- Precedence per field: `routes.local.json` (including an explicit null) →
  public model card → unknown.
  `cost`, `pricing_per_million`, `limits` and `capabilities` have no catalog
  fallback: a vendor's public price is a fact about the vendor's own API,
  never the price of some other route, and a card's capabilities say what the
  model can do, not what a gateway exposes. Card capabilities appear only as
  model facts (`lanista show`), never as route capabilities.
  `context_window`, `max_output` and `modalities` fall back to the model card
  of the route's canonical id when the field is absent.
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
