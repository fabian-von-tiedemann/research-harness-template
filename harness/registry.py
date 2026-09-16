"""Versioned knowledge register. Validates declarations, never their truth."""
from __future__ import annotations
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

SECTIONS = ('sources', 'claims', 'documents')
CLAIM_TYPES = {'observation', 'hypothesis', 'interpretation', 'derivation', 'model_result'}
STATUSES = {'open', 'provisional', 'bounded_support', 'weakened', 'refuted', 'superseded'}
REVIEW_STATUSES = {'unreviewed', 'reviewed', 'needs_review'}
SOURCE_KINDS = ('literature', 'transcript', 'empirical_report', 'dataset', 'model_trial', 'analysis', 'note')


def _load(root):
    return json.loads((Path(root) / 'knowledge/registry.json').read_text(encoding='utf-8'))


def _nodes(data):
    return {n['id']: n for section in SECTIONS for n in data.get(section, [])}


def _dependencies(node):
    return list(dict.fromkeys(node.get('depends_on', []) + [e['source'] for e in node.get('evidence', [])]))


def _safe_path(root, path):
    if not isinstance(path, str) or Path(path).is_absolute():
        raise ValueError('Expected relative path')
    result = (Path(root) / path).resolve()
    if not result.is_relative_to(Path(root).resolve()):
        raise ValueError('Path escapes repository')
    return result


def _dated_history(entries, allowed, current):
    if not isinstance(entries, list) or not entries or any(not isinstance(h, dict) or h.get('status') not in allowed or not h.get('reason') for h in entries):
        return False
    try:
        dates = [date.fromisoformat(h['date']) for h in entries]
    except (KeyError, TypeError, ValueError):
        return False
    return dates == sorted(dates) and entries[-1]['status'] == current


def validate_registry(root):
    errors = []

    def fail(code, message):
        errors.append({'code': code, 'message': message})

    try:
        data = _load(root)
    except (OSError, ValueError) as exc:
        return [{'code': 'registry_read', 'message': str(exc)}]
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        return [{'code': 'schema_version', 'message': 'Expected registry schema_version 1'}]
    nodes, sections = {}, {}
    for section in SECTIONS:
        if not isinstance(data.get(section), list):
            fail('shape', f'{section}: expected list')
            continue
        for n in data[section]:
            if not isinstance(n, dict) or not isinstance(n.get('id'), str) or not n['id']:
                fail('shape', f'{section}: missing string id')
                continue
            ident = n['id']
            if ident in nodes:
                fail('duplicate_id', ident)
            nodes[ident], sections[ident] = n, section
            if not isinstance(n.get('depends_on', []), list) or any(not isinstance(x, str) for x in n.get('depends_on', [])):
                fail('shape', f'{ident}: depends_on must be strings')
            if not isinstance(n.get('evidence', []), list) or any(not isinstance(e, dict) or not isinstance(e.get('source'), str) for e in n.get('evidence', [])):
                fail('shape', f'{ident}: evidence must contain source IDs')
    if any(e['code'] == 'shape' for e in errors):
        return errors
    for ident, n in nodes.items():
        for dep in _dependencies(n):
            if dep not in nodes:
                fail('missing_reference', f'{ident} -> {dep}')
        if sections[ident] == 'sources':
            if any(sections.get(d) != 'sources' for d in _dependencies(n)):
                fail('source_dependency', ident)
            for key in ('family', 'version', 'snapshot', 'sha256', 'origin', 'anchor', 'access', 'kind'):
                if not isinstance(n.get(key), str) or not n[key]:
                    fail('source_metadata', f'{ident}: {key}')
            if n.get('kind') not in SOURCE_KINDS:
                fail('source_kind', ident)
            try:
                content = _safe_path(root, n.get('snapshot')).read_bytes()
                if hashlib.sha256(content).hexdigest() != n.get('sha256'):
                    fail('snapshot_hash', ident)
                anchor = n.get('anchor')
                if not isinstance(anchor, str) or not anchor.startswith('L'):
                    fail('source_anchor', ident)
                else:
                    parts = anchor[1:].split('-L')
                    start, end = int(parts[0]), int(parts[-1])
                    if not 1 <= start <= end <= len(content.decode('utf-8').splitlines()):
                        fail('source_anchor', ident)
            except (OSError, ValueError, TypeError, UnicodeError):
                fail('snapshot_read', ident)
        if sections[ident] == 'claims':
            if n.get('type') not in CLAIM_TYPES:
                fail('claim_type', ident)
            if n.get('status') not in STATUSES:
                fail('claim_status', ident)
            if not isinstance(n.get('version'), int) or isinstance(n.get('version'), bool) or n['version'] < 1:
                fail('claim_version', ident)
            if n.get('review_status') not in REVIEW_STATUSES:
                fail('review_status', ident)
            if not _dated_history(n.get('review_history'), REVIEW_STATUSES, n.get('review_status')):
                fail('review_history', ident)
            if not _dated_history(n.get('history'), STATUSES, n.get('status')):
                fail('status_history', ident)
            if any(not isinstance(n.get(k), str) or not n[k] for k in ('statement', 'scope', 'reconsider_if')):
                fail('claim_metadata', ident)
            if not _dependencies(n):
                fail('missing_premise', ident)
            for e in n.get('evidence', []):
                source = nodes.get(e['source'], {})
                if sections.get(e['source']) != 'sources':
                    fail('evidence_source', f'{ident}: {e["source"]}')
                if e.get('relation') not in ('supports', 'opposes', 'limits', 'origin'):
                    fail('evidence_relation', ident)
                if not e.get('anchor') or not e.get('reading'):
                    fail('evidence_anchor', ident)
                if e.get('anchor') != source.get('anchor'):
                    fail('evidence_anchor', f'{ident}: evidence must select the preserved source excerpt')
                if n.get('type') == 'observation' and e.get('relation') == 'supports' and source.get('kind') not in ('transcript', 'empirical_report'):
                    fail('observation_from_nonobservation', ident)
                if n.get('type') == 'model_result' and e.get('relation') == 'supports' and source.get('kind') != 'model_trial':
                    fail('model_result_from_nontrial', ident)
        if sections[ident] == 'documents':
            if not isinstance(n.get('path'), str) or not n['path']:
                fail('document_path', ident)
    colors = {}

    def visit(ident):
        if colors.get(ident) == 1:
            fail('dependency_cycle', ident)
            return
        if colors.get(ident) == 2:
            return
        colors[ident] = 1
        for dep in _dependencies(nodes[ident]):
            if dep in nodes:
                visit(dep)
        colors[ident] = 2

    for ident in nodes:
        visit(ident)
    versions, paths = set(), {}
    for n in data.get('sources', []):
        pair = (n.get('origin'), n.get('version'))
        if pair in versions:
            fail('duplicate_source_version', n['id'])
        versions.add(pair)
        path = n.get('snapshot')
        if path in paths and paths[path] != n.get('sha256'):
            fail('snapshot_reused', n['id'])
        paths[path] = n.get('sha256')
    return errors


