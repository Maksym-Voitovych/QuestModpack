#!/usr/bin/env python3
"""Check compiled optional Mixin selectors against supplied class-file artifacts.

This reads JVM annotations and real method bytecode; it does not execute Mixin,
resolve Minecraft mappings, simulate slices, or certify a complete client boot.
No target artifact means BLOCKED, never a successful source-only audit.
"""
import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, count):
        assert 0 <= count <= len(self.data) - self.pos, 'Truncated JVM class file'
        value = self.data[self.pos:self.pos + count]
        self.pos += count
        return value

    def number(self, size):
        return int.from_bytes(self.take(size), 'big')

    def u1(self): return self.number(1)
    def u2(self): return self.number(2)
    def u4(self): return self.number(4)


def class_file(raw):
    r = Reader(raw)
    assert r.u4() == 0xCAFEBABE, 'Not a JVM class file'
    r.u2(); major = r.u2()
    pool = [None] * r.u2()
    i = 1
    while i < len(pool):
        tag = r.u1()
        if tag == 1:
            pool[i] = (tag, r.take(r.u2()).decode('utf-8', errors='replace'))
        elif tag in (3, 4):
            data = r.take(4)
            pool[i] = (tag, struct.unpack('>i' if tag == 3 else '>f', data)[0])
        elif tag in (5, 6):
            pool[i] = (tag, r.take(8)); i += 1
        elif tag in (7, 8, 16, 19, 20): pool[i] = (tag, r.u2())
        elif tag in (9, 10, 11, 12, 17, 18): pool[i] = (tag, r.u2(), r.u2())
        elif tag == 15: pool[i] = (tag, r.u1(), r.u2())
        else: raise AssertionError(('Unsupported constant-pool tag', tag))
        i += 1

    def utf(index):
        assert pool[index][0] == 1
        return pool[index][1]

    def annotation(a):
        name = utf(a.u2())
        values = {}
        for _ in range(a.u2()):
            key = utf(a.u2()); values[key] = element(a)
        return {'type': name, **values}

    def element(a):
        tag = chr(a.u1())
        if tag in 'BCDFIJSZs':
            index = a.u2()
            return utf(index) if tag == 's' else pool[index][1]
        if tag == 'e': return {'enum_type': utf(a.u2()), 'name': utf(a.u2())}
        if tag == 'c': return utf(a.u2())
        if tag == '@': return annotation(a)
        if tag == '[': return [element(a) for _ in range(a.u2())]
        raise AssertionError(('Unsupported annotation element', tag))

    def attributes():
        result = {}
        for _ in range(r.u2()):
            name = utf(r.u2()); value = r.take(r.u4())
            result[name] = value
        return result

    def annotations(attrs):
        found = []
        for name in ('RuntimeVisibleAnnotations', 'RuntimeInvisibleAnnotations'):
            if name in attrs:
                a = Reader(attrs[name]); found.extend(annotation(a) for _ in range(a.u2()))
        return found

    r.u2(); name = utf(pool[r.u2()][1]); parent = r.u2()
    super_name = utf(pool[parent][1]) if parent else None
    for _ in range(r.u2()): r.u2()
    for _ in range(r.u2()):
        r.take(6); attributes()
    methods = []
    for _ in range(r.u2()):
        access, method, desc = r.u2(), utf(r.u2()), utf(r.u2())
        attrs = attributes(); code = b''
        if 'Code' in attrs:
            a = Reader(attrs['Code']); a.take(4); code = a.take(a.u4())
        methods.append({'name': method, 'descriptor': desc, 'access': access,
                        'annotations': annotations(attrs), 'code': code})
    attrs = attributes()
    assert r.pos == len(raw), 'Trailing JVM class-file bytes'
    return {'name': name, 'super': super_name, 'major': major, 'methods': methods,
            'annotations': annotations(attrs), 'pool': pool}


