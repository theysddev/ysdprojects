"""Копирует работы портфолио с Cloudflare (*.ysdprojects.space) в папки репозитория.
Схема: https://<sub>.ysdprojects.space/<path> -> /<sub>/<path> на GitHub Pages (ysdprojects.space/<sub>/...).
Ссылки от корня ("/x") внутри HTML/CSS переписываются в "/<sub>/x"."""
import hashlib, os, re, sys, urllib.parse, urllib.request, json

SITES = {
 'shop':[''],'miniapp':[''],'kuhni':[''],'assistant':[''],'redesign':[''],'maket':[''],'travel':[''],'watches':[''],
 'studio':[''],'salon':[''],'logistics':[''],'furniture':[''],'hotel':[''],'law':[''],'fintech':[''],'resto':[''],
 'realty':[''],'dental':[''],'barber':[''],'bakery':[''],'cosmo':[''],'garage':[''],'detailing':[''],'stroy':[''],
 'remont':[''],'fitness':[''],'yoga':[''],'kids':[''],'online':[''],
 'bots':['','food/','beauty/','auto/','ai/','realty/','shop/'],
 'slides':['','franchise/','tender/','pitch/','edu/','it/','realty/'],
 'apps':['','dispatch/','crm/','bi/','warehouse/','pm/','kb/'],
 'design':['','nord/','ritm/','terra/','liniya/','daily/'],
}
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
UA = {'User-Agent': 'Mozilla/5.0 (YSD mirror)'}
REF = re.compile(r'''((?:src|href|data-src|poster|content)\s*=\s*["'])([^"'#]+)(["'])|(url\(\s*["']?)([^"')]+)(["']?\s*\))|(srcset\s*=\s*["'])([^"']+)(["'])''')

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.status, r.headers.get('content-type', ''), r.read()
    except urllib.error.HTTPError as e:
        return e.code, '', b''
    except Exception as e:
        print('ERR', url, e); return 0, '', b''

def local_path(sub, path):
    p = urllib.parse.unquote(path.split('?')[0])
    if p.endswith('/'): p += 'index.html'
    return os.path.join(OUT, sub, p.lstrip('/'))

report = {}
for sub, starts in SITES.items():
    host = f'https://{sub}.ysdprojects.space'
    _, _, fallback = get(host + '/__definitely_missing_%s__/' % sub)   # SPA-заглушка Cloudflare Pages
    fb = hashlib.md5(fallback).hexdigest() if fallback else None
    seen, queue, files = set(), ['/' + s for s in starts], 0
    while queue:
        path = queue.pop(0)
        if path in seen: continue
        seen.add(path)
        st, ct, body = get(host + path)
        if st != 200 or not body: continue
        is_html = 'text/html' in ct
        if is_html and path.strip('/') not in [s.strip('/') for s in starts] and hashlib.md5(body).hexdigest() == fb:
            continue  # несуществующая страница, Pages отдал заглушку
        if is_html or 'text/css' in ct:
            text = body.decode('utf-8', 'replace')
            def fix(u):
                if u.startswith('//') or re.match(r'^[a-z]+:', u, re.I): 
                    if u.startswith(host): u = u[len(host):] or '/'
                    else: return u, None
                absu = urllib.parse.urljoin(path, u)
                return ('/' + sub + absu) if u.startswith('/') else u, absu
            def rep(m):
                if m.group(1):
                    pre, u, post = m.group(1), m.group(2), m.group(3)
                    if pre.lower().startswith('content') and not (u.startswith('/') or u.startswith(host)):
                        return m.group(0)
                    new, absu = fix(u)
                    if absu: queue.append(absu.split('?')[0].split('#')[0])
                    return pre + new + post
                if m.group(4):
                    u = m.group(5)
                    if u.startswith('data:'): return m.group(0)
                    new, absu = fix(u)
                    if absu: queue.append(absu.split('?')[0])
                    return m.group(4) + new + m.group(6)
                parts = []
                for part in m.group(8).split(','):
                    bits = part.strip().split()
                    if not bits: continue
                    new, absu = fix(bits[0])
                    if absu: queue.append(absu.split('?')[0])
                    parts.append(' '.join([new] + bits[1:]))
                return m.group(7) + ', '.join(parts) + m.group(9)
            text = REF.sub(rep, text)
            body = text.encode('utf-8')
        fp = local_path(sub, path)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, 'wb') as f: f.write(body)
        files += 1
    report[sub] = files
    print(sub, files, flush=True)

with open(os.path.join(OUT, 'mirror-report.json'), 'w') as f: json.dump(report, f, ensure_ascii=False, indent=1)