def _valid(root):
    errors = validate_registry(root)
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=False))
    return _load(root)


def context(root, ids):
    """Records for the given IDs and everything they rest on, with source excerpts inlined."""
    data = _valid(root)
    nodes = _nodes(data)
    selected = set()

    def select(ident):
        if ident not in nodes:
            raise ValueError(f'Unknown ID: {ident}')
        if ident in selected:
            return
        selected.add(ident)
        for dep in _dependencies(nodes[ident]):
            select(dep)

    for ident in ids:
        select(ident)
    source_ids = {n['id'] for n in data['sources']}
    records, log = [], []
    for ident in sorted(selected):
        n = dict(nodes[ident])
        if ident in source_ids:
            n['excerpt'] = _safe_path(root, n['snapshot']).read_text(encoding='utf-8')
        records.append(n)
        log.append({'id': ident, 'action': 'included', 'reason': 'requested' if ident in ids else 'dependency'})
    return {'schema_version': 1, 'records': records, 'selection_log': log}


def impact(root, changed_ids):
    """Everything that rests on the changed IDs, at any depth, as review proposals."""
    data = _valid(root)
    nodes = _nodes(data)
    unknown = set(changed_ids) - nodes.keys()
    if unknown:
        raise ValueError(f'Unknown IDs: {sorted(unknown)}')
    affected = set(changed_ids)
    reasons = {ident: 'changed' for ident in affected}
    while True:
        added = {ident for ident, n in nodes.items() if ident not in affected and set(_dependencies(n)) & affected}
        if not added:
            break
        for ident in added:
            reasons[ident] = 'depends_on:' + ','.join(sorted(set(_dependencies(nodes[ident])) & affected))
        affected |= added
    return {'schema_version': 1, 'changed': sorted(changed_ids), 'affected': {section: [n['id'] for n in data[section] if n['id'] in affected] for section in SECTIONS}, 'review_proposals': [{'id': i, 'reason': reasons[i], 'action': 'review_no_automatic_status_change'} for i in sorted(affected)]}


def snapshot(root, file):
    """Copy a file into knowledge/snapshots/<sha256>.txt and return what a source entry needs."""
    file = Path(file)
    content = file.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    rel = f'knowledge/snapshots/{sha}.txt'
    target = Path(root) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(file, target)
    lines = len(content.decode('utf-8').splitlines())
    anchor = f'L1-L{max(lines, 1)}'
    skeleton = {'id': 'S<NNN>', 'family': 'S<NNN>', 'version': f'{date.today().isoformat()}-v1', 'snapshot': rel, 'sha256': sha, 'origin': str(file), 'anchor': anchor, 'kind': '<one of ' + ' | '.join(SOURCE_KINDS) + '>', 'access': '<how you obtained it and whether it may be quoted>', 'depends_on': []}
    return {'sha256': sha, 'snapshot': rel, 'anchor': anchor, 'lines': lines, 'source_skeleton': skeleton}


def build_index(root):
    data = _valid(root)
    rows = ['# Knowledge index', '', 'Generated from `registry.json` by `python3 -m harness index`. Status is a declaration of how much the evidence carries; review status says whether anyone other than the author has checked. Neither is set automatically.', '', '| ID | Version | Type | Status | Review | Statement |', '|---|---|---|---|---|---|']
    for n in data['claims']:
        rows.append(f'| {n["id"]} | {n["version"]} | {n["type"]} | {n["status"]} | {n["review_status"]} | {n["statement"].replace("|", " / ")} |')
    rows.extend(['', '## Sources', ''])
    for family in sorted({n['family'] for n in data['sources']}):
        rows.append(f'- {family}: ' + ', '.join(f'{n["id"]} ({n["kind"]}, {n["version"]})' for n in data['sources'] if n['family'] == family))
    rows.extend(['', '## Documents', ''])
    for n in data['documents']:
        rows.append(f'- {n["id"]}: `{n["path"]}` depends on ' + ', '.join(n.get('depends_on', [])))
    return '\n'.join(rows) + '\n'
