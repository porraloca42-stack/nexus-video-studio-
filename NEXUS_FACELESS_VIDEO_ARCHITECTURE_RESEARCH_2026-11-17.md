# Pesquisa de arquitetura e custos de apps faceless — 17/11/2026

## Objetivo e decisão provisória

Revisar a arquitetura audiovisual do NEXUS à luz dos fluxos públicos de Revid.ai, Crayo, Pictory, InVideo, Fliki e VEED, priorizando qualidade profissional, coerência semântica e custo previsível.

**Decisão provisória:** suspender novas decisões de adoção do LTX-2.5 e não aumentar o uso do LTX-0.9.8 até concluir a comparação de rotas por cena. Não remover nem quebrar o worker atual. O LTX-0.9.8 permanece disponível como caminho legado, sem ser obrigatório para todas as cenas.

Esta pesquisa usa documentação pública dos fornecedores. Ela descreve capacidades e opções visíveis aos clientes, não revela o código interno, os custos marginais reais nem os contratos privados desses serviços. Portanto, não se deve afirmar que todos usam a mesma arquitetura por baixo dos panos.

## 1. O que os produtos comerciais expõem publicamente

### Revid.ai — referência mais detalhada para roteamento por cena

A documentação pública do Revid lista vários tipos de mídia que podem coexistir:
- Stock video.
- Moving AI images: imagens geradas com movimento de câmera.
- AI video: clipes totalmente gerados.
- Motion graphics: cenas gráficas animadas.
- Custom media: arquivos enviados pelo usuário.
- Static/gameplay: fundos estáticos ou gameplay.

A API permite controlar a densidade de visuais por minuto e a animação de imagens. A documentação lista modos como soft, dynamic, depth, overlay, parallax, multiplane, cinemagraph, dust, hook e eco. O mecanismo interno exato desses modos não é público; a lista confirma os controles oferecidos, não que cada modo use um algoritmo específico de depth map ou overlays transparentes.

O Revid informa aproximadamente um visual por quatro segundos. Seu guia recomenda usar imagens animadas ou níveis econômicos nas cenas comuns e reservar vídeo premium para uma ou duas cenas hero. A escolha do tipo de mídia é apresentada como a principal alavanca de aparência e custo.

Referências:
- https://www.revid.ai/llm/revid-ai-media-types-and-models.md
- https://www.revid.ai/llm/revid-ai-credit-costs.md
- https://www.revid.ai/blog/create-ai-videos
- https://www.revid.ai/docs/workflows/prompt-to-video

### Crayo — formatos de storytelling e edição de clipes

O produto documenta formatos de Reddit/story, mensagens falsas, vídeos com gameplay ou stock como fundo, narração por IA, legendas animadas e ferramentas de imagem. Seu editor oferece timeline multifaixa, zooms, transições, LUTs, speed ramps, keyframes de câmera, cutaways, efeitos e ducking de áudio.

A página de preços separa créditos de workflow, minutos de exportação, minutos de voz e quantidade de imagens IA. Um crédito de workflow corresponde a um vídeo gerado por IA em determinados workflows. Isso mostra que geração e exportação são contabilizadas separadamente; não revela o custo marginal real da infraestrutura da Crayo.

Referências:
- https://crayo.ai/pricing
- https://crayo.ai/features/video-editor
- https://crayo.ai/ios

### Pictory — stock footage como base e IA como complemento

O Pictory afirma combinar script segmentado em cenas, matching automático de visuais, biblioteca de mais de 18 milhões de clipes/imagens, Getty/Storyblocks, vozes, legendas e AI Studio para gerar ou substituir visuais específicos. O usuário pode editar cena, texto, visual e voz separadamente.

Isso é um modelo importante para custo: muitas cenas podem ser cobertas por mídia licenciada já existente, sem gerar um vídeo novo por cena.

Referências:
- https://pictory.ai/text-to-video
- https://pictory.ai/pricing/
- https://pictory.ai/academy/how-to-turn-script-into-video-pictory-ai

### InVideo — matching de stock e montagem automática

