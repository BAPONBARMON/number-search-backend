Number Search - Lightweight Flask backend (requests + BeautifulSoup)
==================================================================

What this is:
- A small Flask API that performs best-effort public lookups for a phone number using DuckDuckGo HTML searches and direct page fetches.
- It returns a JSON with platforms, candidate name (if found heuristically), and an optional photo URL (if found in page metadata).

Limitations:
- Sites that require JavaScript (Facebook, Instagram, Truecaller dynamic pages) may not reveal usable data via simple requests. For robust scraping, use Playwright/Puppeteer (requires Docker + extra setup).
- Use responsibly and legally. Don't harass or publish private data.

Files included:
- app.py
- requirements.txt

Quick local test (recommended):
1. Create a Python 3.10+ virtualenv:
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
2. Install deps:
   pip install -r requirements.txt
3. Run app:
   python app.py
4. Test endpoints:
   http://localhost:3000/health
   http://localhost:3000/search?number=919876543210

Deploy to Render (straightforward):
1. Create a new GitHub repo (name: number-search-backend) and push these files.
2. On Render.com: New -> Web Service -> Connect GitHub -> choose the repo.
   - Environment: Python 3
   - Start Command: gunicorn app:app
3. Deploy. After deploy you'll get a public URL like https://your-service.onrender.com
4. Use that URL in your frontend (replace API_URL).

If you want a more powerful scraper (Playwright/Puppeteer), I can provide a Dockerfile+script for Render that runs headless Chromium. That is recommended for dynamic sites but requires a larger image and extra libs.