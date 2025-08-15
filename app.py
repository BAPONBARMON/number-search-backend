from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    number = request.json.get("number", "").strip()
    if not number:
        return jsonify({"error": "No number provided"}), 400

    results = []

    # Example: Google Search link
    google_url = f"https://www.google.com/search?q={number}"
    results.append({"platform": "Google Search", "result": google_url})

    # Example: Truecaller (web search page, no API)
    truecaller_url = f"https://www.truecaller.com/search/in/{number}"
    results.append({"platform": "Truecaller", "result": truecaller_url})

    # Example: Facebook Forgot Password
    fb_url = f"https://www.facebook.com/login/identify/?ctx=recover&c=%2F&number={number}"
    results.append({"platform": "Facebook Forgot", "result": fb_url})

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
