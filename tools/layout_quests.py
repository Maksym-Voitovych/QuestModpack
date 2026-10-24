#!/usr/bin/env python3
"""Deterministic coordinates for the existing AIA2 quest graph.

Only quest x/y values change. IDs, order, tasks, dependencies, rewards, chapter
containers and progress data are outside this tool's write contract. Generated
chapters use JSON, which is the strict subset of SNBT accepted by FTB Quests.

The layout uses weakly connected courses, longest-path layers, alternating
barycentric ordering, exact straight-line crossing comparisons, isotonic vertical
compaction and epoch shelves. The two legacy optional epoch leaves get their own
side strip. Technology, magic and research provide semantic ordering seeds, not
new dependency rules. The dependency graph always wins over a preferred lane.

Run without flags for a read-only audit. --apply writes coordinates and a report;
the main content compiler should call apply(root) only after building all chapters.
"""
import argparse
from collections import defaultdict
import copy
import hashlib
import heapq
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 1
ALGORITHM = 'stable-dag-barycentric-v2'
EPSILON = 1e-9
ZONE_ORDER = {'technology': 0, 'magic': 1, 'research': 2}
LONG_EDGE_COLUMNS = 12
CROSSING_DENSITY_WARNING = 1.0


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _uid(name):
    return hashlib.sha256(('aia2-runtime-v1:' + name).encode()).hexdigest()[:12].upper().rjust(16, '0')


def _strip_coordinates(chapter):
    result = copy.deepcopy(chapter)
    for quest in result.get('quests', []):
        quest.pop('x', None)
        quest.pop('y', None)
    return result


