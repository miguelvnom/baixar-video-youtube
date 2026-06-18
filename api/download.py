from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import glob
import os
import re
import shutil
import tempfile
import yt_dlp
from imageio_ffmpeg import get_ffmpeg_exe


def _cookiefile():
    raw = os.environ.get("YT_COOKIES")
    if not raw:
        return None
    path = "/tmp/yt_cookies.txt"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw)
    return path


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url = unquote(query.get("url", [""])[0])

        if not url:
            self._send_text(400, "Parâmetros inválidos.")
            return

        tmpdir = tempfile.mkdtemp(dir="/tmp")
        try:
            outtmpl = os.path.join(tmpdir, "out.%(ext)s")
            dl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
                "cookiefile": _cookiefile(),
                "format": "bv*+ba/best",
                "merge_output_format": "mp4",
                "outtmpl": outtmpl,
                "ffmpeg_location": get_ffmpeg_exe(),
            }
            try:
                with yt_dlp.YoutubeDL(dl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            except Exception as e:
                self._send_text(500, f"Falha ao baixar o vídeo: {e}")
                return

            title = re.sub(r"[^\w\s-]", "", info.get("title", "video")).strip() or "video"

            matches = glob.glob(os.path.join(tmpdir, "out.*"))
            if not matches:
                self._send_text(500, "Não foi possível gerar o arquivo final.")
                return

            filepath = matches[0]
            ext = filepath.rsplit(".", 1)[-1]

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{title}.{ext}"')
            self.send_header("Content-Length", str(os.path.getsize(filepath)))
            self.end_headers()

            try:
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(262144)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _send_text(self, status, message):
        body = message.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