A documentação oficial descreve análise do script por cena, seleção de clipes em biblioteca de stock, narração, música e montagem em timeline. A empresa anuncia uma biblioteca de 16 milhões de itens ilustrativos. A edição manual de timeline é gratuita no editor; geração e assistência de IA consomem créditos, com custos variáveis por modelo.

Referências:
- https://info.invideo.io/ai-text-script-to-full-video
- https://invideo.io/pricing/
- https://help.invideo.io/en/articles/11528140-invideo-plans-and-credits-everything-you-need-to-know

### Fliki — escolha explícita entre stock, imagem e vídeo IA

O workflow Script-to-Video permite selecionar stock media ou AI images, escolher estilo de animação, e opcionalmente transformar imagens em clipes IA. O usuário define também a cobertura percentual de cenas que receberão vídeo IA. A plataforma oferece voz, legendas e editor de timeline.

A tabela pública de créditos distingue voz, imagem IA, vídeo IA, exportação e workflows. Portanto, o próprio produto diferencia o custo de gerar mídia do custo de montar/exportar.

Referências:
- https://fliki.ai/text-to-video
- https://fliki.ai/features/ai-video-generator
- https://fliki.ai/credits
- https://fliki.ai/pricing

### VEED — roteamento entre stock, modelos IA e edição

O VEED expõe geração a partir de texto, script ou imagem; seleção de stock ou mídia IA; múltiplos modelos de vídeo; voz, avatar, legendas e editor final. A documentação não revela o custo interno por vídeo nem a composição exata do backend.

Referência:
- https://www.veed.io/tools/ai-video

## 2. Padrão de produto que emerge da comparação

Os produtos não dependem de vídeo generativo em todas as cenas. O padrão visível é uma **mistura de tipos de mídia com seleção por cena**:

1. Stock video quando existe uma ação real e licenciada que representa a fala.
2. Imagem IA animada quando uma imagem forte, com movimento de câmera, é suficiente.
3. Motion graphics quando o assunto é abstrato, explicativo, textual ou quantitativo.
4. Imagem/vídeo do próprio usuário quando há material de marca ou personagem.
5. Vídeo IA completo quando a ação, o personagem ou a transformação precisam de movimento que stock e animação 2D não conseguem entregar.
6. Voz, legendas, música, efeitos, transições, cutaways e edição numa timeline única.
7. Prévia de custo e regeneração seletiva de uma cena, em vez de reconstruir o vídeo inteiro.

A regra “um visual a cada quatro segundos” é uma referência comercial documentada pelo Revid, não uma regra universal. Para 60 segundos, isso representa aproximadamente 15 unidades visuais. O diretor NEXUS deve poder variar densidade e duração de acordo com o ritmo da narração.

## 3. O que os preços públicos dizem — e o que não dizem

### Revid: créditos cobrados do cliente

A tabela pública do Revid registra:
- Imagem IA: 1, 4 ou 16 créditos por imagem, conforme nível.
- Vídeo IA: 15, 50 ou 100 créditos por cinco segundos em tiers comuns; modelos premium podem custar 250 ou 500 créditos por cinco segundos.
- Motion graphics: 2, 3 ou 5 créditos por segundo, com mínimo de 15 segundos.
- Voz: 10 créditos por 500 caracteres.
- Música IA: 20 créditos; efeitos sonoros: 1 crédito por efeito.

O Revid publicou também uma estimativa de 75 créditos para um vídeo de 60 segundos com imagens IA animadas. No plano Growth consultado, 2.000 créditos custam US$39/mês. A equivalência proporcional é cerca de US$1,46 em créditos do cliente para aquele vídeo. **Isso não é o custo interno do Revid**: é apenas o valor de créditos consumidos pelo usuário. A empresa não divulga o custo marginal de GPU, licenças, armazenamento, suporte ou margem.

Fontes:
- https://www.revid.ai/llm/revid-ai-credit-costs.md
- https://www.revid.ai/llm/revid-ai-pricing-plans.md
- https://www.revid.ai/blog/mastering-video-editing-comprehensive-tutorial-guide

### Conclusão sobre “US$0,02 por vídeo”

