# NEXUS VIDEO STUDIO

Aplicação Streamlit para transformar roteiros em vídeos verticais com storyboard dirigido por IA, busca de mídia, revisão visual multimodal, narração, legendas e exportação MP4.

## Publicação
- Aplicação Streamlit.
- Arquivo principal: `app.py`.

## Segredos
Configure apenas no gerenciador privado de segredos do Streamlit:
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (opcional; padrão `auto`)
- `PIXABAY_API_KEY` (chave gratuita da API de vídeo do Pixabay)
- `PEXELS_API_KEY` (chave da API de vídeo do Pexels, se já disponível)

O Wikimedia Commons não exige chave de API. O Coverr foi removido das fontes ativas porque a chave disponível na conta do projeto retorna `Invalid API_KEY` e a conta está no plano Demo; não será exigido upgrade pago.

Nunca coloque chaves no repositório nem as envie pelo chat.

## Bibliotecas automáticas gratuitas
1. **Pixabay** — API gratuita com chave `PIXABAY_API_KEY`; cache e limites da API devem ser respeitados.
2. **Pexels** — API gratuita com chave `PEXELS_API_KEY`; pesquisa orientada a vídeos verticais.
3. **Wikimedia Commons** — API pública sem chave; o adaptador aceita apenas CC0, domínio público e CC BY, guardando autor, fonte e licença.

O Coverr não é fonte ativa: a chave previamente testada retornou `Invalid API_KEY` no plano Demo. O NEXUS não exige upgrade pago.

