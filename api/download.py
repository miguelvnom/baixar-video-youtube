from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import glob
import os
import re
import shutil
import tempfile
import requests
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


def _base_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
        "cookiefile": _cookiefile(),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url = unquote(query.get("url", [""])[0])
        format_id = query.get("format_id", [""])[0]

        if not url or not format_id:
            self._send_text(400, "Parâmetros inválidos.")
            return

        info_opts = dict(_base_opts(), skip_download=True, ignore_no_formats_error=True)
        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self._send_text(500, f"Falha ao processar o vídeo: {e}")
            return

        title = re.sub(r"[^\w\s-]", "", info.get("title", "video")).strip() or "video"
        chosen = next(
            (f for f in info.get("formats", []) if f.get("format_id") == format_id), None
        )
        has_audio = bool(chosen and chosen.get("acodec") not in (None, "none"))

        if has_audio:
            self._proxy_direct(chosen, title)
        else:
            self._download_and_mux(url, format_id, title)

    def _proxy_direct(self, chosen, title):
        direct_url = chosen.get("url")
        ext = chosen.get("ext", "mp4")

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

    def _download_and_mux(self, url, format_id, title):
        tmpdir = tempfile.mkdtemp(dir="/tmp")
        try:
            outtmpl = os.path.join(tmpdir, "out.%(ext)s")
            dl_opts = dict(
                _base_opts(),
                format=f"{format_id}+bestaudio/best",
                merge_output_format="mp4",
                outtmpl=outtmpl,
                ffmpeg_location=get_ffmpeg_exe(),
            )
            try:
                with yt_dlp.YoutubeDL(dl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                self._send_text(500, f"Falha ao baixar e juntar o vídeo: {e}")
                return

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