def invocations(data, method):
    """Walk instruction boundaries, including switch padding and WIDE operands."""
    code, pool = method['code'], data['pool']
    one = {0x10, 0x12, *range(0x15, 0x1a), *range(0x36, 0x3b), 0xa9, 0xbc}
    two = {0x11, 0x13, 0x14, 0x84, *range(0x99, 0xa9), *range(0xb2, 0xb9),
           0xbb, 0xbd, 0xc0, 0xc1, 0xc6, 0xc7}
    position, found = 0, []
    while position < len(code):
        start, opcode = position, code[position]; position += 1
        if opcode in (0xb6, 0xb7, 0xb8, 0xb9):
            index = int.from_bytes(code[position:position + 2], 'big')
            ref = pool[index]
            assert ref[0] in (10, 11), 'Invocation does not reference a method'
            owner = pool[pool[ref[1]][1]][1]
            pair = pool[ref[2]]
            found.append({'owner': owner, 'name': pool[pair[1]][1],
                          'descriptor': pool[pair[2]][1], 'offset': start})
        if opcode in one: position += 1
        elif opcode in two: position += 2
        elif opcode in (0xb9, 0xba, 0xc8, 0xc9): position += 4
        elif opcode == 0xc5: position += 3
        elif opcode == 0xc4:
            assert position < len(code)
            position += 5 if code[position] == 0x84 else 3
        elif opcode in (0xaa, 0xab):
            position += (-position) % 4
            if opcode == 0xaa:
                low = int.from_bytes(code[position + 4:position + 8], 'big', signed=True)
                high = int.from_bytes(code[position + 8:position + 12], 'big', signed=True)
                assert high >= low
                position += 12 + 4 * (high - low + 1)
            else:
                pairs = int.from_bytes(code[position + 4:position + 8], 'big', signed=True)
                assert pairs >= 0
                position += 8 + 8 * pairs
        assert position <= len(code), ('Truncated bytecode instruction', start)
    return found


def artifact(path):
    path = Path(path)
    if path.is_dir():
        files = {p.relative_to(path).as_posix()[:-6]: p.read_bytes() for p in path.rglob('*.class')}
        digest = hashlib.sha256(json.dumps({n: hashlib.sha256(b).hexdigest() for n, b in sorted(files.items())}, sort_keys=True).encode()).hexdigest()
    else:
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None, 'JAR CRC failure'
            files = {n[:-6]: z.read(n) for n in z.namelist() if n.endswith('.class')}
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return files, {'name': path.name, 'sha256': digest, 'classes': len(files)}


def method_matches(selector, method):
    if selector.startswith('L') and ';' in selector: selector = selector.split(';', 1)[1]
    if '(' in selector:
        name, descriptor = selector.split('(', 1)
        return fnmatch.fnmatchcase(method['name'], name) and method['descriptor'] == '(' + descriptor
    return fnmatch.fnmatchcase(method['name'], selector)


