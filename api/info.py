from http.server import BaseHTTPRequestHandler
import json
import os
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
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"

        try:
            data = json.loads(raw or b"{}")
        except Exception:
            data = {}

        url = (data.get("url") or "").strip()

        if not url or "youtu" not in url:
            self._send_json(400, {"error": "Link do YouTube inválido."})
            return

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
            "cookiefile": _cookiefile(),
            "ignore_no_formats_error": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self._send_json(
                500,
                {
                    "error": "Não foi possível obter informações deste vídeo. "
                    "Ele pode ser privado, restrito por idade ou indisponível.",
                    "detail": str(e),
                },
            )
            return

        duration_s = info.get("duration") or 0
        duration = f"{int(duration_s // 60)}:{int(duration_s % 60):02d}"

        self._send_json(
            200,
            {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": duration,
            },
        )

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