Não encontrei documentação pública que comprove que Revid, Crayo ou outro concorrente produza um vídeo completo de 60 segundos por menos de US$0,02 de custo marginal. As páginas públicas mostram preços/consumo de créditos ao cliente e opções de mídia, não o custo de infraestrutura do fornecedor.

O número de US$0,02 deve ser tratado como **meta experimental interna do NEXUS**, com escopo definido, não como fato sobre concorrentes.

## 4. Cloudflare Workers AI — estimativa para as imagens que o NEXUS já gera

O código NEXUS usa `@cf/black-forest-labs/flux-2-klein-4b`, atualmente solicitando imagens de 512×910. A tabela oficial consultada em 12/11/2026 informa US$0,000287 por tile de saída 512×512 e US$0,000059 por tile de entrada 512×512. O uso é contabilizado em Neurons; há alocação gratuita de 10.000 Neurons por dia e o excedente custa US$0,011 por 1.000 Neurons em Workers Paid.

Estimativa condicional, assumindo arredondamento para dois tiles de saída para 512×910:
- Uma imagem: 2 × US$0,000287 = aproximadamente US$0,000574.
- 14 imagens: aproximadamente US$0,00804.
- 15 imagens: aproximadamente US$0,00861.
- Uma referência de personagem pode acrescentar custo de imagem de referência e tiles de entrada.

O cálculo de tiles é uma estimativa baseada na unidade de preço publicada; precisa ser confrontado com o consumo real de Neurons no painel Cloudflare. A alocação gratuita diária depende do total de uso da conta e não é uma garantia de custo zero permanente.

**Importante:** 512×910 não é “ultra HD”. O pipeline atual aumenta essas imagens para 720×1280 na composição final. Upscaling para 720p ou 4K não recupera detalhes que não existiam na imagem de origem.

Fonte:
- https://developers.cloudflare.com/workers-ai/platform/pricing/

## 5. Modal — correções necessárias nas hipóteses do Gemini

A tabela atual da Modal informa:
- T4: US$0,000164 por segundo de GPU.
- L40S: US$0,000542 por segundo de GPU.
- CPU e memória são cobradas separadamente.
- O tempo de carregamento da aplicação e processamento é faturável.
- A janela padrão de ociosidade é 60 segundos, configurável.
- O parâmetro de timeout limita a execução; não é uma promessa de preço fixo.

Uma estimativa de US$0,005 em GPU T4 equivale a aproximadamente 30,5 segundos faturáveis de GPU, antes de CPU e memória. Se houver 60 segundos de GPU faturável, só a GPU custaria aproximadamente US$0,00984. Portanto, US$0,005 para uma cena de 2,5 segundos pode ser plausível apenas se o tempo total faturável de GPU (incluindo inicialização/carregamento e janela ociosa) ficar abaixo de cerca de 30,5 segundos. Isso **não foi medido** no NEXUS e a compatibilidade/performance do modelo atual em T4 não foi validada.

No NEXUS atual:
- O worker Modal usa L40S, não T4.
- O perfil LTX-0.9.8 usa 10 passos (7 + 3), 512×896, 24 fps.
- O cache de pesos fica em Volume Modal.
- A janela de scale-down está em 5 segundos.
- A função tem timeout de 45 minutos.
- O cliente envia todas as cenas em um único `run_batch`; o worker carrega o modelo uma vez e percorre todas as cenas.
- O limite de GPU configurado é US$0,42, com estimativa cumulativa baseada em carregamento, execução e scale-down.

Assim, não é correto afirmar que o NEXUS já anima apenas uma ou duas cenas, nem que cada cena recebe uma chamada independente. O custo retornado por cena no worker é cumulativo dentro do lote.

### Timeout de 60 segundos

O timeout de uma função Modal aplica-se ao input e ao startup, salvo configuração separada de `startup_timeout`. Um timeout de 60 segundos no `run_batch` atual seria um limite para o lote inteiro, não para cada cena individual. Ele pode interromper o lote, mas não apaga o custo de GPU já consumido antes da interrupção. É necessário desenhar e testar o limite em conjunto com o carregamento do modelo.

