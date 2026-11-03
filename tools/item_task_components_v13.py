"""Reviewed CDG Mold predicates; unsupported component schemas fail closed.

FTB2101.1.36 silently defaults an unknown matching mode to NONE. Never emit
an unverified mode or silently discard a component requested by an author.
"""
import copy
import json

MOLD_ITEM = 'createdieselgenerators:mold'
MOLD_COMPONENT = 'createdieselgenerators:mold_type'
MOLD_PROFILES = frozenset('createdieselgenerators:'+name for name in ('lines', 'bowl', 'chain', 'bar'))


def predicate(record):
    for field in record:
        if field.strip().casefold().replace('_', '') in {'components', 'matchcomponents'}:
            assert field in {'components', 'match_components'}, 'Use exact lowercase components/match_components field names'
    present = 'components' in record or 'match_components' in record
    if not present:
        return None
    assert record.get('type') == 'item' and record.get('item') == MOLD_ITEM, 'Components require a reviewed Mold item task'
    components = record.get('components')
    assert isinstance(components, dict) and set(components) == {MOLD_COMPONENT}, 'Only the reviewed mold_type component is supported'
    profile = components[MOLD_COMPONENT]
    assert isinstance(profile, str) and profile in MOLD_PROFILES, 'Unknown or unqualified Mold profile ResourceLocation'
    assert record.get('match_components') == 'fuzzy', 'Mold tasks require literal fuzzy matching; unknown modes default to NONE in FTB'
    assert all(type(record.get(flag, False)) is bool and record.get(flag, False) is False
               for flag in ('consume', 'craft')), 'Mold profile tasks require Boolean false inventory flags'
    assert type(record.get('count', 1)) is int and record.get('count', 1) > 0, 'Mold task count must be a positive integer'
    return {'components': copy.deepcopy(components), 'match_components': 'fuzzy'}


def item_stack(record):
    stack = {'id': record['item'], 'count': 1}
    spec = predicate(record)
    if spec is not None:
        stack['components'] = spec['components']
    return stack


def signature_suffix(record):
    spec = predicate(record)
    return () if spec is None else (json.dumps(spec['components'], sort_keys=True, separators=(',', ':')), spec['match_components'])
