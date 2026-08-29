from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_file,
    send_from_directory,
)
from pytubefix import YouTube
import os
import re
import time
import unicodedata
import subprocess


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DOWNLOAD_FOLDER = "downloads"
MAX_FILE_SIZE_MB = 100

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def clean_old_files(folder: str, max_age_minutes: int = 10):
    now = time.time()
    max_age = max_age_minutes * 60

    for filename in os.listdir(folder):
        path = os.path.join(folder, filename)

        if os.path.isfile(path):
            age = now - os.path.getmtime(path)

            if age > max_age:
                try:
                    os.remove(path)
                except OSError:
                    pass


def is_valid_youtube_url(url: str) -> bool:
    pattern = re.compile(
        r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/"
        r"(watch\?v=|embed/|v/|.+\?v=)?([\w-]{11})([&?].*)?$"
    )
    return bool(pattern.match(url.strip()))


def sanitize_filename(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ASCII", "ignore").decode("ASCII")
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    return name.strip()[:100]


@app.get("/cgu")
def cgu():
    return send_from_directory("static", "cgu.html")


@app.get("/mentions-legales")
def mentions_legales():
    return send_from_directory("static", "ml.html")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/en")
def index_en():
    return render_template("en.html")


@app.get("/robots.txt")
def robots():
    return send_from_directory("static", "robots.txt")


@app.get("/sitemap.xml")
def sitemap():
    return send_from_directory("static", "sitemap.xml")


@app.get("/ads.txt")
def ads():
    return send_from_directory("static", "ads.txt")


@app.post("/convert")
def convert():
    clean_old_files(DOWNLOAD_FOLDER)

    url = request.form.get("youtube_url", "").strip()
    format_type = request.form.get("format", "mp3")

    if not is_valid_youtube_url(url):
        flash("L'URL n'est pas une URL YouTube valide.", "error")
        return redirect(url_for("index"))

    temp_file = None
    filepath = None

    try:
        yt = YouTube(
            url,
            client="WEB",
            use_po_token=True,
        )

        filename_base = sanitize_filename(yt.title) or "youtube_download"

        if format_type == "mp3":
            stream = (
                yt.streams
                .filter(only_audio=True)
                .order_by("abr")
                .desc()
                .first()
            )

            if stream is None:
                raise RuntimeError("Aucun flux audio disponible pour cette vidéo.")

            temp_file = stream.download(
                output_path=DOWNLOAD_FOLDER,
                filename=f"{filename_base}.webm",
            )

            filepath = os.path.join(
                DOWNLOAD_FOLDER,
                f"{filename_base}.mp3",
            )

            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_file,
                    filepath,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    "La conversion MP3 avec FFmpeg a échoué : "
                    + result.stderr[-500:]
                )

            os.remove(temp_file)
            temp_file = None

        elif format_type == "mp4":
            stream = yt.streams.get_highest_resolution()

            if stream is None:
                raise RuntimeError("Aucun flux vidéo disponible pour cette vidéo.")

            filepath = stream.download(
                output_path=DOWNLOAD_FOLDER,
                filename=f"{filename_base}.mp4",
            )

        else:
            raise RuntimeError("Format demandé invalide.")

        size_mb = os.path.getsize(filepath) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            os.remove(filepath)
            filepath = None
            flash(
                f"Fichier trop volumineux (maximum : {MAX_FILE_SIZE_MB} Mo).",
                "error",
            )
            return redirect(url_for("index"))

        response = send_file(filepath, as_attachment=True)

        @response.call_on_close
        def cleanup():
            for file_path in (temp_file, filepath):
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

        return response

    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

        flash(f"Erreur lors du téléchargement : {str(e)}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    clean_old_files(DOWNLOAD_FOLDER)
    app.run(debug=False)