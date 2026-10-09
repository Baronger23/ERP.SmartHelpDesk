"""Validate document links, traceability IDs and exported diagram structures.
Does not verify business requirements or ERP/LLM runtime behavior.
"""
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    documents=list(ROOT.rglob('*.md'))
    joined='\n'.join(p.read_text(encoding='utf-8') for p in documents)
    identifiers={'pain_points':set(re.findall(r'PP-\d{2}',joined)),
                 'stories':set(re.findall(r'US-\d{2}',joined)),
                 'acceptance_stories':set(re.findall(r'AC-(\d{2})\.',joined)),
                 'domain_functions':set(re.findall(r'M\d{2}-F\d{2}',joined))}
    assert identifiers['pain_points']=={f'PP-{i:02}' for i in range(1,21)}
    assert identifiers['stories']=={f'US-{i:02}' for i in range(1,49)}
    assert identifiers['acceptance_stories']=={f'{i:02}' for i in range(1,49)}
    assert len(identifiers['domain_functions'])==60,identifiers['domain_functions']
    for p in ROOT.rglob('*'):
        if p.is_file(): assert p.name==p.name.lower(),p
    links=0
    for p in documents:
        text=p.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if re.match(r'https?://|[A-Za-z]:/|#',target): continue
            assert (p.parent/target.split('#')[0]).exists(),(p.name,target)
            links+=1
    svg_files=list((ROOT/'diagrams').glob('*.svg'))
    for p in svg_files: ET.parse(p)
    for p in (ROOT/'diagrams').glob('*.drawio'):
        for page in ET.parse(p).findall('diagram'):
            cells=page.findall('.//mxCell');ids=[c.get('id') for c in cells]
            assert len(ids)==len(set(ids)),(p.name,page.get('name'))
    for p in (ROOT/'diagrams').glob('*.html'):
        for target in re.findall(r'(?:src|href|value)="([^"]+)"',p.read_text(encoding='utf-8')):
            if target.endswith(('.svg','.drawio','.md','.html','.png')) and not target.startswith('http'):
                assert (p.parent/target).exists(),(p.name,target)
    conformance=json.loads((ROOT/'ai_architecture/contracts/conformance_results.json').read_text(encoding='utf-8'))
    assert conformance['passed_vectors']==conformance['protocol_vectors']==26
    assert not conformance['runtime_integration_tested']
    report={'scope':'documentation_structure_only','markdown_docs':len(documents),
            'ai_design_docs':len(list((ROOT/'ai_architecture').glob('[0-9]*.md'))),
            'domain_modules':len(list((ROOT/'modules').glob('*.md'))),
            **{k:len(v) for k,v in identifiers.items()},'local_links_checked':links,
            'svg_diagrams':len(svg_files),'ai_svg_diagrams':len(list((ROOT/'diagrams').glob('ai_*.svg'))),
            'drawio_pages':len(ET.parse(ROOT/'diagrams/thiet_ke_doanh_nghiep.drawio').findall('diagram')),
            'offline_protocol_vectors_passed':conformance['passed_vectors']}
    (ROOT/'design_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__': main()
