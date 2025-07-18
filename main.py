from flask import Flask, render_template, request, flash, redirect, url_for, send_file, send_from_directory
from pytubefix import YouTube
import os
import re
import unicodedata
import subprocess

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DOWNLOAD_FOLDER = "downloads"
MAX_FILE_SIZE_MB = 100
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

import time

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
                except Exception:
                    pass


def is_valid_youtube_url(url: str) -> bool:
    import re
    pattern = re.compile(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([\w-]{11})([&?].*)?$'
    )
    return bool(pattern.match(url.strip()))


@app.get('/cgu')
def cgu():
    return send_from_directory('static', 'cgu.html')

@app.get('/mentions-legales')
def mentions_legales():
    return send_from_directory('static', 'ml.html')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/en', methods=['GET'])
def index_en():
    return render_template('en.html')

@app.route("/robots.txt")
def robots():
    return send_from_directory("static", "robots.txt")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory("static", "sitemap.xml")

@app.route("/ads.txt")
def ads():
    return send_from_directory("static", "ads.txt")

def sanitize_filename(name: str) -> str:
    # Supprime les accents
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    # Supprime les caractères invalides Windows
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Limite à 100 caractères pour éviter les chemins trop longs
    return name.strip()[:100]

@app.route('/convert', methods=['POST'])
def convert():
    clean_old_files(DOWNLOAD_FOLDER)  # Nettoyage automatique
    url = request.form['youtube_url']
    format_type = request.form['format']

    if not is_valid_youtube_url(url):
        flash("L'URL n'est pas une URL Youtube valide", "error")
        return redirect(url_for("index"))

    flash("Téléchargement en cours...", "success")

    try:
        yt = YouTube(url)
        # filename_base = uuid.uuid4().hex
        filename_base = sanitize_filename(yt.title)
        filepath = None

        if format_type == 'mp3':
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            temp_file = stream.download(output_path=DOWNLOAD_FOLDER, filename=filename_base + ".webm")
            output_file = os.path.join(DOWNLOAD_FOLDER, filename_base + ".mp3")

            command = [
                'ffmpeg', '-i', temp_file,
                output_file
            ]
            subprocess.run(command)
            os.remove(temp_file)
            filepath = output_file


        else:  # mp4
            stream = yt.streams.get_highest_resolution()
            filepath = stream.download(output_path=DOWNLOAD_FOLDER, filename=filename_base + ".mp4")

        # Vérification de la taille
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            os.remove(filepath)
            flash(f"Fichier trop volumineux (> {MAX_FILE_SIZE_MB} Mo).", "error")
            return redirect(url_for("index"))

        response = send_file(filepath, as_attachment=True)

        @response.call_on_close
        def cleanup():
            try:
                os.remove(filepath)
            except Exception:
                pass

        return response

    except Exception as e:
        flash(f"Erreur lors du téléchargement : {str(e)}", "error")
        return redirect(url_for("index"))

if __name__ == '__main__':
    clean_old_files(DOWNLOAD_FOLDER)
    app.run(debug=False)
