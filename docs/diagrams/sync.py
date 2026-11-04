"""Copy existing diagrams by type; --check verifies copies without writing files."""
import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent


def assets():
    protected_sequences = {'SD01.png', 'SD01.puml', 'SD01.svg',
                           'SD05.png', 'SD05.puml', 'SD05.svg'}
    for week in ('week04', 'week05'):
        for source in sorted((DOCS / week / 'diagrams').iterdir()):
            if not source.is_file():
                continue
            if source.name in protected_sequences:
                continue
            group = ('bfd' if source.stem == 'BFD' else
                     'bpmn' if source.stem.startswith('BPMN') else
                     'use-case' if source.stem.startswith('UC_') else
                     'sequence' if source.stem.startswith('SD') else None)
            if group is None:
                raise ValueError(f'Unclassified diagram: {source}')
            yield HERE / group / source.name, source.read_bytes()
    for name in sorted(protected_sequences):
        yield HERE / 'sequence' / name, (HERE / 'sequence' / name).read_bytes()
    for name in ('ui-mockup.svg', 'ui-mockup-v2.png', 'ui-mockup-figma.png'):
        yield HERE / 'ui-mockup' / name, (DOCS / name).read_bytes()
    groups = {
        'Phân rã chức năng BFD': ('bfd', 'BFD-legacy'),
        'Kiến trúc triển khai local': ('architecture', 'local-architecture'),
        'ERD': ('erd', 'ERD-legacy'),
        'Trạng thái hội thoại': ('state-machine', 'conversation-states'),
        'Sequence hoàn tất và tiếp nhận lại': ('sequence', 'ticket-lifecycle-legacy'),
    }
    assert len(groups) == 5, len(groups)
    ignored_sections = {'Luồng nghiệp vụ mức 0'}
    text = (DOCS / 'DESIGN.md').read_text(encoding='utf-8')
    found = set()
    for section, content in re.findall(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)', text, re.MULTILINE | re.DOTALL):
        blocks = re.findall(r'^```mermaid\n(.*?)^```', content, re.MULTILINE | re.DOTALL)
        if not blocks:
            continue
        if section in ignored_sections:
            continue
        if section not in groups or len(blocks) != 1:
            raise ValueError(f'Unclassified Mermaid section: {section}')
        found.add(section)
        group, name = groups[section]
        yield HERE / group / (name + '.mmd'), (blocks[0].rstrip() + '\n').encode('utf-8')
    assert found == set(groups), 'Missing Mermaid diagram in DESIGN.md'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = dict(assets())
    assert len(expected) == 58, len(expected)
    if not args.check:
        for path, content in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    for path, content in expected.items():
        actual_content = path.read_bytes() if path.is_file() else None
        if actual_content is not None and path.suffix == '.mmd':
            actual_content = actual_content.replace(b'\r\n', b'\n')
        if actual_content != content:
            raise SystemExit(f'Missing or stale copy: {path.relative_to(DOCS)}; run python docs/diagrams/sync.py')
    legacy = {
        HERE / 'flowchart' / 'business-flow-legacy.mmd',
        HERE / 'sequence' / 'rag-late-ai-legacy.mmd',
    }
    actual = {p for p in HERE.rglob('*')
              if p.suffix in {'.png', '.svg', '.puml', '.bpmn', '.mmd'} and p not in legacy}
    assert actual == set(expected), f'Unexpected diagram files: {actual - set(expected)}'
    readme = (HERE / 'README.md').read_text(encoding='utf-8')
    for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', readme):
        assert (HERE / link).exists(), f'Broken diagram index link: {link}'
    print(f'OK: {len(expected)} diagram/mockup files in {len({p.parent for p in expected})} groups; source copies and index links match.')