## Bancos gratuitos complementares (curadoria manual)
- **Mixkit** — [coleção vertical](https://mixkit.co/free-vertical-videos/). Usar somente itens com **Free License**; itens Restricted não podem ser usados em conteúdo comercial. A licença gratuita permite projetos comerciais e não exige atribuição, mas os termos proíbem bots/scraping e downloads em massa.
- **ISO Republic** — [vídeos CC0](https://isorepublic.com/). Uso pessoal e comercial; sem atribuição obrigatória. Confirmar a licença do item.
- **Vecteezy** — [vídeos gratuitos](https://www.vecteezy.com/free-videos). A licença Free exige atribuição e impõe limites ao uso comercial e a projetos de vídeo; a API gratuita anuncia 500 downloads/mês, mas não inclui acesso aos metadados de recursos, portanto não serve como busca automática confiável para o NEXUS.
- **Vidsplay** — [biblioteca gratuita](https://www.vidsplay.com/). Exige crédito/link visível conforme os termos.
- **National Park Service** — [multimídia e B-roll](https://www.nps.gov/media/multimedia-search.htm). Útil para natureza e parques; verificar direitos/créditos por arquivo.

Esses sites complementam a descoberta e a curadoria humana. O NEXUS não faz scraping nem simula APIs: sem uma API pública que permita pesquisa e download automatizados, o site é apresentado como fonte manual, não como biblioteca automática do render. NASA não entra na seleção comercial automática porque parte do acervo pode conter material de terceiros e as diretrizes restringem usos promocionais/comerciais.

## Pipeline e critérios de seleção
- Gemini planeja cenas e cria consultas específicas para ação/conteúdo e estilo.
- O motor consulta as bibliotecas ativas e agrega candidatos, removendo URLs duplicadas.
- A conexão semântica com a narração é prioridade; estilo visual é secundário; qualidade técnica desempata.
- Gemini Vision avalia quadros reais dos candidatos antes da seleção.
- A produção é interrompida se alguma cena não tiver clipe aprovado; não gera MP4 incompleto.
- Edge TTS gera narração e legendas; FFmpeg monta e valida MP4 vertical, áudio, duração e integridade.

## Diagnóstico
O painel avançado testa busca, download e leitura do vídeo. O resultado precisa ser validado no Streamlit publicado e com uma geração real; testes unitários simulados não comprovam a disponibilidade externa das bibliotecas.

## Estado de validação — 16/11/2026
- **Código no GitHub:** alterações de seleção 9:16, revisão visual, bibliotecas gratuitas e Wikimedia Commons registradas na branch `main`.
- **CI principal:** run #291 aprovado; compilação e 54 testes automatizados passaram. O teste de render FFmpeg confirma MP4 vertical com áudio/legendas.
- **Remotion:** runs #26 e #31 aprovados. O adaptador Python gerou manifesto a partir de clipe + WAV + SRT; Remotion renderizou H.264/AAC 720×1280, duração 4,011s; FFprobe e upload do artefato passaram. Demo gráfica 50s também foi validada no run #26. Fonte sans-serif corrigida e inspecionada no artefato do run #29.
- **Wikimedia Commons ao vivo:** busca e download de um vídeo licenciado foram concluídos; FFprobe confirmou arquivo VP9 válido (1920×1080, 261,16 s, CC BY 3.0). Isso valida o fluxo técnico com o candidato testado, não a relevância editorial de todo resultado.
- **Ainda pendente:** configuração dos Secrets Cloudflare/GitHub, geração real de imagens Workers AI, execução do worker de produção com credenciais, confirmação do deploy Streamlit e inspeção de um MP4 final com imagens geradas.
- **Não declarar produção ponta a ponta validada** até concluir essas verificações no ambiente publicado.

## Modo experimental: imagens originais + Remotion
O NEXUS possui um modo opcional de produção com imagens originais por cena:
- Gemini inclui `image_prompt` em cada cena, com direção vertical 9:16 e estilo global.
- Cloudflare Workers AI gera imagens com `@cf/black-forest-labs/flux-2-klein-4b`, resolução nativa 512×910 e 4 passos fixos.
- Edge TTS gera a narração/legendas no worker; Remotion compõe movimento de câmera, texto, áudio e vídeo H.264 720×1280.
- GitHub Actions atua como worker isolado. O MP4 volta ao Streamlit pelo artefato da execução.
- FFmpeg continua como pipeline padrão/fallback; o novo modo só é ativado pelo seletor de motor visual.

### Secrets necessários para ativação
No GitHub → Settings → Secrets and variables → Actions:
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN` com permissão Account → Workers AI → Read.

No Streamlit → Manage app → Settings → Secrets:
- `GITHUB_ACTIONS_TOKEN`: fine-grained token do repositório com Actions Read/Write e Contents Read.
- `CLOUDFLARE_API_TOKEN`: o mesmo token Cloudflare, usado para gerar imagens no worker e derivar a chave de criptografia dos dados privados.

O conteúdo do storyboard é criptografado antes do workflow_dispatch; o MP4 e o relatório também são criptografados antes do upload. O artefato público contém somente arquivos cifrados. Não gravar tokens no repositório, código, logs ou mensagens.

### Custo, licença e limite de imagens
A franquia Workers AI Free é de 10.000 Neurons por dia, com reinício às 00:00 UTC. FLUX.2 Klein 4B custa 26,05 Neurons por tile de saída 512×512; uma imagem 512×910 usa aproximadamente dois tiles (52,1 Neurons), o que sugere cerca de 191 imagens/dia como teto teórico. O valor real pode variar por contabilização, falhas e uso de outros modelos. Não é uma cota garantida. A variante Klein 4B é Apache 2.0 e permite uso comercial; não confundir com Klein 9B ou FLUX.2 dev, que têm licenças não comerciais.
Fontes oficiais: [FLUX.2 Klein 4B no Cloudflare](https://developers.cloudflare.com/workers-ai/models/flux-2-klein-4b/), [preços Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/), [parâmetros multipart](https://developers.cloudflare.com/changelog/post/2026-01-15-flux-2-klein-4b-workers-ai/), [licença FLUX.2](https://github.com/black-forest-labs/flux2).

### Estado
- Implementado no GitHub: adaptador Cloudflare, prompts de imagem por cena, manifesto Remotion com movimento por cena, worker GitHub Actions, envio/recuperação de artefato e criptografia do conteúdo.
- CI: 53 testes passaram no run #271 (incluindo Cloudflare, Remotion, criptografia e regressão FFmpeg). O typecheck Remotion também passou.
- Pendente: concluir render integrado com clipe+áudio no GitHub Actions; configurar Secrets; realizar geração real no Workers AI; validar MP4 de produção no Streamlit.
- O novo modo não está validado em produção e não substituiu o motor FFmpeg.