### Spend limit de US$30

A documentação atual da Modal distingue:
- Workspace budget: limite rígido de uso total no ciclo, antes dos créditos.
- Spend limit: limite rígido do valor líquido cobrado do bolso, depois dos créditos.

Logo, configurar **Spend limit = US$30 não significa “não cobrar o cartão”**: pode permitir até US$30 de cobrança líquida. Para uma proteção mais forte, a configuração a avaliar é Spend limit = US$0 e Workspace budget definido no teto total desejado. Se o Starter tiver US$30 de créditos de compute, um Workspace budget de US$30 limita o uso total coberto por esse teto, enquanto o spend limit zero bloqueia cobrança líquida adicional. O estado atual do painel/conta do usuário não foi inspecionado.

Fontes:
- https://modal.com/pricing
- https://modal.com/docs/sdk/py/latest/App
- https://modal.com/docs/guide/budgets

## 6. Auditoria do NEXUS atual

Arquivos examinados na branch `main`, HEAD `b676cab62827089201dd1312d41f31bdb73f21fc`:

| Camada | Estado observado |
|---|---|
| Diretor/storyboard | Gemini gera cenas e prompts de imagem/movimento |
| Narração | Fish Audio |
| Keyframes | Cloudflare FLUX.2 Klein 4B, 512×910 |
| Animação atual | LTX-0.9.8 em Modal L40S para todas as cenas |
| Composição | Remotion, saída 720×1280, 30 fps |
| Auditoria | análise técnica de movimento e auditoria multimodal já existentes |
| Roteamento de mídia por cena | não implementado no worker: todas as cenas seguem para LTX |
| Parallax real com mapa de profundidade | não implementado |
| Overlays de vídeo transparentes em loop | não implementados |
| Sound design com SFX por beat | não implementado no componente Remotion examinado |
| Legendas dinâmicas word-level | não implementadas no componente Remotion examinado |

### Diferença entre o que existe e o que foi sugerido

O Remotion já executa zoom/pan/tilt 2D, transições, alguns efeitos CSS de partículas/chuva/neblina, flicker e light sweep. Há metadados `depthLayers` no manifesto e na tipagem, mas a composição atual não calcula mapa de profundidade nem separa primeiro plano, sujeito e fundo. Os efeitos de partículas atuais são elementos CSS, não vídeos de overlay reais.

Os “beats” usados pelo componente são eventos temporais do storyboard, não uma análise de batida da faixa de áudio. Não se deve chamar isso de sincronização musical real.

Arquivos:
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/nexus/cloudflare_images.py
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/nexus/modal_i2v.py
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/modal_worker.py
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/nexus/ltx_config.py
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/nexus/remote_render_job.py
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/remotion/src/NexusVideo.tsx
- https://github.com/porraloca42-stack/nexus-video-studio-/blob/main/nexus/remotion_renderer.py

## 7. Arquitetura recomendada para o NEXUS

Adotar um motor híbrido, com decisão de mídia por cena, em vez de escolher um único motor para o vídeo inteiro.

### Roteamento por cena

1. **Stock video licenciado:** primeira opção quando representa a ação concreta narrada. Pesquisar várias bibliotecas, pontuar relevância e validar licença, orientação, resolução e duração.
2. **Imagem IA animada:** usar quando a cena pede uma composição específica, personagem recorrente ou metáfora visual. Aplicar movimento de câmera com parcimônia.
3. **Parallax 2.5D:** usar apenas em imagens com separação de planos confiável. Gerar mapa de profundidade ou máscaras, criar camadas e animar com limites para evitar halos e regiões vazias. Não chamar isso de 3D verdadeiro; é uma ilusão 2.5D derivada de uma imagem.
4. **Overlays e atmosfera:** biblioteca licenciada de partículas, fumaça, poeira, chuva, flare e luz, com formatos que preservem alpha quando necessário. Misturar com blend modes apenas quando fizer sentido para a cena. Não aplicar poeira dourada/cósmica indiscriminadamente.
5. **Motion graphics:** usar para conceitos, números, etapas, relações, palavras-chave e mudanças de estado. Não substituir cenas concretas por gráficos genéricos.
6. **Vídeo IA:** reservar para hook, ação central ou cena hero em que o movimento seja essencial e não possa ser obtido por stock ou composição. Limite inicial proposto: 0–2 cenas por vídeo, decidido pelo diretor; não é uma regra rígida de todos os vídeos.

