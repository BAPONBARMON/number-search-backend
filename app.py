
#!/usr/bin/env python3
\"\"\"Number Search (Flask backend - lightweight)
This app performs best-effort, server-side lookups for a phone number using public search pages
(DuckDuckGo HTML, simple site searches, direct page fetches).

Important limitations:
- This is NOT a guaranteed "name finder" for every platform (Facebook/Instagram/Truecaller are often JS-heavy and block scraping).
- For dynamic sites or pages requiring JS, a headless browser (Playwright/Selenium) is required. This app uses requests+bs4 only (lightweight, free).
- Use responsibly and legally.
\"\"\"

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
}

NAME_RE = re.compile(r'([A-Z][a-z]{2,}(?:\\s[A-Z][a-z]{2,}){0,3})')

def normalize_number(raw: str) -> str:
    if not raw: return ''
    digits = re.sub(r'\\D', '', raw)
    if len(digits) == 10:
        digits = '91' + digits
    return digits

def ddg_search_html(query: str, timeout=12):
    \"\"\"Use DuckDuckGo's lightweight HTML endpoint to get search results (POST).
       Returns list of dicts: {title, href, snippet}\"\"\"
    url = 'https://html.duckduckgo.com/html/'
    try:
        resp = requests.post(url, data={'q': query}, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        return {'error': f'duckduckgo search failed: {e}'}
    soup = BeautifulSoup(resp.text, 'html.parser')
    results = []
    # DuckDuckGo HTML has <a class="result__a"> links, but fallback to simple <a>
    for a in soup.find_all('a'):
        href = a.get('href')
        title = a.get_text(separator=' ', strip=True)
        if not href or not title: 
            continue
        # attempt to find a nearby snippet (parent)
        snippet = ''
        parent = a.find_parent()
        if parent:
            s = parent.get_text(separator=' ', strip=True)
            snippet = s.replace(title, '').strip()[:300]
        results.append({'title': title, 'href': href, 'snippet': snippet})
        if len(results) >= 8:
            break
    return results

def fetch_meta_image_and_title(url: str, timeout=10):
    \"\"\"Fetch a page and return og:title/og:image or first meaningful image and any text snippet.\"\"\"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        return {'error': f'fetch failed: {e}'}
    soup = BeautifulSoup(resp.text, 'html.parser')
    og_title = None
    og_image = None
    t = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name':'title'})
    if t:
        og_title = t.get('content') or t.get('value') or None
    img = soup.find('meta', property='og:image') or soup.find('img')
    if img:
        og_image = img.get('content') or img.get('src') or None
    # text snippet
    text = soup.get_text(separator=' ', strip=True')[:800]
    return {'title': og_title, 'image': og_image, 'text': text}

def extract_name_from_text(text: str):
    if not text: return None
    m = NAME_RE.search(text)
    return m.group(1) if m else None

@app.route('/health')
def health():
    return jsonify({'ok': True, 'note': 'lightweight number search (requests+bs4)'}), 200

@app.route('/search')
def search():
    raw = request.args.get('number') or ''
    if not raw:
        return jsonify({'error': 'missing number parameter, e.g. /search?number=919876543210'}), 400
    number = normalize_number(raw)
    if not number:
        return jsonify({'error': 'invalid number'}), 400

    # platforms to try (best-effort)
    platforms = [
        {'platform': 'DuckDuckGo (exact)', 'type': 'ddg', 'query': f'\"{number}\"'},
        {'platform': 'PhonePe (DDG)', 'type': 'ddg', 'query': f'\"{number}\" PhonePe'},
        {'platform': 'WhoCallsMe (site search)', 'type': 'ddg', 'query': f'site:whocallsme.com \"{number}\"'},
        {'platform': 'SpamCalls (site search)', 'type': 'ddg', 'query': f'site:spamcalls.net \"{number}\"'},
        {'platform': 'Truecaller (direct)', 'type': 'direct', 'url': f'https://www.truecaller.com/search/in/{number}'},
        {'platform': 'Google (DDG fallback)', 'type': 'ddg', 'query': f'\"{number}\" Google'},
    ]

    results = []
    for p in platforms:
        entry = {'platform': p['platform'], 'name': None, 'photo': None, 'notes': None}
        try:
            if p['type'] == 'ddg':
                res = ddg_search_html(p['query'])
                if isinstance(res, dict) and 'error' in res:
                    entry['notes'] = res['error']
                else:
                    # scan snippets for name-like text and attempt to fetch top result image
                    found = False
                    for r in res:
                        text = (r.get('snippet') or '') + ' ' + (r.get('title') or '')
                        name = extract_name_from_text(text)
                        if name and not found:
                            entry['name'] = name
                            # attempt to fetch image from the result page
                            meta = fetch_meta_image_and_title(r['href'])
                            if isinstance(meta, dict) and meta.get('image'):
                                entry['photo'] = meta.get('image')
                            entry['notes'] = r.get('href')
                            found = True
                            break
                    if not found and res:
                        # fallback: use first result's href as source
                        entry['notes'] = res[0].get('href')
            elif p['type'] == 'direct':
                meta = fetch_meta_image_and_title(p['url'])
                if isinstance(meta, dict) and 'error' in meta:
                    entry['notes'] = meta['error']
                else:
                    entry['notes'] = p['url']
                    # try to extract name from meta.title or text
                    if meta.get('title'):
                        nm = extract_name_from_text(meta.get('title'))
                        if nm: entry['name'] = nm
                    if not entry['name'] and meta.get('text'):
                        nm = extract_name_from_text(meta.get('text'))
                        if nm: entry['name'] = nm
                    entry['photo'] = meta.get('image')
            # small sleep to be polite
            time.sleep(0.6)
        except Exception as e:
            entry['notes'] = f'error: {e}'
        results.append(entry)

    return jsonify({'queried': raw, 'normalized': number, 'results': results}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False)