def _semantic_hash(chapter):
    value = json.dumps(_strip_coordinates(chapter), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(value.encode()).hexdigest()


def load_metadata(root=ROOT):
    """Return stable logical identity, stage and lane hints without editing data."""
    root = Path(root)
    metadata = {}
    for n in range(1, 49):
        for i in range(1, 7):
            zone = 'technology' if i <= 2 else 'magic' if i <= 4 else 'research'
            metadata[_uid(f'E{n:02d}_M{i}')] = dict(epoch=n, zone=zone, logical=f'1_milestone_{i}')
        for i, kind in enumerate(('tech_matrix', 'arcane_catalyst', 'convergence_core', 'epoch_seal')):
            metadata[_uid(f'E{n:02d}_COMPONENT_{kind}')] = dict(
                epoch=n, zone=('technology' if kind == 'tech_matrix' else
                               'magic' if kind == 'arcane_catalyst' else 'research'),
                logical=f'2_component_{i}')
        for suffix in ('KEY', 'O1', 'O2', 'EXPANSION_TRIAL', 'DUAL_TECH', 'DUAL_ARCANE'):
            zone = 'technology' if suffix == 'DUAL_TECH' else 'magic' if suffix == 'DUAL_ARCANE' else 'research'
            metadata[_uid(f'E{n:02d}_{suffix}')] = dict(
                epoch=n, zone=zone, logical='3_' + suffix, side_optional=suffix in {'O1', 'O2'})
    for path in sorted((root/'content/quests').glob('*.json')):
        data = _read(path)
        records = data if isinstance(data, list) else data.get('quests', [])
        for quest in records:
            category = quest.get('category', '')
            zone = ('technology' if category in {'technology', 'automation'} else
                    'magic' if category == 'magic' else 'research')
            metadata[_uid(quest['id'])] = dict(
                epoch=int(quest['epoch']), zone=zone, logical=quest['id'], mod=quest.get('mod', ''))
    runtime_path = root/'kubejs/config/aia2_runtime.json'
    if runtime_path.exists():
        for epoch in _read(runtime_path).get('epochs', []):
            qid = epoch['finalQuestId']
            hint = metadata.setdefault(qid, dict(epoch=epoch['number'], zone='research', logical='3_KEY'))
            # The server checks these gates without rewriting old saved quest
            # dependencies. Put the visual transition after its actual gates.
            hint['layout_after'] = sorted(set(epoch.get('branchKeyQuestIds', {}).values()) |
                                          set(epoch.get('requiredQuestIds', [])))
    return metadata


def _hint(quest, metadata):
    hint = dict(metadata.get(quest['id'], {}))
    if 'epoch' not in hint:
        epochs = []
        for task in quest.get('tasks', []):
            advancement = task.get('advancement', '')
            if isinstance(advancement, str) and advancement.startswith('aia2:stages/e'):
                suffix = advancement.rsplit('/e', 1)[1]
                if suffix.isdigit():
                    epochs.append(int(suffix))
        hint['epoch'] = min(epochs, default=99)
    hint.setdefault('logical', quest['id'])
    hint.setdefault('zone', 'research')
    return hint


def _topology(quests):
    """Sorted Kahn traversal; external dependencies do not share this canvas."""
    if len(quests) != len(set(quests)):
        raise ValueError('Duplicate quest ID')
    predecessors = {qid: sorted({dep for dep in quest.get('dependencies', []) if dep in quests})
                    for qid, quest in quests.items()}
    successors = {qid: [] for qid in quests}
    for qid, deps in predecessors.items():
        for dep in deps:
            successors[dep].append(qid)
    indegree = {qid: len(deps) for qid, deps in predecessors.items()}
    ready = [qid for qid, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    order, ranks = [], {}
    while ready:
        qid = heapq.heappop(ready)
        order.append(qid)
        ranks[qid] = 1 + max((ranks[dep] for dep in predecessors[qid]), default=-1)
        for child in sorted(successors[qid]):
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    if len(order) != len(quests):
        raise ValueError('Quest dependency cycle: ' + ', '.join(sorted(qid for qid, count in indegree.items() if count)))
    return predecessors, successors, ranks, order


def _layout_topology(quests, metadata):
    graph = {qid: dict(quest, dependencies=sorted(set(quest.get('dependencies', [])) |
                                               set(metadata.get(qid, {}).get('layout_after', []))))
             for qid, quest in quests.items()}
    return _topology(graph)


def _orient(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _crosses(a, b, c, d):
    # Shared endpoints and collinear segments are deliberately not "proper"
    # crossings; this definition is included in the generated audit report.
    return (_orient(a, b, c)*_orient(a, b, d) < -EPSILON and
            _orient(c, d, a)*_orient(c, d, b) < -EPSILON)


def _size(quest, chapter):
    size = float(quest.get('size') or chapter.get('default_quest_size') or 1)
    if not math.isfinite(size) or size <= 0:
        raise ValueError('Invalid quest size: ' + quest['id'])
    return size


def chapter_metrics(chapter):
    """Measure all locally drawn edges, even if some are currently hidden.

    Crossings use straight center-to-center segments and exclude shared endpoints
    and collinear segments. Node overlap uses FTB's default size of one quest unit.
    Cross-chapter dependencies are counted separately because FTB's QuestButton
    only draws dependency buttons belonging to the selected chapter canvas.
    """
    quests = {quest['id']: quest for quest in chapter.get('quests', [])}
    if len(quests) != len(chapter.get('quests', [])):
        raise ValueError('Duplicate quest IDs in chapter ' + str(chapter.get('filename', chapter.get('id'))))
    positions = {}
    for qid, quest in quests.items():
        pos = (float(quest.get('x', 0)), float(quest.get('y', 0)))
        if not all(math.isfinite(value) for value in pos):
            raise ValueError('Non-finite coordinates: ' + qid)
        positions[qid] = pos
    edges = sorted((dep, qid) for qid, quest in quests.items()
                   for dep in quest.get('dependencies', []) if dep in quests)
    # Twelve normal layout columns are a review threshold, not a claim that a
    # real transitive dependency can safely be removed. Larger quest icons use
    # the same twelve-column policy with their actual spacing.
    step = max(2.0, max((_size(q, chapter) for q in quests.values()), default=1) + 1)
    long_edge_limit = LONG_EDGE_COLUMNS * step
    result = dict(quests=len(quests), local_edges=len(edges), external_edges=sum(
        dep not in quests for quest in quests.values() for dep in quest.get('dependencies', [])),
        overlaps=0, backwards_edges=0, vertical_edges=0, crossings=0, edge_length=0.0,
        long_edges=0, max_edge_length=0.0, long_edge_limit=long_edge_limit)
    for qid, quest in quests.items():
        for other_id, other in quests.items():
            if other_id >= qid:
                continue
            minimum = (_size(quest, chapter) + _size(other, chapter))/2
            if (abs(positions[qid][0]-positions[other_id][0]) < minimum-EPSILON and
                    abs(positions[qid][1]-positions[other_id][1]) < minimum-EPSILON):
                result['overlaps'] += 1
    for i, (start, end) in enumerate(edges):
        result['backwards_edges'] += positions[start][0] > positions[end][0] + EPSILON
        result['vertical_edges'] += abs(positions[start][0]-positions[end][0]) <= EPSILON
        length = math.dist(positions[start], positions[end])
        result['edge_length'] += length
        result['max_edge_length'] = max(result['max_edge_length'], length)
        result['long_edges'] += length > long_edge_limit + EPSILON
        for a, b in edges[:i]:
            if len({start, end, a, b}) == 4:
                result['crossings'] += _crosses(positions[start], positions[end], positions[a], positions[b])
    result['edge_length'] = round(result['edge_length'], 6)
    result['max_edge_length'] = round(result['max_edge_length'], 6)
    result['crossing_density'] = round(result['crossings']/max(1, len(edges)), 6)
    result['audit_warnings'] = []
    if result['long_edges']:
        result['audit_warnings'].append('long_dependency_lines')
    if result['crossing_density'] > CROSSING_DENSITY_WARNING:
        result['audit_warnings'].append('high_crossing_density')
    if positions:
        xs, ys = zip(*positions.values())
        result['width'] = round(max(xs)-min(xs)+max(_size(q, chapter) for q in quests.values()), 3)
        result['height'] = round(max(ys)-min(ys)+max(_size(q, chapter) for q in quests.values()), 3)
    else:
        result.update(width=0.0, height=0.0)
    return result


def _isotonic(targets, gap):
    """Least-squares ordered coordinates with a fixed minimum node spacing."""
    blocks = []
    for index, target in enumerate(targets):
        blocks.append([target-index*gap, 1])
        while len(blocks) > 1 and blocks[-2][0]/blocks[-2][1] > blocks[-1][0]/blocks[-1][1]:
            block = blocks.pop()
            blocks[-1][0] += block[0]
            blocks[-1][1] += block[1]
    values = []
    for total, count in blocks:
        for _ in range(count):
            values.append(total/count + len(values)*gap)
    return values


def _seed_key(qid, quests, metadata, seed):
    hint = _hint(quests[qid], metadata)
    priority = ZONE_ORDER.get(hint['zone'], 2)
    if seed == 'logical':
        priority = 0
    elif seed == 'central_components' and hint['logical'].startswith('2_component_'):
        priority = 2
    return priority, hint['logical'], qid


def _component_layout_from_seed(quests, metadata, step, seed):
    predecessors, successors, ranks, _ = _layout_topology(quests, metadata)
    layers = defaultdict(list)
    stable = lambda qid: _seed_key(qid, quests, metadata, seed)
    for qid in sorted(quests, key=stable):
        layers[ranks[qid]].append(qid)
    # Virtual transition constraints choose columns but are not drawn by FTB.
    edges = sorted((dep, qid) for qid, quest in quests.items()
                   for dep in quest.get('dependencies', []) if dep in quests)

    def coordinates(compact=True):
        xy = {qid: [depth*step, (index-(len(ids)-1)/2)*step]
              for depth, ids in layers.items() for index, qid in enumerate(ids)}
        if compact:
            for sweep in range(8):
                neighbours = predecessors if sweep % 2 == 0 else successors
                for depth in sorted(layers, reverse=sweep % 2 == 1):
                    ids = layers[depth]
                    target = [sum(xy[dep][1] for dep in neighbours[qid])/len(neighbours[qid])
                              if neighbours[qid] else xy[qid][1] for qid in ids]
                    for qid, y in zip(ids, _isotonic(target, step)):
                        xy[qid][1] = y
        minimum = min((p[1] for p in xy.values()), default=0)
        return {qid: (p[0], round(p[1]-minimum, 3)) for qid, p in xy.items()}

    def score(xy):
        crossings, length = 0, 0.0
        for i, (a, b) in enumerate(edges):
            length += math.dist(xy[a], xy[b])
            for c, d in edges[:i]:
                if len({a, b, c, d}) == 4:
                    crossings += _crosses(xy[a], xy[b], xy[c], xy[d])
        return crossings, length, max((p[1] for p in xy.values()), default=0)

    best = coordinates()
    best_score = score(best)
    for sweep in range(14):
        current = coordinates()
        neighbours = predecessors if sweep % 2 == 0 else successors
        for depth in sorted(layers, reverse=sweep % 2 == 1):
            layers[depth].sort(key=lambda qid: (
                sum(current[dep][1] for dep in neighbours[qid])/len(neighbours[qid])
                if neighbours[qid] else current[qid][1], stable(qid)))
        for compact in (False, True):
            candidate = coordinates(compact)
            candidate_score = score(candidate)
            if candidate_score < best_score:
                best, best_score = candidate, candidate_score
        # Exact comparisons avoid assuming that a barycentric sweep necessarily
        # improves the straight lines FTB actually draws for long dependencies.
        for depth in sorted(layers):
            for index in range(len(layers[depth])-1):
                old = layers[depth]
                changed = old[:]
                changed[index], changed[index+1] = changed[index+1], changed[index]
                layers[depth] = changed
                candidate = coordinates()
                candidate_score = score(candidate)
                if candidate_score < best_score:
                    best, best_score = candidate, candidate_score
                else:
                    layers[depth] = old
    return best, best_score


def _component_layout(quests, metadata, step):
    # A semantic seed is useful but can create more crossings around a dense
    # transition. Try the stable course order and a central hybrid-component
    # seed too, then keep the best measured real-edge result. Equal scores
    # prefer the semantic seed. Virtual transition edges remain undrawn.
    candidates, orders = [], set()
    for seed in ('semantic', 'logical', 'central_components'):
        order = tuple(sorted(quests, key=lambda qid: _seed_key(qid, quests, metadata, seed)))
        if order not in orders:
            orders.add(order)
            candidates.append(_component_layout_from_seed(quests, metadata, step, seed))
    return min(candidates, key=lambda candidate: candidate[1])[0]


def layout_chapter(chapter, metadata=None):
    """Return a copy with deterministic coordinates and no semantic changes."""
    metadata = {} if metadata is None else metadata
    result = copy.deepcopy(chapter)
    quests = {quest['id']: quest for quest in result.get('quests', [])}
    if len(quests) != len(result.get('quests', [])):
        raise ValueError('Duplicate quest IDs in chapter')
    if not quests:
        return result
    predecessors, successors, _, _ = _layout_topology(quests, metadata)
    step = max(2.0, max(_size(quest, result) for quest in quests.values()) + 1)
    # A side quest that later becomes a prerequisite must stay in the main graph.
    side_ids = {qid for qid, quest in quests.items()
                if _hint(quest, metadata).get('side_optional') and not successors[qid]}
    body = {qid: quest for qid, quest in quests.items() if qid not in side_ids}
    unseen = set(body)
    components = []
    while unseen:
        pending, group = [min(unseen)], set()
        while pending:
            qid = pending.pop()
            if qid in group:
                continue
            group.add(qid)
            pending.extend((set(predecessors[qid]) | set(successors[qid])) & set(body) - group)
        unseen -= group
        components.append(group)
    key = lambda qid: (_hint(quests[qid], metadata)['epoch'],
                       ZONE_ORDER.get(_hint(quests[qid], metadata)['zone'], 2),
                       _hint(quests[qid], metadata)['logical'], qid)
    components.sort(key=lambda group: min(key(qid) for qid in group))
    x_offset = y_offset = row_height = 0.0
    previous_epoch = None
    body_offset = step + 1 if side_ids else 0.0
    for group in components:
        xy = _component_layout({qid: quests[qid] for qid in group}, metadata, step)
        width = max(p[0] for p in xy.values()) + step
        height = max(p[1] for p in xy.values()) + step
        epoch = min(_hint(quests[qid], metadata)['epoch'] for qid in group)
        if x_offset and (x_offset + width > step*10 or epoch != previous_epoch):
            x_offset = 0.0
            y_offset += row_height + 1
            row_height = 0.0
        for qid, (x, y) in xy.items():
            quests[qid].update(x=round(x_offset+x, 3), y=round(body_offset+y_offset+y, 3))
        x_offset += width + 1
        row_height = max(row_height, height)
        previous_epoch = epoch
    occupied_side_x = []
    for qid in sorted(side_ids, key=key):
        x = max((quests[dep]['x'] for dep in predecessors[qid]), default=-step) + step
        while any(abs(x-used) < step-EPSILON for used in occupied_side_x):
            x += step
        quests[qid].update(x=round(x, 3), y=0.0)
        occupied_side_x.append(x)
    if _strip_coordinates(result) != _strip_coordinates(chapter):
        raise AssertionError('Layout changed non-coordinate quest data')
    checked = chapter_metrics(result)
    if checked['overlaps'] or checked['backwards_edges'] or checked['vertical_edges']:
        raise AssertionError('Invalid generated layout: ' + json.dumps(checked))
    return result


def _totals(chapters):
    chapters = list(chapters)
    fields = ('quests', 'local_edges', 'external_edges', 'overlaps', 'backwards_edges',
              'vertical_edges', 'crossings', 'edge_length', 'long_edges')
    totals = {field: round(sum(chapter[field] for chapter in chapters), 6) for field in fields}
    totals['max_edge_length'] = max((chapter['max_edge_length'] for chapter in chapters), default=0)
    totals['warning_chapters'] = sum(bool(chapter['audit_warnings']) for chapter in chapters)
    totals['high_crossing_density_chapters'] = sum(
        'high_crossing_density' in chapter['audit_warnings'] for chapter in chapters)
    return totals


def audit(root=ROOT):
    """Read-only metrics of the current canonical chapter coordinates."""
    root = Path(root)
    chapters = {path.name: chapter_metrics(_read(path))
                for path in sorted((root/'config/ftbquests/quests/chapters').glob('*.snbt'))}
    return dict(schema=SCHEMA, algorithm=ALGORITHM, chapter_count=len(chapters),
                totals=_totals(chapters.values()), chapters=chapters)


def _plan(root):
    root = Path(root)
    metadata = load_metadata(root)
    entries = {}
    pending = []
    for path in sorted((root/'config/ftbquests/quests/chapters').glob('*.snbt')):
        before = _read(path)
        after = layout_chapter(before, metadata)
        before_hash, after_hash = _semantic_hash(before), _semantic_hash(after)
        if before_hash != after_hash:
            raise AssertionError('Semantic fingerprint changed: ' + path.name)
        zones = defaultdict(list)
        for quest in after.get('quests', []):
            hint = _hint(quest, metadata)
            zones['optional_side' if hint.get('side_optional') else hint['zone']].append(quest['id'])
        entries[path.name] = dict(chapter_id=before['id'], semantic_sha256=before_hash,
                                  before=chapter_metrics(before), after=chapter_metrics(after),
                                  layout_only_edges=sorted([dep, quest['id']]
                                      for quest in after.get('quests', [])
                                      for dep in metadata.get(quest['id'], {}).get('layout_after', [])
                                      if dep in {q['id'] for q in after.get('quests', [])}
                                      and dep not in quest.get('dependencies', [])),
                                  zones={zone: sorted(ids) for zone, ids in sorted(zones.items())})
        pending.append((path, after))
    before_totals = _totals(entry['before'] for entry in entries.values())
    after_totals = _totals(entry['after'] for entry in entries.values())
    report = dict(schema=SCHEMA, algorithm=ALGORITHM, chapter_count=len(entries),
                  before=before_totals, after=after_totals,
                  changed_fields=['quests[].x', 'quests[].y'],
                  all_non_coordinate_data_preserved=True,
                  crossings_reduced_by=before_totals['crossings']-after_totals['crossings'],
                  edge_length_reduced_by=round(before_totals['edge_length']-after_totals['edge_length'], 6),
                  metric_definition='Proper intersections of local straight center-to-center dependency segments; shared endpoints and collinear segments excluded. Cross-chapter links reported separately.',
                  warning_policy=dict(long_edge_columns=LONG_EDGE_COLUMNS,
                                      crossing_density=CROSSING_DENSITY_WARNING,
                                      meaning='Review warnings; real dependencies are retained. Structural failures are overlaps, cycles and non-forward local edges.'),
                  scope='Static coordinates and graph verification only; client zoom, labels, tooltips and hidden-node appearance still require Minecraft UI review.',
                  zones='Technology, magic and research order seeds with a separate optional epoch strip. Dependency constraints take precedence over lane preference.',
                  chapters=entries)
    return pending, report


def preview(root=ROOT):
    """Compute and validate the proposed layout without changing any files."""
    _, report = _plan(root)
    report['applied'] = False
    return report


def apply(root=ROOT, report_path=None):
    """Lay out every existing chapter; never create/delete a chapter container."""
    root = Path(root)
    pending, report = _plan(root)
    # Complete all validations before the first write; worlds and FTB team files
    # are never opened. Existing IDs therefore retain their saved progress.
    for path, chapter in pending:
        path.write_text(json.dumps(chapter, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report['applied'] = True
    destination = Path(report_path) if report_path else root/'implementation/layout-v5-report.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='Write x/y coordinates after checking every chapter')
    mode.add_argument('--preview', action='store_true', help='Compute proposed metrics without changing files')
    args = parser.parse_args()
    report = apply(args.root) if args.apply else preview(args.root) if args.preview else audit(args.root)
    print(json.dumps({key: value for key, value in report.items() if key != 'chapters'}, ensure_ascii=False, indent=2))