### Composição

Remotion deve montar uma timeline real:
- trilhas separadas para base visual, overlays, texto/legendas, narração, música e SFX;
- movimentos de câmera com easing e limites por cena;
- transições motivadas pelo conteúdo;
- ducking de música sob a fala;
- SFX pontuais e sincronizados com eventos, sem exagero;
- legendas temporizadas por palavra/frase, com estilos legíveis;
- saída inicial 1080×1920, 30 fps, sujeita a benchmark de qualidade/tempo. 60 fps só quando o movimento justificar o custo e o arquivo final ganhar algo perceptível.

### Inteligência editorial

O diretor deve classificar cada beat da narração por:
- ação física observável;
- metáfora visual;
- imagem atmosférica;
- explicação gráfica;
- evidência/objeto específico;
- necessidade de continuidade de personagem.

Depois escolhe a mídia mais barata que atenda à intenção visual, em vez de gerar vídeo por padrão.

## 8. Contabilidade e guardrails obrigatórios

Antes de qualquer geração paga, o NEXUS deve apresentar estimativa por cena e total:
- quantidade de imagens e custo/Neurons Cloudflare;
- duração e modelo de cada clipe IA;
- GPU-seconds medidos, carregamento, startup, CPU, memória e scale-down Modal;
- chamadas Gemini e tokens;
- caracteres/minutos Fish Audio;
- minutos GitHub Actions, armazenamento, tráfego e retries;
- margem de contingência.

O worker deve:
- receber um orçamento total explícito;
- reservar custo de startup antes de iniciar;
- bloquear novas cenas quando o saldo estimado não cobrir a próxima;
- registrar custo por cena e custo total;
- evitar retry automático caro;
- produzir relatório que permita comparar estimativa e cobrança real.

Não tratar timeout como teto de custo. Usar orçamento rígido da Modal e limites por trabalho. Validar as configurações do painel antes de ativar GPU.

## 9. Plano de validação sem custos variáveis

### Fase A — sem GPU e sem API paga
- Criar o roteador de mídia por cena e testes unitários com respostas simuladas.
- Adicionar no Remotion suporte a camadas de overlay locais, blend modes, animações de câmera e SFX.
- Implementar parallax 2.5D com mapas/máscaras de teste locais, sem inferência remota.
- Criar manifestos sintéticos e renders de teste com imagens/áudios locais de licença segura.
- Fazer teste de render, sincronismo, codec, resolução e duração.
- Criar relatório de custos estimados e guardrails.

### Fase B — comparação visual controlada, mediante autorização de custos
Produzir o mesmo roteiro em três rotas:
1. Stock + edição Remotion.
2. FLUX stills + movimento Remotion (incluindo parallax/overlays seletivos).
3. Híbrido com no máximo uma ou duas cenas LTX.

Comparar:
- coerência semântica por cena;
- movimento percebido e artefatos;
- continuidade;
- retenção visual nos primeiros 3 segundos;
- legibilidade;
- duração/qualidade do áudio;
- custo real por vídeo;
- tempo total e taxa de falha.

### Fase C — decisão de motor
Só reavaliar LTX-2.5 após a rota híbrida passar pelos critérios de qualidade e custo. LTX-2.5 não deve ser o motor padrão apenas por ser mais novo.

## 10. Conclusão

A direção mais defensável para o NEXUS é **stock + imagens IA animadas + motion graphics + overlays seletivos + 0–2 clipes de vídeo IA quando necessários**. Isso corresponde às opções de mídia documentadas em produtos comerciais e elimina a premissa cara de animar todas as cenas por IA.

