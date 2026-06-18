# Baixar Vídeo do YouTube

Site simples em Next.js para baixar vídeos do YouTube, pronto para deploy na Vercel.

## Aviso legal

Use apenas para vídeos próprios, de domínio público, com licença Creative
Commons ou para os quais você tenha autorização. Baixar conteúdo protegido
por direitos autorais sem permissão pode violar os Termos de Serviço do
YouTube e a legislação de direitos autorais.

## Rodando localmente

```bash
npm install
npm run dev
```

Abra http://localhost:3000

> Observação: a busca de informações e o download (`/api/info.py` e
> `/api/download.py`) são funções serverless em Python e só funcionam de
> fato hospedadas na Vercel (ou via `vercel dev`). Rodando só com `next dev`
> apenas o frontend funciona.

## Deploy na Vercel

1. Suba este projeto para um repositório no GitHub.
2. Em https://vercel.com, clique em "Add New Project" e importe o repositório.
3. A Vercel detecta automaticamente o Next.js (frontend) e o Python (`/api`,
   via `requirements.txt`) — não precisa configurar nada manualmente.
4. Clique em "Deploy".

## Limitações conhecidas

- **IP bloqueado pelo YouTube**: o YouTube às vezes bloqueia/limita
  requisições vindas de IPs de datacenters (incluindo os da Vercel),
  retornando erro 429. Isso é uma limitação do lado do YouTube, não um bug
  do código.
- **Tempo de execução**: funções serverless da Vercel têm limite de duração
  (configurado em `vercel.json` via `maxDuration`). Vídeos muito longos
  podem estourar esse limite no plano gratuito (Hobby).
- **Biblioteca `yt-dlp`**: depende da lógica interna do player do YouTube,
  que muda com frequência. O projeto é atualizado com bastante frequência
  pela comunidade; se algo parar de funcionar, atualize a versão fixada em
  `requirements.txt`.
- **Qualidade limitada**: como não há `ffmpeg` para combinar áudio e vídeo
  separados, só são oferecidos formatos "progressivos" (áudio+vídeo já
  juntos), geralmente até 720p.
