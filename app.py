from flask import Flask, render_template, request, redirect, Response
import requests
import os
import time

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

RAPIDAPI_KEY = "f30b4baaecmsh7d04f39e3f19019p15339bjsnad800cd8c0d2"
RAPIDAPI_HOST = "instagram-downloader-scraper-reels-igtv-posts-stories.p.rapidapi.com"

def clean_instagram_link(link):
    if "/reel/" in link:
        video_id = link.split("/reel/")[1].split("/")[0].split("?")[0]
        return f"https://www.instagram.com/reel/{video_id}/"
    elif "/p/" in link:
        video_id = link.split("/p/")[1].split("/")[0].split("?")[0]
        return f"https://www.instagram.com/p/{video_id}/"
    return link.split("?")[0]

def get_insta_data(link):
    clean_link = clean_instagram_link(link)
    print(f"Fetching: {clean_link}")
    try:
        r = requests.get(
            f"https://{RAPIDAPI_HOST}/scraper",
            params={"url": clean_link},
            headers={
                "x-rapidapi-key": RAPIDAPI_KEY,
                "x-rapidapi-host": RAPIDAPI_HOST
            },
            timeout=20
        )
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Response keys: {list(data.keys())}")

        # Struktur: {"data": [{"media": "https://...mp4..."}]}
        items = data.get("data", [])
        if isinstance(items, list) and len(items) > 0:
            item = items[0]
            video_url = item.get("media") or item.get("video_url") or item.get("url")
            cover_url = item.get("thumbnail") or item.get("thumbnail_url") or "https://placehold.co/400x600?text=Ready+to+Download"
            if video_url:
                print(f"Berhasil! URL: {video_url[:80]}")
                return {"video": video_url, "cover": cover_url}

        print(f"video_url tidak ditemukan. Data: {data}")

    except Exception as e:
        print(f"Error: {e}")

    return None

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    if request.method == "POST":
        input_link = request.form.get("url")
        if not input_link or "instagram.com" not in input_link:
            error = "Mohon masukkan link Instagram yang valid."
        else:
            result = get_insta_data(input_link)
            if not result:
                error = "Gagal mengambil video. Link mungkin salah atau akun diprivat."
    return render_template("index.html", result=result, error=error)

@app.route("/download")
def download():
    video_url = request.args.get("url")
    if not video_url:
        return "URL tidak valid", 400
    try:
        r = requests.get(
            video_url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.instagram.com/"},
            stream=True,
            timeout=30
        )
        filename = f"InstaSave_{int(time.time())}.mp4"
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(generate(), headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "video/mp4",
        })
    except Exception as e:
        print(f"Download error: {e}")
        return redirect(video_url)

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True)
