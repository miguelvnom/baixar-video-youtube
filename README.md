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

## Deploy na Vercel

1. Suba este projeto para um repositório no GitHub.
2. Em https://vercel.com, clique em "Add New Project" e importe o repositório.
3. A Vercel detecta automaticamente que é um projeto Next.js — não precisa configurar nada.
4. Clique em "Deploy".

## Limitações conhecidas

- **IP bloqueado pelo YouTube**: o YouTube às vezes bloqueia/limita
  requisições vindas de IPs de datacenters (incluindo os da Vercel),
  retornando erro 429. Isso é uma limitação do lado do YouTube, não um bug
  do código.
- **Tempo de execução**: funções serverless da Vercel têm limite de duração
  (configurado aqui para 60s via `maxDuration`). Vídeos muito longos podem
  estourar esse limite no plano gratuito (Hobby).
- **Biblioteca `@distube/ytdl-core`**: depende do player interno do YouTube,
  que muda com frequência. Se o YouTube alterar algo, pode ser necessário
  atualizar a dependência (`npm update @distube/ytdl-core`).
