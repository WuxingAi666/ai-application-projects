"""Render reviewed project facts into static HTML, resume and public RAG files.

Edit frontend/content/projects.json, then run this script. No API calls required.
--check checks generated outputs without changing them.
"""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START, END = '<!-- PROJECTS:START -->', '<!-- PROJECTS:END -->'
RSTART, REND = '<!-- RESUME-PROJECTS:START -->', '<!-- RESUME-PROJECTS:END -->'


def esc(value):
    return html.escape(str(value), quote=True)


def card(p, rank):
    tags = ''.join(f'<span class="tag">{esc(t)}</span>' for t in p['tags'])
    preview_tags = ''.join(f'<span class="tag">{esc(t)}</span>' for t in p['tags'][:4])
    preview = ''.join(f'<li><b>{esc(k)}</b><span>{esc(v)}</span></li>' for k, v in p['preview'])
    bullets = ''.join(f'<li><b>{esc(k)}</b><p>{esc(v)}</p></li>' for k, v in p['highlights'])
    details = ''.join(f'<div class="detail-point"><h4>{esc(k)}</h4><p>{esc(v)}</p></div>' for k, v in p['details'])
    links = ''.join(f'<a class="detail-link" href="{esc(link["url"])}" target="_blank" rel="noopener noreferrer">{esc(link["label"])} ↗</a>' for link in p['links'])
    github_link = next(link for link in p['links'] if 'github.com/' in link['url'])
    quick_links = f'<a href="{esc(github_link["url"])}" target="_blank" rel="noopener noreferrer" aria-label="{esc(p["title"])}：GitHub 源码或说明">GitHub ↗</a>'
    for link in p['links']:
        if 'github.io/' in link['url']:
            quick_links += f'<a href="{esc(link["url"])}" target="_blank" rel="noopener noreferrer">在线体验 ↗</a>'
    feature = '<span class="work-feature">重点项目</span>' if rank == 1 else ''
    return f'''<article class="work-card reveal" id="{esc(p['anchor'])}" data-project="{esc(p['id'])}">
      <div class="work-kicker"><span class="work-category"><span class="project-rank">{rank:02}</span>{esc(p['category'])}</span>{feature}</div>
      <h3 class="work-title">{esc(p['title'])}</h3>
      <p class="work-state"><span aria-hidden="true"></span>{esc(p['status'])}</p>
      <p class="work-summary">{esc(p['summary'])}</p>
      <ul class="work-highlights">{preview}</ul>
      <div class="work-tags tags" aria-label="主要技术">{preview_tags}</div>
      <div class="work-footer">
        <details class="work-detail" id="details-{esc(p['id'])}" data-title="{esc(p['title'])}" data-rank="{rank:02}">
          <summary>查看项目详情<span aria-hidden="true">↗</span></summary>
          <div class="work-detail-body">
            <p class="detail-state">{esc(p['category'])} · {esc(p['status'])}</p>
            <p class="detail-intro">{esc(p['description'])}</p>
            <div class="detail-section"><h3>实际实现与职责</h3><ul class="detail-highlights">{bullets}</ul></div>
            <div class="detail-section"><h3>处理链路</h3><p class="detail-caption">以下为处理流程示意。</p><picture class="detail-flow"><source media="(max-width:600px)" srcset="assets/project-{esc(p['id'])}-mobile.svg"><img src="assets/project-{esc(p['id'])}.svg" alt="{esc(p['title'])}处理流程示意：{esc(' → '.join(p['pipeline']))}" loading="lazy" decoding="async"></picture></div>
            <div class="detail-section"><h3>设计取舍与实践复盘</h3>{details}</div>
            <div class="detail-section detail-boundary"><h3>当前状态与边界</h3><p>{esc(p['note'])}</p></div>
            <div class="detail-section"><h3>完整技术栈</h3><div class="tags">{tags}</div></div>
            <div class="detail-section"><h3>源码与相关入口</h3><div class="detail-links">{links}</div></div>
          </div>
        </details>
        <div class="work-links">{quick_links}</div>
      </div>
    </article>'''


def project_section(projects):
    names = {'rag': 'RAG', 'speech': '语音情感', 'boss': 'BOSS 工具', 'ledger': '记账本', 'fruit': '果蔬识别', 'coze': 'Coze'}
    nav = ''.join(f'<a href="#{esc(p["anchor"])}"><span>{i:02}</span> {esc(names[p["id"]])}</a>' for i, p in enumerate(projects, 1))
    cards = [card(p, i) for i, p in enumerate(projects, 1)]
    return f'''{START}
<section id="proj" class="shade">
  <div class="wrap">
    <div class="sec-head reveal" data-label="SELECTED PROJECTS"><h2 class="sec-title"><span class="sec-no">02</span>项目作品</h2><p class="sec-sub">六个项目，连接业务需求、模型集成与应用交付。查看详情，了解完整实现、技术取舍与当前状态。</p></div>
    <nav class="project-index" aria-label="项目快速定位">{nav}</nav>
    <div class="work-grid">{''.join(cards)}</div>
  </div>
</section>
{END}'''