O custo de geração de imagens FLUX.2 Klein pode ficar abaixo de um centavo para 14–15 imagens em 512×910, dependendo do tile metering e da alocação diária gratuita. Isso não prova que o vídeo completo custe US$0,02: voz, LLM, GPU opcional, execução CPU, armazenamento, tráfego e retries também entram na conta.

**Nenhuma alteração de código de produção, geração paga, inferência GPU, deploy, download de pesos ou render real foi executado nesta pesquisa.** O objetivo desta etapa é corrigir a decisão arquitetural antes de investir mais.

## Fontes principais

- Revid media types: https://www.revid.ai/llm/revid-ai-media-types-and-models.md
- Revid credit costs: https://www.revid.ai/llm/revid-ai-credit-costs.md
- Revid workflow guide: https://www.revid.ai/blog/create-ai-videos
- Crayo pricing: https://crayo.ai/pricing
- Crayo editor: https://crayo.ai/features/video-editor
- Pictory script-to-video: https://pictory.ai/text-to-video
- Pictory pricing: https://pictory.ai/pricing/
- InVideo workflow: https://info.invideo.io/ai-text-script-to-full-video
- InVideo pricing: https://invideo.io/pricing/
- Fliki script-to-video: https://fliki.ai/text-to-video
- Fliki credit usage: https://fliki.ai/credits
- VEED AI video: https://www.veed.io/tools/ai-video
- Cloudflare Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Modal pricing: https://modal.com/pricing
- Modal timeout reference: https://modal.com/docs/sdk/py/latest/App
- Modal budgets: https://modal.com/docs/guide/budgets


## 11. Pipeline editorial em quatro cérebros — proposta aprovada pelo usuário (17/11/2026)

Esta seção incorpora uma proposta editorial fornecida pelo usuário. Ela deve ser tratada como **arquitetura-alvo do NEXUS**, inspirada em padrões de produto observáveis, e não como descrição comprovada do backend proprietário de Revid, Crayo, Pictory ou qualquer outro app. A separação em quatro cérebros é uma decisão de design para tornar o raciocínio auditável, testável e especializado. Os quatro estágios podem usar prompts/chamadas separados ou módulos encadeados sobre o mesmo modelo; não é obrigatório pagar por quatro modelos diferentes.

### Cérebro 1 — Estrategista de retenção (Hook & estrutura)

Antes de escrever cenas, recebe tema, objetivo, público e duração e deve:
1. Propor três hooks distintos: curiosidade, perda/oportunidade relevante (sem urgência falsa ou medo manipulativo) e quebra de padrão.
2. Avaliar força, clareza, especificidade, credibilidade e aderência ao tema.
3. Selecionar um hook e registrar por que venceu os outros.
4. Desenhar o arco narrativo: promessa inicial, desenvolvimento, tensão/curiosidade crescente, revelação/entrega e fechamento.
5. Projetar um final que possa conectar naturalmente ao início em loop, sem corte arbitrário nem retenção enganosa.

**Saída estruturada:** três candidatos, hook escolhido, justificativa, promessa narrativa, curva de tensão por trecho, payoff e proposta de ligação entre final e abertura.

### Cérebro 2 — Roteirista de micro-ritmo

Recebe o arco aprovado e o transforma em fala oral curta e editável:
- Preferir unidades de fala com cerca de 2,5–3,5 segundos, como heurística inicial, não como limite rígido.
- Eliminar enchimentos, redundâncias e frases que não avançam a ideia.
- Alternar frases curtas e pausas intencionais; evitar transformar tudo em metralhadora de palavras.
- Marcar palavras-chave, pausas, mudança emocional, pergunta, revelação e payoff.
- Preservar naturalidade, inteligibilidade e densidade compatível com a velocidade real de narração.
- Garantir a duração pretendida sem quebrar a lógica nem cortar explicações essenciais.

**Saída estruturada:** blocos de fala ordenados, texto exato, duração-alvo, intenção vocal, palavras de ênfase, pausas e função narrativa. A duração será recalibrada após gerar a voz e alinhar o áudio.

### Cérebro 3 — Diretor de fotografia (tradução visual metafórica)

