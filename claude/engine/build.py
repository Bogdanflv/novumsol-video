"""Construiește un clip Novum Sol din claude/clipuri/<folder>/clip.json.

Utilizare:
  python claude/engine/build.py claude/clipuri/2026-11-24-test            # randare completă
  python claude/engine/build.py claude/clipuri/2026-11-24-test --preview   # doar cadre PNG de control

clip.json:
{
  "chip": "Tratamente de iarnă",
  "intro": {"kicker": "...", "title": ["Linia 1", "Linia 2"], "sub": "...", "pill": "..."},
  "products": [{"id": 123, "title": "Nume scurt", "maker": "BAYER", "line": "din descrierea oficială"}],
  "outro": {"slogan": "...", "cta": "Comandă acum", "line": "Arad · livrare în toată țara"},
  "pesticide": true
}
Prețurile, promoția și poza se iau AUTOMAT din data/products.json (ziua curentă).
"""
import json, os, re, subprocess, sys

ENGINE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(ENGINE))
DATA = os.path.join(ROOT, 'data')
FPS = 30
T_INTRO, T_PROD, T_OUTRO = 3.5, 4.2, 4.8


def fail(msg):
    print('EROARE:', msg)
    sys.exit(1)


def trimmed(src, folder):
    """Decupează marginile albe ale pozei oficiale (fără alte modificări) ca produsul să umple cardul."""
    from PIL import Image, ImageChops
    im = Image.open(src).convert('RGB')
    diff = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).convert('L').point(lambda v: 255 if v > 18 else 0)
    box = diff.getbbox()
    if box:
        pad = int(max(im.size) * 0.04)
        box = (max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))
        im = im.crop(box)
    out = os.path.join(folder, '_work', 'img_' + os.path.basename(src).rsplit('.', 1)[0] + '.jpg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, quality=92)
    return 'file://' + out


def _norm(t):
    import unicodedata
    t = unicodedata.normalize('NFKD', str(t)).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r'(\d+)[\s,.]*(litri|litru|l)\b', r'\1l', t)
    t = re.sub(r'(\d+)[\s]*(grame|gr|g)\b', r'\1g', t)
    t = re.sub(r'(\d+)[\s]*(kg)\b', r'\1kg', t)
    return re.findall(r'[a-z0-9]+', t)


def check_stock(prods, specs, stock_path):
    """Stocul real vine din aplicația Control Novum Sol (Nexus): data/nexus_stock_history.json.
    Produsul intră în clip doar dacă are stoc liber > 0 în MICRO sau DIVA. Statusul de pe site NU contează."""
    snap = json.load(open(stock_path))
    items = snap['items']
    report = []
    for p, spec in zip(prods, specs):
        if spec.get('nexus'):
            cands = [i for i in items if i['product'].strip().lower() == spec['nexus'].strip().lower()]
        else:
            title = [w for w in _norm(spec.get('title') or p['name']) if not w.isdigit()]
            pack = [w for w in _norm(p['name']) if re.fullmatch(r'\d+(l|g|kg|ml)', w)]
            cands = [i for i in items if all(w in _norm(i['product']) for w in title[:2])
                     and (not pack or pack[0] in _norm(i['product']))]
        if len(cands) != 1:
            fail(f"stoc Nexus: {len(cands)} potriviri pentru „{p['name']}” "
                 f"({[c['product'] for c in cands][:5]}) – adaugă \"nexus\": \"<nume exact>\" în clip.json")
        c = cands[0]
        free = (c.get('micro_free') or 0) + (c.get('diva_free') or 0)
        if free <= 0:
            fail(f"„{p['name']}” NU e în stoc în Nexus ({c['product']}: {c['status']}). Alege alt produs.")
        report.append(f"{p['name']} → Nexus „{c['product']}”: în stoc")
        print('stoc OK', c['product'])
    return snap.get('updated_at'), report