def resume_section(projects):
    rows = []
    for p in projects:
        bullets = ''.join(f'<li>{esc(t)}</li>' for t in p['resume'])
        rows.append(f'<div class="rsm-t sub">{esc(p["title"])}<span class="rsm-date">{esc(p["status"])}</span></div><div class="rsm-org">技术栈：{esc(" · ".join(p["tags"]))}</div><ul>{bullets}</ul>')
    return RSTART + '\n<div class="rsm-row"><div class="rsm-k">项目经验</div><div class="rsm-v">' + ''.join(rows) + '</div></div>\n' + REND


def diagram(p, mobile=False):
    width, height = (480, 268) if mobile else (1000, 220)
    boxes = [(24 + (i % 2) * 232, 58 + (i // 2) * 96, 200, 76) for i in range(4)] if mobile else [(24 + i * 246, 69, 222, 90) for i in range(4)]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{esc(p["title"])}流程示意</title><rect width="{width}" height="{height}" fill="#f3f7fd"/>', '<g font-family="Arial,Microsoft YaHei,sans-serif">', '<text x="24" y="32" font-size="12" font-weight="700" fill="#55749b">APPLICATION FLOW / 处理流程示意</text>']
    for i, ((x, y, w, h), label) in enumerate(zip(boxes, p['pipeline'])):
        parts += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="white" stroke="#cbd9ea"/>', f'<text x="{x+15}" y="{y+26}" font-size="12" fill="#7890ae">0{i+1}</text>', f'<text x="{x+15}" y="{y+53}" font-size="16" font-weight="600" fill="#23466f">{esc(label)}</text>']
        if not mobile and i < 3:
            parts.append(f'<path d="M{x+w+5} {y+h/2}h14m-5-5 5 5-5 5" fill="none" stroke="#8ba6c7" stroke-width="1.5"/>')
    parts += ['</g></svg>']
    return ''.join(parts)


def knowledge(p):
    lines = [f'【{p["title"]}】', p['description'], f'材料依据：{p["evidence"]}。当前状态：{p["status"]}。', '', '【实际实现与实践】']
    lines += [f'{k}：{v}' for k, v in p['highlights']]
    lines += ['', '【设计与边界】'] + [f'{k}：{v}' for k, v in p['details']]
    lines += [p['note'], '', '【公开入口】'] + [f'{x["label"]}：{x["url"]}' for x in p['links']]
    if p['id'] == 'rag':
        lines += ['', '【配置细节】', 'TextLoader 加载公开 TXT，RecursiveCharacterTextSplitter 默认按 420 字符分块、80 字符重叠；默认硅基流动 BAAI/bge-m3 向量，可切换本地 BGE。生成模型接入 DeepSeek Chat API，具体模型名以配置为准。']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    projects = json.loads((ROOT / 'frontend/content/projects.json').read_text(encoding='utf-8'))
    assert len(projects) == 6 and len({p['id'] for p in projects}) == 6
    path = ROOT / 'frontend/index.html'
    source = path.read_text(encoding='utf-8')
    if START not in source:
        a = source.index('<section id="proj"')
        b = source.index('</section>', a) + len('</section>')
    else:
        a, b = source.index(START), source.index(END) + len(END)
    source = source[:a] + project_section(projects) + source[b:]
    if RSTART not in source:
        a = source.rfind('<div class="rsm-row">', 0, source.index('<div class="rsm-k">项目经验'))
        b = source.index('<div class="rsm-row">', source.index('<div class="rsm-k">项目经验'))
    else:
        a, b = source.index(RSTART), source.index(REND) + len(REND)
    source = source[:a] + resume_section(projects) + source[b:]
    outputs = {path: source}
    manifest_path = ROOT / 'backend/data/public/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    # Replace all project entries together so citations follow the reordered cards.
    manifest = [x for x in manifest if x['id'] not in {p['knowledge_id'] for p in projects}]
    for p in projects:
        outputs[ROOT / 'backend/data/public' / p['knowledge_file']] = knowledge(p)
        manifest.append({'id': p['knowledge_id'], 'file': p['knowledge_file'], 'title': p['title'], 'anchor': p['anchor']})
        for mobile in (False, True):
            suffix = '-mobile' if mobile else ''
            outputs[ROOT / f'frontend/assets/project-{p["id"]}{suffix}.svg'] = diagram(p, mobile)
    outputs[manifest_path] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    stale = [str(p.relative_to(ROOT)) for p, content in outputs.items() if not p.exists() or p.read_text(encoding='utf-8') != content]
    if args.check:
        if stale:
            raise SystemExit('Generated content out of date: ' + ', '.join(stale))
        print('Project cards, resume, diagrams and knowledge are synchronized.')
    else:
        for p, content in outputs.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8')
        print(f'Synchronized {len(projects)} projects into {len(outputs)} files.')


if __name__ == '__main__':
    main()