Não deve ilustrar cada substantivo literalmente. Deve traduzir a intenção emocional e semântica da fala em imagens filmáveis, específicas e memoráveis. Uma fala sobre dinheiro, por exemplo, não obriga a mostrar cédulas; pode pedir uma metáfora visual coerente. A metáfora precisa comunicar a ideia — não ser apenas bonita e aleatória.

O diretor cria uma **bíblia visual por vídeo**, travando:
- paleta e contraste;
- linguagem de luz e atmosfera;
- família de lentes/linguagem de enquadramento;
- textura, grão e tratamento de cor;
- regras de composição e distância de câmera;
- continuidade de personagem/objetos quando necessária.

Consistência não significa repetir enquadramentos, sujeitos ou cenários. Cada cena deve variar ação, escala, composição e ambiente sem romper a identidade visual.

**Saída estruturada por beat:** intenção da fala, emoção dominante, metáfora, ação visível, sujeito/ambiente, enquadramento/lente, movimento de câmera, paleta/iluminação, continuidade e rota recomendada (stock, imagem IA animada, parallax 2.5D, overlay, motion graphics ou vídeo IA). O roteador híbrido por cena continua decidindo a técnica de produção.

### Cérebro 4 — Editor de ritmo e sincronização audiovisual

Só fecha a edição depois que a narração final existir:
1. Alinhar o texto efetivamente falado ao áudio e obter timestamps por palavra.
2. Selecionar palavras/expressões âncora, priorizando sílabas tônicas ou momentos de ênfase perceptiva quando detectáveis com confiança.
3. Posicionar cortes, transições, zooms e movimentos para reforçar a fala.
4. Aplicar whoosh, bass hit ou outros SFX discretos apenas quando houver evento visual/narrativo que os justifique.
5. Sincronizar legendas, ênfases tipográficas, música e ducking.
6. Verificar a continuidade entre último e primeiro beat quando houver loop intencional.

**Precisão técnica:** o repositório oficial do OpenAI Whisper oferece a opção word_timestamps para extrair tempos por palavra, mas documenta o recurso como experimental. Isso não equivale a alinhamento fonético perfeito nem identifica automaticamente a sílaba tônica. Para sincronizar no nível de sílaba/fonema, o NEXUS precisará avaliar um alinhador fonético/forced aligner e, se necessário, uma camada de prosódia/ênfase. Não prometer corte na sílaba exata usando apenas timestamps de palavra. Mesmo com alinhamento, o corte deve respeitar continuidade visual e inteligibilidade.

Referências técnicas:
- OpenAI Whisper — opção experimental word_timestamps: https://github.com/openai/whisper/blob/main/whisper/transcribe.py
- OpenAI Whisper — implementação de alinhamento de palavras: https://github.com/openai/whisper/blob/main/whisper/timing.py
- Discussão do projeto sobre limites de precisão dos timestamps: https://github.com/openai/whisper/discussions/1855

### Contrato entre os quatro cérebros

Fluxo: Tema + objetivo + duração → 1) três hooks, escolha, arco e loop → 2) micro-blocos, fala final e ênfases → 3) metáforas, bíblia visual e plano por beat → geração da narração final → 4) alinhamento temporal, cortes, SFX, movimento e legendas → roteador híbrido + Remotion → MP4 → auditoria.

O cérebro 3 pode planejar em paralelo à preparação da narração, mas o cérebro 4 depende do áudio final. Se a duração real da voz mudar, timestamps e montagem precisam ser recalculados.

### Regras de qualidade

- O hook deve criar interesse com promessa que o vídeo realmente entrega.
- A tensão não pode inventar fatos, explorar medo de forma enganosa ou adiar artificialmente uma resposta simples.
- A metáfora deve ser compreensível e conectada à ideia; beleza sem semântica não é qualidade.
- A bíblia visual garante unidade, não uniformidade repetitiva.
- Não cortar em toda palavra nem adicionar whoosh/bass em cada transição. Silêncio e ausência de efeito também fazem parte do ritmo.
- 2,5–3,5s por unidade é ponto de partida para teste, não regra universal.
- O loop deve ser continuidade intencional, não repetição forçada.
- Cada cérebro produz dados estruturados, justificativas e sinais de confiança; a auditoria aponta decisões frágeis antes do render.