def load(folder):
    clip = json.load(open(os.path.join(folder, 'clip.json')))
    db = json.load(open(os.path.join(DATA, 'products.json')))
    legal = json.load(open(os.path.join(ROOT, 'config', 'legal.json')))
    by_id = {p['id']: p for p in db['products']}
    logo = db.get('logo') or fail('lipsește logo-ul în data/products.json')
    prods = []
    for spec in clip['products']:
        p = by_id.get(spec['id']) or fail(f"produsul {spec['id']} nu există în products.json")
        if not p.get('image'):
            fail(f"{p['name']} nu are poză oficială")
        if not p.get('in_stock'):
            print('ATENȚIE: nu e în stoc ->', p['name'])
        prods.append({
            'title': spec.get('title') or p['name'], 'maker': spec.get('maker', ''), 'line': spec.get('line', ''),
            'price': p['price'], 'regular_price': p['regular_price'], 'on_sale': p['on_sale'],
            'image': trimmed(os.path.join(DATA, p['image']), folder), 'name': p['name'], 'url': p['url'],
        })
    # verificare cuvinte interzise
    blob = json.dumps(clip, ensure_ascii=False).lower()
    post = os.path.join(folder, 'postare.txt')
    if os.path.exists(post):
        blob += open(post).read().lower()
    for w in legal['interzis']:
        if w in blob:
            fail(f'cuvânt interzis: „{w}”')
    stock_path = os.environ.get('NEXUS_STOCK') or os.path.join(folder, '_work', 'nexus_stock_history.json')
    if not os.path.exists(stock_path):
        fail('lipsește stocul din aplicație (nexus_stock_history.json). Copiază-l de pe calculator în ' + stock_path)
    stock_time, stock_report = check_stock(prods, clip['products'], stock_path)
    data = {
        'logo': 'file://' + os.path.join(DATA, logo), 'chip': clip.get('chip', ''),
        'intro': clip['intro'], 'outro': clip['outro'], 'products': prods,
        'legal': legal['art66_ro'] if clip.get('pesticide', True) else None,
        'timing': {'intro': T_INTRO, 'prod': T_PROD, 'outro': T_OUTRO},
    }
    data['_stock'] = (stock_time, stock_report)
    return clip, data, db['synced']


def scenes(data):
    return [('intro', T_INTRO)] + [(f'p{i + 1}', T_PROD) for i in range(len(data['products']))] + [('outro', T_OUTRO)]


def main():
    folder = os.path.abspath(sys.argv[1])
    preview = '--preview' in sys.argv
    clip, data, synced = load(folder)
    work = os.path.join(folder, '_work')
    os.makedirs(work, exist_ok=True)
    html = open(os.path.join(ENGINE, 'template.html')).read()
    open(os.path.join(work, 'index.html'), 'w').write(html)
    open(os.path.join(work, 'clip_data.js'), 'w').write('window.CLIP=' + json.dumps({k: v for k, v in data.items() if k != '_stock'}, ensure_ascii=False) + ';')
    sc = scenes(data)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--allow-file-access-from-files'])
        pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        parts = []
        for name, dur in sc:
            pg.goto(f'file://{work}/index.html?s={name}')
            pg.wait_for_function('window.ready === true')
            if preview:
                for t in (dur * 0.15, dur * 0.55, dur - 0.05):
                    pg.evaluate(f'seek({t * 1000})')
                    pg.screenshot(path=os.path.join(work, f'{name}_{t:.1f}.png'))
                continue
            out = os.path.join(work, f'{name}.mp4')
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS),
                                   '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
                                   '-pix_fmt', 'yuv420p', '-r', str(FPS), out], stdin=subprocess.PIPE)
            for i in range(round(dur * FPS)):
                pg.evaluate(f'seek({i * 1000 / FPS})')
                ff.stdin.write(pg.screenshot(type='jpeg', quality=92))
            ff.stdin.close()
            ff.wait() == 0 or fail('ffmpeg scena ' + name)
            parts.append(out)
            print('ok', name)
        b.close()
    if preview:
        print('preview în', work)
        return
    total = sum(d for _, d in sc)
    starts = [T_INTRO + i * T_PROD for i in range(len(data['products']))]
    subprocess.run([sys.executable, os.path.join(ENGINE, 'music.py'), os.path.join(work, 'music.wav'),
                    str(total), json.dumps(starts)], check=True)
    lst = os.path.join(work, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{x}'\n" for x in parts))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-i', os.path.join(work, 'music.wav'), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', os.path.join(folder, 'clip.mp4')], check=True)
    # surse
    with open(os.path.join(folder, 'surse.md'), 'w') as f:
        f.write(f'# Surse\n\nPrețuri din data/products.json, sincronizat {synced}.\n\n')
        for x in data['products']:
            f.write(f"- {x['name']} – {x['price']} lei" + (f" (preț vechi {x['regular_price']} lei)" if x['on_sale'] else '') + f" – {x['url']}\n")
        f.write(f"\nStoc verificat în aplicația Control Novum Sol (Nexus), actualizat {data['_stock'][0]}:\n")
        for line in data['_stock'][1]:
            f.write(f'- {line}\n')
        if data['legal']:
            f.write(f"\nFraza art. 66: „{data['legal']}”\n")
    print('GATA', os.path.join(folder, 'clip.mp4'), f'{total:.1f}s')


if __name__ == '__main__':
    main()
