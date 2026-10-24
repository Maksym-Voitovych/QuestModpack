#!/usr/bin/env python3
"""Validate native action proofs against frozen advancement JSON and exact sources.

This checks a reviewed contract, not Java dispatch in a running modpack. An OR
inventory fallback cannot stand in for a mandatory action. Code-granted
impossible criteria need separate, hash-pinned grant-site evidence.
"""
import hashlib
import json
from pathlib import Path
import re

CONTRACT = 'content/audit/v5-native-advancement-contracts.json'
IDENTIFIER = re.compile(r'^[a-z0-9_.-]+:[a-z0-9_./-]+$')
PASSIVE = {'minecraft:inventory_changed', 'minecraft:recipe_unlocked',
           'minecraft:tick', 'minecraft:location', 'minecraft:impossible'}


def require(condition, *context):
    if not condition:
        raise AssertionError(context)


def frozen_file(root, path, digest):
    relative = Path(path)
    require(not relative.is_absolute() and '..' not in relative.parts,
            'Nonportable native advancement evidence', path)
    target = (root / relative).resolve()
    require(target.is_relative_to(root.resolve()) and target.is_file(),
            'Missing native advancement evidence', path)
    content = target.read_bytes()
    require(re.fullmatch(r'[0-9a-f]{64}', digest or '') and
            hashlib.sha256(content).hexdigest() == digest,
            'Stale native advancement evidence', path)
    return content


def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    return expected == actual


def validate(root, records, rules, versions):
    root = Path(root)
    path = root / CONTRACT
    document = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {'schema': 1, 'advancements': []}
    require(document.get('schema') == 1 and isinstance(document.get('advancements'), list),
            'Unsupported native advancement contract')
    contracts = {}
    evidence_paths = set()
    direct_count = 0
    for contract in document['advancements']:
        identifier = contract.get('id', '')
        require(IDENTIFIER.fullmatch(identifier) and identifier not in contracts,
                'Duplicate or invalid native action advancement', identifier)
        mod_id = contract.get('mod_id')
        require(mod_id in versions and contract.get('installed_version') == versions[mod_id],
                'Native advancement installed version mismatch', identifier)
        epoch = contract.get('epoch')
        require(type(epoch) is int and 1 <= epoch <= 48, 'Invalid native advancement epoch', identifier)
        require(len(contract.get('proof_scope_uk', '').strip()) >= 30,
                'Native advancement lacks a precise proof scope', identifier)
        content = frozen_file(root, contract['json_path'], contract['json_sha256'])
        advancement = json.loads(content)
        evidence_paths.add(contract['json_path'])
        criteria = advancement.get('criteria', {})
        require(criteria and all(isinstance(c, dict) for c in criteria.values()),
                'Native advancement has no valid criteria', identifier)
        allowed = contract.get('required_action_triggers', [])
        require(allowed and len(set(allowed)) == len(allowed) and
                all(IDENTIFIER.fullmatch(t) for t in allowed),
                'Native advancement lacks exact action triggers', identifier)
        sources = contract.get('sources', [])
        require(len(sources) >= 2, 'Native action requires codec/dispatch and version evidence', identifier)
        source_files = {}
        for source in sources:
            source_path = source.get('path', source.get('local_path', ''))
            source_files[source_path] = frozen_file(root, source_path, source.get('sha256'))
            evidence_paths.add(source_path)
        direct = contract.get('dispatch_mode') == 'direct_native_grant'
        if direct:
            require(allowed == ['minecraft:impossible'], 'Direct native grant must use its impossible criterion', identifier)
            grant = contract.get('direct_grant', {})
            require(grant.get('path') in source_files, 'Native direct grant lacks reviewed grant site', identifier)
            source = frozen_file(root, grant['path'], grant.get('sha256')).decode('utf-8')
            tokens = grant.get('required_source_tokens', [])
            require(len(tokens) >= 3 and all(isinstance(t, str) and t and t in source for t in tokens),
                    'Native direct grant source contract changed', identifier)
            require(any(identifier.split(':', 1)[1] in token for token in tokens),
                    'Native direct grant does not identify its advancement', identifier)
            direct_count += 1
        else:
            owners = contract.get('trigger_mod_versions', {})
            for owner, version in owners.items():
                require(versions.get(owner) == version, 'Native trigger owner version mismatch', identifier, owner)
            require(not set(allowed) & PASSIVE and
                    all(t.split(':', 1)[0] == mod_id or t.split(':', 1)[0] in owners for t in allowed),
                    'Passive or foreign trigger cannot prove a native mod action', identifier)
        expected = contract.get('expected_conditions', {})
        require(set(expected) <= set(allowed), 'Conditions refer to an unaudited trigger', identifier)
        action_names = set()
        for name, criterion in criteria.items():
            trigger = criterion.get('trigger')
            if trigger in allowed and subset(expected.get(trigger, {}), criterion.get('conditions', {})):
                action_names.add(name)
        require(action_names, 'Native advancement no longer proves its declared action', identifier)
        requirements = advancement.get('requirements', [[name] for name in criteria])
        require(requirements and all(isinstance(group, list) and group and
                                    all(name in criteria for name in group) for group in requirements),
                'Invalid native advancement requirements', identifier)
        # Each inner list is OR; outer groups are AND. At least one entire
        # required OR group must contain only the reviewed action criteria.
        require(any(set(group) <= action_names for group in requirements),
                'Inventory or another criterion can bypass the native action', identifier)
        if identifier.startswith('aia2:'):
            runtime = root / 'kubejs/data/aia2/advancement' / (identifier.split(':', 1)[1] + '.json')
            require(runtime.is_file() and runtime.read_bytes() == content,
                    'Custom native action advancement differs from reviewed JSON', identifier)
        contracts[identifier] = contract
    process_ids = {r['advancement'] for r in json.loads((root/'kubejs/config/aia2_mechanics.json').read_text())['rules']} if (root/'kubejs/config/aia2_mechanics.json').is_file() else set()
    used = set()
    action_quests = set()
    for quest in records:
        for task in quest.get('tasks', []):
            if task.get('type') != 'advancement':
                continue
            identifier = task['advancement']
            stage = re.fullmatch(r'aia2:(?:stages|keys)/e(\d{2})', identifier)
            if stage:
                require(1 <= int(stage[1]) <= min(48, quest['epoch']),
                        'Quest references an invalid/future epoch proof', quest['id'], identifier)
                continue
            if identifier in process_ids:
                continue
            require(identifier in contracts, 'Quest references an unreviewed native advancement', quest['id'], identifier)
            require(contracts[identifier]['epoch'] <= quest['epoch'],
                    'Quest requires a future native action', quest['id'], identifier)
            used.add(identifier)
            action_quests.add(quest['id'])
    require(set(contracts) == used, 'Unused native action contracts', sorted(set(contracts) - used))
    return {'status': 'passed', 'approved_advancements': sorted(used),
            'native_action_quests': len(action_quests), 'direct_native_grants': direct_count,
            'hash_verified_source_files': len(evidence_paths), 'full_pack_dispatch': 'not_run'}
