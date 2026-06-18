"use client";

import { useState } from "react";

function formatSize(bytes) {
  if (!bytes) return "";
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(1)} MB`;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [video, setVideo] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setVideo(null);

    if (!url.trim()) return;

    setLoading(true);
    try {
      const res = await fetch("/api/info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Não foi possível processar este link.");
      }

      setVideo(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>Baixar Vídeo do YouTube</h1>
      <p className="subtitle">
        Cole o link do vídeo abaixo e escolha a qualidade desejada.
      </p>

      <form className="form-row" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="https://www.youtube.com/watch?v=..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {video && (
        <div className="video-card">
          <img src={video.thumbnail} alt={video.title} />
          <div className="video-title">{video.title}</div>
          <div className="video-meta">Duração: {video.duration}</div>

          <div className="formats">
            {video.formats.map((f) => (
              <div className="format-row" key={f.format_id}>
                <span>
                  {f.qualityLabel || Math.round(f.audioBitrate || 0) + " kbps"} ·{" "}
                  {f.container}
                  {f.filesize ? ` · ${formatSize(f.filesize)}` : ""}
                </span>
                <a
                  href={`/api/download?url=${encodeURIComponent(
                    url
                  )}&format_id=${f.format_id}`}
                >
                  Baixar
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="disclaimer">
        Use esta ferramenta apenas para baixar vídeos próprios, de domínio
        público, com licença Creative Commons ou para os quais você tenha
        autorização. Baixar conteúdo protegido por direitos autorais sem
        permissão pode violar os Termos de Serviço do YouTube e a legislação
        de direitos autorais.
      </p>
    </div>
  );
}
