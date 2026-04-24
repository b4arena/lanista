"""Registry of every source lanista knows about.

New sources: add a module in this package that exposes a module-level
``SOURCE: Source`` and list it here. The index builder iterates this tuple
in order; observations in the merged index appear in the same order.
"""

from __future__ import annotations

from lanista.source_base import Source
from lanista.sources import (
    aider,
    artificial_analysis,
    factory_weather,
    gkisokay,
    litellm,
    lmarena,
    openrouter,
    pimono,
)

SOURCES: tuple[Source, ...] = (
    openrouter.SOURCE,
    litellm.SOURCE,
    pimono.SOURCE,
    gkisokay.SOURCE,
    factory_weather.SOURCE,
    aider.SOURCE,
    artificial_analysis.SOURCE,
    lmarena.SOURCE,
)