def check(guard_path, target_paths, prefix='moze_intel/projecte/', mixin_names=None):
    guard, guard_info = artifact(guard_path)
    targets, artifacts = {}, []
    for path in target_paths:
        classes, info = artifact(path); artifacts.append(info)
        for name, raw in classes.items():
            assert name not in targets or targets[name] == raw, ('Conflicting artifact classes', name)
            targets[name] = raw
    result = {'schema': 1, 'status': 'BLOCKED', 'scope': 'compiled annotation/method/invocation contracts only',
              'guard': guard_info, 'target_artifacts': artifacts, 'prefix': prefix,
              'checked_mixins': [], 'checks': [], 'errors': [], 'unverified_details': [],
              'actual_mixin_transform': 'NOT_RUN', 'full_client_boot': 'NOT_RUN',
              'installed_binary_provenance': 'Input artifact SHA recorded; compare with the installed JAR separately.'}
    if not target_paths:
        result['errors'].append({'kind': 'missing_artifacts', 'message': 'No target JAR supplied; source evidence cannot certify compiled selectors.'})
        return result
    for mixin_class, raw in sorted(guard.items()):
        if mixin_names and mixin_class.rsplit('/', 1)[-1] not in mixin_names: continue
        data = class_file(raw)
        configs = [a for a in data['annotations'] if a['type'] == 'Lorg/spongepowered/asm/mixin/Mixin;']
        for config in configs:
            names = config.get('targets', []) + [v[1:-1] for v in config.get('value', [])]
            for target in names:
                target = target.replace('.', '/')
                if not target.startswith(prefix): continue
                label = mixin_class.rsplit('/', 1)[-1]
                if label not in result['checked_mixins']: result['checked_mixins'].append(label)
                if target not in targets:
                    result['errors'].append({'kind': 'missing_class', 'mixin': label, 'target': target}); continue
                target_data = class_file(targets[target])
                for handler in data['methods']:
                    for annotation in handler['annotations']:
                        if not annotation['type'].startswith('Lorg/spongepowered/asm/mixin/injection/') or 'method' not in annotation: continue
                        selectors = annotation['method']; selectors = selectors if isinstance(selectors, list) else [selectors]
                        selected = [m for m in target_data['methods'] if any(method_matches(s, m) for s in selectors)]
                        require = annotation.get('require', -1); require = 1 if require < 0 else require
                        entry = {'mixin': label, 'handler': handler['name'], 'target': target, 'selectors': selectors,
                                 'matched_methods': [m['name'] + m['descriptor'] for m in selected], 'require': require, 'invoke_checks': []}
                        result['checks'].append(entry)
                        if not selected and require:
                            result['errors'].append({'kind': 'missing_method', **entry}); continue
                        ats = annotation.get('at', []); ats = ats if isinstance(ats, list) else [ats]
                        for at in ats:
                            if at.get('value') == 'INVOKE' and at.get('target'):
                                match = re.fullmatch(r'L([^;]+);([^()]+)(\(.*)', at['target'])
                                assert match, ('Unsupported method invocation selector', at['target'])
                                owner, name, descriptor = match.groups()
                                count = 0
                                for method in selected:
                                    hits = [i for i in invocations(target_data, method) if (i['owner'], i['name'], i['descriptor']) == (owner, name, descriptor)]
                                    ordinal = at.get('ordinal', -1)
                                    count += len(hits) if ordinal < 0 else int(ordinal < len(hits))
                                item = {'target': at['target'], 'matches': count, 'ordinal': at.get('ordinal', -1)}
                                entry['invoke_checks'].append(item)
                                if count < require: result['errors'].append({'kind': 'missing_invocation', 'mixin': label, 'handler': handler['name'], 'require': require, **item})
                                allow = annotation.get('allow', -1)
                                if allow >= require and allow >= 0 and count > allow:
                                    result['errors'].append({'kind': 'too_many_invocations', 'mixin': label, 'handler': handler['name'], 'allow': allow, **item})
                            elif at.get('value') not in ('HEAD', 'RETURN', 'TAIL', 'INVOKE'):
                                result['unverified_details'].append({'mixin': label, 'handler': handler['name'], 'at': at.get('value'), 'reason': 'Only method selectors and INVOKE sites are checked.'})
                        if annotation.get('slice'):
                            result['unverified_details'].append({'mixin': label, 'handler': handler['name'], 'reason': 'Slices are not evaluated; invocation search covers the selected method.'})
    if not result['checks']:
        result['errors'].append({'kind': 'no_coverage', 'message': 'No requested optional injection contracts found.'})
    result['status'] = 'FAILED' if result['errors'] else 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guard', type=Path, required=True, help='Compiled companion JAR or class directory')
    parser.add_argument('--target-jar', type=Path, action='append', default=[])
    parser.add_argument('--prefix', default='moze_intel/projecte/')
    parser.add_argument('--mixin', action='append', help='Optional simple Mixin class name filter')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = check(args.guard, args.target_jar, args.prefix.replace('.', '/'), set(args.mixin or []) or None)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_text(text)
    print(text, end='')
    return 0 if result['status'].startswith('PASSED_') else 2


if __name__ == '__main__':
    raise SystemExit(main())
