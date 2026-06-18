from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import os
import re
import requests
import yt_dlp


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
        format_id = query.get("format_id", [""])[0]

        if not url or not format_id:
            self._send_text(400, "Parâmetros inválidos.")
            return

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "format": format_id,
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
            "cookiefile": _cookiefile(),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self._send_text(500, f"Falha ao processar o vídeo: {e}")
            return

        direct_url = info.get("url")
        ext = info.get("ext", "mp4")
        title = re.sub(r"[^\w\s-]", "", info.get("title", "video")).strip() or "video"

        if not direct_url:
            self._send_text(500, "URL de download não encontrada.")
            return

        try:
            upstream = requests.get(direct_url, stream=True, timeout=20)
        except Exception:
            self._send_text(502, "Falha ao conectar ao servidor de vídeo.")
            return

        self.send_response(200)
        self.send_header(
            "Content-Type", upstream.headers.get("Content-Type", "application/octet-stream")
        )
        self.send_header("Content-Disposition", f'attachment; filename="{title}.{ext}"')
        content_length = upstream.headers.get("Content-Length")
        if content_length:
            self.send_header("Content-Length", content_length)
        self.end_headers()

        try:
            for chunk in upstream.iter_content(chunk_size=262144):
                if chunk:
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_text(self, status, message):
        body = message.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
