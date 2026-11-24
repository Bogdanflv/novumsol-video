"""Copiază produsele, prețurile, pozele și logo-ul de pe novumsol.ro în data/.
Rulează zilnic din GitHub Actions (.github/workflows/sync.yml). Doar stdlib + Pillow."""
import csv, datetime, hashlib, html, io, json, os, re, sys, time, urllib.request
from PIL import Image

SITE = 'https://novumsol.ro'
API = SITE + '/wp-json/wc/store/v1/products'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
IMG = os.path.join(DATA, 'images')
MAXPX = 1000
UA = {'User-Agent': 'Mozilla/5.0 (novumsol-video sync; +https://github.com/Bogdanflv/novumsol-video)'}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), dict(r.headers)
        except Exception as e:
            if i == tries - 1:
                raise
            print('retry', url, e)
            time.sleep(3 * (i + 1))


def text(s):
    s = re.sub(r'<(br|/p|/li|/h\d)[^>]*>', '\n', s or '')
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    return re.sub(r'\n\s*\n+', '\n', re.sub(r'[ \t\xa0]+', ' ', s)).strip()


def money(v, minor):
    return None if v in (None, '') else round(int(v) / 10 ** minor, 2)


def save_image(url, dest_noext, manifest):
    """Descarcă și micșorează la max 1000 px. Sare peste dacă sursa nu s-a schimbat."""
    key = hashlib.sha1(url.encode()).hexdigest()[:12]
    old = manifest.get(dest_noext)
    if old and old['key'] == key and os.path.exists(os.path.join(DATA, old['file'])):
        return old['file']
    raw, _ = get(url)
    if url.lower().split('?')[0].endswith('.svg'):
        rel = f'{dest_noext}.svg'
        for e in ('png', 'jpg'):
            if os.path.exists(os.path.join(DATA, f'{dest_noext}.{e}')):
                os.remove(os.path.join(DATA, f'{dest_noext}.{e}'))
        open(os.path.join(DATA, rel), 'wb').write(raw)
        manifest[dest_noext] = {'key': key, 'src': url, 'file': rel}
        return rel
    im = Image.open(io.BytesIO(raw))
    im.load()
    alpha = im.mode in ('RGBA', 'LA', 'P') and 'transparency' in im.info or im.mode in ('RGBA', 'LA')
    im = im.convert('RGBA' if alpha else 'RGB')
    im.thumbnail((MAXPX, MAXPX), Image.LANCZOS)
    ext = 'png' if alpha else 'jpg'
    rel = f'{dest_noext}.{ext}'
    for e in ('png', 'jpg', 'svg'):
        p = os.path.join(DATA, f'{dest_noext}.{e}')
        if e != ext and os.path.exists(p):
            os.remove(p)
    out = os.path.join(DATA, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if alpha:
        im.save(out, optimize=True)
    else:
        im.save(out, quality=88, optimize=True, progressive=True)
    manifest[dest_noext] = {'key': key, 'src': url, 'file': rel}
    return rel


def find_logo():
    page, _ = get(SITE + '/')
    page = page.decode('utf-8', 'ignore')
    cands = []
    # 1) orice imagine al cărei fișier conține „logo” (SVG întâi), 2) custom-logo, 3) favicon
    srcs = re.findall(r'(?:src|href)="([^"]*?logo[^"]*?\.(?:svg|png|webp|jpe?g))"', page, re.I)
    cands += sorted(dict.fromkeys(srcs), key=lambda u: (not u.lower().endswith('.svg'), 'favicon' in u.lower()))
    for pat in (r'<img[^>]+class="[^"]*custom-logo[^"]*"[^>]*>', r'<img[^>]+(?:alt|class|id)="[^"]*logo[^"]*"[^>]*>'):
        for tag in re.findall(pat, page, re.I):
            m = re.search(r'(?:data-src|src)="([^"]+)"', tag)
            if m and not m.group(1).startswith('data:'):
                cands.append(m.group(1))
    m = re.search(r'<link[^>]+rel="(?:apple-touch-icon|icon)"[^>]+href="([^"]+)"', page, re.I)
    if m:
        cands.append(m.group(1))
    out = []
    for c in cands:
        c = html.unescape(c)
        if c.startswith('//'):
            c = 'https:' + c
        elif c.startswith('/'):
            c = SITE + c
        if c not in out:
            out.append(c)
    return out


def main():
    os.makedirs(IMG, exist_ok=True)
    mpath = os.path.join(DATA, 'images_manifest.json')
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}

    items, page = [], 1
    while True:
        raw, hdr = get(f'{API}?per_page=100&page={page}')
        batch = json.loads(raw)
        items += batch
        total = int(hdr.get('X-WP-TotalPages') or hdr.get('x-wp-totalpages') or 1)
        print(f'page {page}/{total}: {len(batch)}')
        if page >= total or not batch:
            break
        page += 1

    today = datetime.date.today().isoformat()
    products = []
    for p in items:
        pr = p.get('prices') or {}
        mu = pr.get('currency_minor_unit', 2)
        imgs = p.get('images') or []
        rec = {
            'id': p['id'], 'name': html.unescape(p.get('name', '')), 'slug': p.get('slug'),
            'url': p.get('permalink'), 'sku': p.get('sku'),
            'categories': [html.unescape(c['name']) for c in p.get('categories', [])],
            'tags': [html.unescape(t['name']) for t in p.get('tags', [])],
            'brands': [html.unescape(b['name']) for b in p.get('brands', [])] if p.get('brands') else [],
            'attributes': {html.unescape(a['name']): [html.unescape(t['name']) for t in a.get('terms', [])] for a in p.get('attributes', [])},
            'price': money(pr.get('price'), mu), 'regular_price': money(pr.get('regular_price'), mu),
            'sale_price': money(pr.get('sale_price'), mu), 'currency': pr.get('currency_code', 'RON'),
            'on_sale': bool(p.get('on_sale')), 'in_stock': bool(p.get('is_in_stock')),
            'stock': (p.get('stock_availability') or {}).get('text'),
            'type': p.get('type'),
            'short_description': text(p.get('short_description')),
            'description': text(p.get('description')),
            'image': None, 'image_src': imgs[0]['src'] if imgs else None,
        }
        if imgs:
            try:
                rec['image'] = save_image(imgs[0]['src'], f"images/{p['id']}", manifest)
            except Exception as e:
                print('image fail', p['id'], e)
        products.append(rec)

    logo = None
    try:
        for i, url in enumerate(find_logo()):
            try:
                f = save_image(url, 'logo' if i == 0 else f'logo_alt{i}', manifest)
                logo = logo or f
            except Exception as e:
                print('logo fail', url, e)
    except Exception as e:
        print('logo page fail', e)

    json.dump({'synced': today, 'source': API, 'logo': logo, 'count': len(products), 'products': products},
              open(os.path.join(DATA, 'products.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(manifest, open(mpath, 'w'), indent=1)
    os.makedirs(os.path.join(DATA, 'prices'), exist_ok=True)
    with open(os.path.join(DATA, 'prices', f'{today}.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', 'name', 'price', 'regular_price', 'on_sale', 'in_stock'])
        for r in products:
            w.writerow([r['id'], r['name'], r['price'], r['regular_price'], int(r['on_sale']), int(r['in_stock'])])
    print(f'OK {len(products)} produse, {sum(1 for r in products if r["on_sale"])} la promoție, logo={logo}')


if __name__ == '__main__':
    sys.exit(main())
