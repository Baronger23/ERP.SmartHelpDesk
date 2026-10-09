"""Extract and render Markdown Mermaid blocks with Playwright/Edge.

Requires Node/npx and the existing Playwright dependency for PNG previews.
The Mermaid library comes from the pinned CLI npm cache; no project dependency edits.
"""
from pathlib import Path
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]


def run(args, env=None):
    result=subprocess.run(args,cwd=REPO,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    if result.stdout: print(result.stdout,flush=True)
    if result.stderr: print(result.stderr,flush=True)
    result.check_returncode()


def main():
    sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',help='Comma-separated diagram names/globs, e.g. 04_mo_hinh_du_lieu,ai_*')
    parser.add_argument('--skip-previews',action='store_true',help='Skip native SVG browser PNG previews')
    options=parser.parse_args()
    edge=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
    if not edge.exists(): edge=Path('C:/Program Files/Microsoft/Edge/Application/msedge.exe')
    if not edge.exists(): raise RuntimeError('Edge executable not found; provide an installed Chromium path.')
    npx='npx.cmd' if os.name=='nt' else 'npx'
    docs=[ROOT.parent/'02_kien_truc_logic_va_du_lieu.md',*sorted((ROOT.parent/'modules').glob('*.md')),*sorted((ROOT.parent/'ai_architecture').glob('[0-9]*.md'))]
    blocks=[]
    for p in docs:
        code=re.findall(r'```mermaid\s*\n(.*?)```',p.read_text(encoding='utf-8'),re.S)
        base='ai_'+p.stem if p.parent.name=='ai_architecture' else p.name[:3]+'_luong_nghiep_vu' if p.parent.name=='modules' else '04_mo_hinh_du_lieu'
        for number,body in enumerate(code,1):
            name=base+f'_{number:02}' if p.parent.name=='ai_architecture' or len(code)>1 else base
            if options.only and not any(fnmatch.fnmatchcase(name,pattern) for pattern in options.only.split(',')): continue
            (ROOT/(name+'.mmd')).write_text(body.strip()+'\n',encoding='utf-8')
            blocks.append((name,body))
    env=os.environ.copy();env['PUPPETEER_SKIP_DOWNLOAD']='true'
    with tempfile.TemporaryDirectory(prefix='ais-mermaid-') as folder:
        tmp=Path(folder)
        cache=Path(os.environ.get('LOCALAPPDATA',''))/'npm-cache'/'_npx'
        candidates=[]
        for package in cache.glob('*/node_modules/@mermaid-js/mermaid-cli/package.json'):
            if json.loads(package.read_text(encoding='utf-8')).get('version')=='11.12.0':
                vendor=package.parents[2]/'mermaid'/'dist'
                if (vendor/'mermaid.esm.min.mjs').exists(): candidates.append(vendor)
        if not candidates: raise RuntimeError('Pinned Mermaid library missing: run npx --yes --package @mermaid-js/mermaid-cli@11.12.0 mmdc --help once.')
        jobs=tmp/'jobs.json'; jobs.write_text(json.dumps([{'name':name,'source':body,'output':str(tmp/f'flow-{i}.svg')} for i,(name,body) in enumerate(blocks,1)]),encoding='utf-8')
        run(['node',str(ROOT/'render_mermaid.cjs'),str(jobs),str(candidates[0]),str(ROOT/'mermaid_config.json'),str(edge)],env)
        for i,(name,_) in enumerate(blocks,1):
            image=tmp/f'flow-{i}.svg'
            if not image.exists(): raise RuntimeError(f'Missing rendered Mermaid output: {image}')
            (ROOT/(name+'.svg')).write_bytes(image.read_bytes())
    previews=[] if options.skip_previews else [('01_tong_quan_he_thong',1660),('02_chuoi_gia_tri',1100),('03_quan_he_module',1380),('05_agent_harness',1500)]
    for name,height in previews:
        run([npx,'playwright','screenshot','--browser','chromium','--channel','msedge','--viewport-size',f'1920,{height}',(ROOT/(name+'.svg')).as_uri(),str(ROOT/(name+'.png'))])
    print(f'Rendered {len(blocks)} Mermaid diagrams and {len(previews)} browser PNG previews.')


if __name__=='__main__': main()