### Estado de implementação

- **Aprovado como direção de produto/arquitetura:** sim, pelo usuário em 17/11/2026.
- **Implementado no código:** não.
- **Testado com roteiro/áudio real:** não.
- **Validado por retenção ou comparação A/B:** não.
- **Custo variável nesta etapa:** US$0; nenhuma API paga, GPU, render de produção ou download de modelo foi acionado.

### Ordem recomendada de implementação sem custo variável

1. Definir schemas JSON e testes determinísticos para os quatro artefatos.
2. Separar hooks/arco da escrita de cenas, preservando o diretor atual até a nova cadeia passar nos testes.
3. Adicionar micro-blocos e marcações editoriais sem impor duração rígida.
4. Adicionar bíblia visual e tradução metafórica por beat, conectadas ao roteador híbrido.
5. Criar alinhamento temporal com áudio sintético/local; comparar Whisper word timestamps com forced alignment antes de escolher dependência.
6. Fazer Remotion consumir cortes/ênfases/SFX como eventos de timeline e validar sincronismo em render local.
7. Só depois comparar qualidade e retenção com vídeos reais, mediante autorização explícita para qualquer custo variável.



## Implementação inicial dos contratos dos quatro cérebros — 17/11/2026
- Criado `nexus/editorial_pipeline.py`, módulo stdlib-only e sem efeitos externos, com contratos versionados e validadores independentes para: estrategista de retenção, roteirista de micro-ritmo, diretor de fotografia e editor de sincronização.
- Brain 1 valida três ângulos distintos de hook (curiosidade, perda/oportunidade e quebra de padrão), seleção, justificativa, promessa, payoff e arco.
- Brain 2 valida blocos de fala, duração-alvo (0,5–8s aceita para não transformar a heurística 2,5–3,5s em bloqueio rígido), função narrativa, intenção vocal, ênfases, pausas e reconstrução fiel de full_narration.
- Brain 3 valida bíblia visual e direção por beat, incluindo metáfora, ação observável, continuidade e rota de mídia híbrida.
- Brain 4 valida duração do áudio, alinhamento por palavra/fonema, timestamps ordenados, âncoras de edição, eventos de legenda e mixagem. Uma âncora fonêmica é rejeitada se o artefato declarar apenas alinhamento por palavra; isso evita prometer precisão que a ferramenta não forneceu.
- Validação cruzada: cada micro-bloco deve ter direção visual; âncoras devem apontar para blocos existentes; o hook selecionado deve aparecer na fala de abertura.
- Criado `tests/test_editorial_pipeline.py` com fixtures determinísticas e cobertura dos quatro contratos e das referências cruzadas.
- Commits: `76c0b57` (contratos), `f19748f` (testes iniciais), `fe586c0` (validação cruzada), `b2631cf` (testes cruzados).
- CI #908, run `44098118981`, no commit `f19748f`: 170 testes Python passaram; Remotion typecheck e Commons smoke passaram. A suíte desse run antecede os três testes de validação cruzada adicionados nos commits seguintes.
- CI #910, run `44098265445`, commit `b2631cf`: unit-tests e Remotion typecheck concluídos com sucesso; Commons live smoke ainda estava em andamento na última consulta. Resultado final do run ainda pendente.
- Estado: contratos e testes implementados no GitHub; ainda não integrados ao fluxo de geração Gemini nem ao Remotion; sem teste com áudio real, sem retenção A/B, sem deploy ou MP4 validado.
- Nenhuma API Gemini/Fish/Cloudflare, inferência Modal/GPU, download de modelo ou render de produção foi executado por esta etapa. Custo variável adicional US$0.
- Próxima etapa: pesquisar e especificar os artefatos reais de cada cérebro e integrar primeiro Brain 1 em modo shadow/dry-run, mantendo o storyboard atual como fonte de produção até comparar e aprovar resultados. Não introduzir chamadas adicionais de API nem custo variável sem autorização específica.

