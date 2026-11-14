"""Read studio/publisher credit lists without splitting company suffixes.

New imports store JSON arrays. Older GamePulse databases store comma-joined text,
so the legacy fallback uses a small, documented suffix-repair rule.
"""
from __future__ import annotations
import json
import re

SUFFIXES = {'inc', 'incorporated', 'ltd', 'limited', 'llc', 'l l c', 'co', 'corp', 'corporation', 'gmbh', 's a', 'plc', 'pty', 'pvt'}


def _suffix(text: str) -> bool:
    cleaned = re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    return cleaned in SUFFIXES


def parse_credits(value) -> list[str]:
    """Best-effort credit names; preserves commas inside JSON credit names."""
    if value is None: return []
    if isinstance(value, (list,tuple)): return list(dict.fromkeys(str(v).strip() for v in value if str(v).strip()))
    text = str(value).strip()
    if not text or text.lower() in {'nan','none','null','[]'}: return []
    if text.startswith('['):
        try:
            from ast import literal_eval
            try: obj = json.loads(text)
            except (ValueError, TypeError): obj = literal_eval(text)
            if isinstance(obj,list):
                return list(dict.fromkeys(str(v).strip() for v in obj if str(v).strip()))
        except (ValueError, SyntaxError, TypeError): pass
    parts = [p.strip() for p in text.split(',') if p.strip()]
    combined=[]
    for part in parts:
        if _suffix(part):
            if combined: combined[-1] += ', ' + part
        else:
            combined.append(part)
    return list(dict.fromkeys(combined))


def display_credits(value) -> str:
    return ' · '.join(parse_credits(value)) or 'Unknown'
