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


def _cookie_debug():
    raw = os.environ.get("YT_COOKIES")
    if not raw:
        return "YT_COOKIES não está definida no servidor"
    lines = [l for l in raw.splitlines() if l.strip() and not l.startswith("#")]
    tabbed = sum(1 for l in lines if "\t" in l)
    return f"YT_COOKIES presente ({len(raw)} chars, {len(lines)} linhas de cookie, {tabbed} com tabs)"


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
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
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
                    "detail": f"{e} | {_cookie_debug()}",
                },
            )
            return

        duration_s = info.get("duration") or 0
        duration = f"{int(duration_s // 60)}:{int(duration_s % 60):02d}"

        all_formats = info.get("formats", [])

        combined = [
            f
            for f in all_formats
            if f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none")
        ]
        combined.sort(key=lambda f: (f.get("ext") != "mp4", -(f.get("height") or 0)))

        formats = []
        seen_heights = set()
        for f in combined:
            h = f.get("height")
            if h in seen_heights:
                continue
            seen_heights.add(h)
            formats.append(
                {
                    "format_id": f["format_id"],
                    "qualityLabel": f"{h}p" if h else f.get("format_note", ""),
                    "container": f.get("ext"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                }
            )
            if len(formats) >= 6:
                break

        if not formats:
            # Vídeo sem formato combinado (comum em uploads recentes): oferece
            # vídeo sem áudio como alternativa, já que não há ffmpeg no servidor
            # para juntar os streams separados.
            video_only = [
                f
                for f in all_formats
                if f.get("vcodec") not in (None, "none") and f.get("acodec") in (None, "none")
            ]
            video_only.sort(key=lambda f: f.get("height") or 0, reverse=True)
            seen_heights = set()
            for f in video_only:
                h = f.get("height")
                if h in seen_heights:
                    continue
                seen_heights.add(h)
                formats.append(
                    {
                        "format_id": f["format_id"],
                        "qualityLabel": f"{h}p (sem áudio)" if h else f.get("format_note", ""),
                        "container": f.get("ext"),
                        "filesize": f.get("filesize") or f.get("filesize_approx"),
                    }
                )
                if len(formats) >= 4:
                    break

        audio_only = [
            f
            for f in all_formats
            if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none")
        ]
        audio_only.sort(key=lambda f: f.get("abr") or 0, reverse=True)
        if audio_only:
            f = audio_only[0]
            formats.append(
                {
                    "format_id": f["format_id"],
                    "audioBitrate": f.get("abr"),
                    "container": f.get("ext"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                }
            )

        self._send_json(
            200,
            {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": duration,
                "formats": formats,
            },
        )

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
