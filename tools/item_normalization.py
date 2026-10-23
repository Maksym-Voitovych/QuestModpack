"""Resolve known unproducible duplicate material IDs without touching persistent IDs."""
import json
from pathlib import Path
RULES = json.loads((Path(__file__).resolve().parents[1]/'content/audit/unification-corrections.json').read_text())['replacements']

def normalize(value):
    if isinstance(value, str): return RULES.get(value, value)
    if isinstance(value, list): return [normalize(v) for v in value]
    if isinstance(value, dict): return {k: normalize(v) for k,v in value.items()}
    return value
