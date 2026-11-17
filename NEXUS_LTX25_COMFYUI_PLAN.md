# NEXUS — Plano isolado de protótipo ComfyUI + LTX-2.5

Data da pesquisa: 17/11/2026  
Status: pesquisa técnica e arquitetura propostas; **não implementado, não implantado e não executado em GPU**.

## 1. Objetivo

Avaliar LTX-2.5 como alternativa de maior qualidade ao worker atual LTX-Video 0.9.8 2B. A integração deve nascer como worker independente, mantendo o worker existente como fallback. Nenhuma inferência, benchmark ou implantação que possa gerar custo variável será iniciada sem autorização explícita.

## 2. Evidências oficiais consultadas

- Workflow oficial de referência: `LTX-2.5_T2V_I2V_Two_Stage_Distilled.json`, em `Lightricks/ComfyUI-LTXVideo/example_workflows/2.5/`.
- O workflow oficial usa o transformer distilled de 22B em BF16, aceita uma imagem inicial opcional e faz duas etapas: geração em resolução-base, upscale espacial latente 2× e refinamento curto de 3 passos.
- A documentação da família indica que o fluxo de duas etapas é o padrão recomendado quando o detalhe espacial importa; o single-stage é mais leve e adequado a prévias.
- O workflow oficial gera áudio e vídeo conjuntamente. O NEXUS, porém, usa Fish Audio como fonte de narração. A integração deve descartar qualquer áudio gerado pelo LTX na composição final; investigar se o decode/mux de áudio pode ser removido sem quebrar o grafo.
- O workflow exige contagem de frames no formato `1 + 8n`. O JSON consultado tem 24 fps, 121 frames e dimensões padrão 960×544 (paisagem). A adaptação NEXUS deve ser vertical, com dimensões múltiplas de 32, por exemplo 544×960, e contagem 49/73/97/121 frames para durações aproximadas de 2/3/4/5 segundos a 24 fps. A linha do tempo final deve continuar sendo controlada pelo Remotion.
- O fluxo oficial carrega transformer 22B, VAE de vídeo, VAE de áudio, encoder Gemma 4 12B, enhancer Gemma 4 E2B e upscaler latente. Como o Gemini já entrega prompts dirigidos no NEXUS, o enhancer extra deve ser desativado/removido quando tecnicamente seguro para reduzir carga e dependências.
- Requisitos publicados para LTX-2.5: GPU NVIDIA com pelo menos 32 GB VRAM, 32 GB RAM, 100 GB livres, CUDA 12.7+ e Python 3.12+. Configuração recomendada: A100 80 GB ou H100, 64 GB+ RAM e 200 GB+ SSD.
- A L40S atual do NEXUS tem 48 GB VRAM: supera o mínimo publicado, mas fica abaixo da recomendação. Isso não prova que o workflow 22B BF16 caiba com folga, nem que o tempo/custo seja aceitável.
- A API nativa do ComfyUI permite submeter workflows em `POST /prompt`, acompanhar por `/ws`, consultar `/history/{prompt_id}` e recuperar arquivos por `/view`. O grafo de produção precisa estar no formato API exportado; o JSON visual do workflow não deve ser enviado diretamente como se fosse o formato API.

Fontes oficiais:
- [LTX-2.5 ComfyUI workflows](https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/example_workflows/2.5/README.md)
- [Workflow I2V/T2V two-stage distilled](https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/example_workflows/2.5/LTX-2.5_T2V_I2V_Two_Stage_Distilled.json)
- [LTX system requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements/)
- [ComfyUI server HTTP/WebSocket routes](https://github.com/Comfy-Org/docs/blob/main/development/comfyui-server/comms_routes.mdx)

## 3. Arquitetura proposta — worker separado

1. Criar uma aplicação Modal independente, por exemplo `nexus-comfy-ltx25-i2v`; não alterar `nexus-video-i2v` nem o fluxo padrão atual.
2. Fixar versões/SHAs de ComfyUI e `ComfyUI-LTXVideo`; não usar `master` flutuante em produção.
3. Construir a imagem do worker com Python/CUDA compatíveis, ComfyUI, custom nodes e dependências explicitamente pinadas.
4. Manter os pesos num Modal Volume persistente. Verificar gating/licença e necessidade de `HF_TOKEN` sem expor segredos.
5. Iniciar ComfyUI como processo local dentro do container Modal, limitado a loopback; não expor a interface/porta publicamente.
6. Carregar um workflow em formato API exportado e versionado no repositório. Fazer patch somente dos inputs autorizados: prompt I2V, imagem, duração/frame count, fps, dimensões, seed e negative prompt.
7. Enviar keyframe por `POST /upload/image`; submeter o grafo por `POST /prompt`; acompanhar a execução via WebSocket ou polling de `/history/{prompt_id}`; baixar o resultado via `/view`.
8. Normalizar o MP4 com FFmpeg: H.264, dimensões verticais, fps definido, sem áudio LTX. Validar arquivo, codec, duração, frames e stream de vídeo antes de devolver bytes.
9. Retornar telemetria por cena: modelo/revisão, GPU, cold start, tempo de carregamento, tempo de fila, inferência, duração/frames, memória máxima, tempo total faturável estimado e custo GPU estimado.
10. Adicionar seleção por feature flag apenas para testes internos. O pipeline atual continua sendo o padrão e fallback.

## 4. Compatibilidade com o NEXUS

- Entrada: keyframe FLUX já aprovado + `video_motion_prompt` em inglês + duração de 2–5 segundos.
- Preservar a identidade do protagonista pela imagem inicial e pelo fluxo de referência já existente.
- Não repetir `image_prompt` no prompt de movimento; descrever somente a ação que ocorre após o primeiro quadro.
- Não acrescentar zoom/pan/shake sintético no Remotion sobre o clipe gerado.
- Fish Audio continua sendo a única narração oficial do vídeo. O áudio gerado pelo LTX não deve substituir, misturar ou duplicar a voz.
- A saída deve respeitar o contrato de clipe usado por `nexus/modal_i2v.py` ou por um adaptador paralelo compatível, sem acoplar o restante do pipeline ao ComfyUI.

## 5. Trabalho de código permitido sem GPU

- Criar adaptador HTTP ComfyUI com cliente mockável.
- Versionar o workflow API exportado e validar os IDs/tipos dos nós usados pelo patch.
- Criar testes de contrato para upload de imagem, submissão, prompt_id, polling, histórico, download, timeout, erro de validação e cancelamento.
- Criar testes para dimensões 9:16, frames 1+8n, duração 2–5s, seed, saída MP4 sem áudio e contrato de telemetria.
- Testar conversão/patch do workflow apenas com dados falsos; nenhum download de pesos, boot de ComfyUI ou chamada GPU.
- Fixar commits e hashes dos artefatos, documentar tamanhos dos modelos e dependências.

## 6. Portões de custo e validação

**Não autorizado nesta fase:** baixar pesos grandes, iniciar ComfyUI em GPU, deploy que provoque download de modelos, smoke test de inferência, benchmark, geração de clipes ou render completo.

Antes de qualquer execução paga, apresentar estimativa baseada em cold start + carregamento + inferência + scaledown + CPU/RAM/armazenamento. O teto desejado permanece US$0,50 por vídeo, com reserva de US$0,08 para CPU/memória/variação e orçamento operacional de GPU de US$0,42. A estimativa não é garantia de fatura.

Após autorização específica:
1. Executar apenas um clipe de 2–3s, com keyframe/prompt idênticos ao teste comparativo do LTX 0.9.8.
2. Capturar custo real, cold start, memória, tempo de inferência e estabilidade.
3. Avaliar movimento físico, progressão temporal, aderência à ação, identidade, anatomia, flicker e detalhes.
4. Comparar lado a lado com LTX 0.9.8.
5. Só considerar troca do worker se qualidade e custo forem melhores e repetíveis.

## 7. Decisões em aberto

- Se 48 GB L40S é suficiente para o workflow two-stage 22B BF16 sem OOM e sem offload excessivamente lento.
- Se é necessário A100 80 GB/H100, e se o custo pode caber no orçamento.
- Como exportar e fixar o workflow em formato API, incluindo subgraphs.
- Como remover o decode de áudio sem alterar a geração AV de forma inválida.
- Se o modelo e os pesos exigem aceite de licença ou token Hugging Face para download automatizado.
- Quais nós/custom nodes e versões mínimas são obrigatórios no workflow oficial consultado.

## 8. Estado

- Pesquisa documental: feita.
- Arquitetura proposta: documentada.
- Código ComfyUI no NEXUS: não implementado.
- Worker ComfyUI: não criado.
- Workflow API exportado e adaptado: não criado.
- Testes de contrato: não criados.
- Deploy: não feito.
- GPU/inferência/benchmark: não executados.
- Custo variável nesta pesquisa: US$0.


## 9. Base HTTP client — implementação sem GPU (17/11/2026)
- Criado `nexus/comfyui_client.py`: cliente HTTP mockável para upload de keyframe, submissão de workflow API, leitura de histórico, espera por conclusão, detecção de erro e download de arquivo.
- Criado `tests/test_comfyui_client.py`: testes com sessão HTTP falsa para upload, fila, node_errors, sucesso, erro de execução, timeout sem reenvio automático, extração/download de MP4 e validação de URL.
- O módulo não inicia ComfyUI, não baixa pesos, não usa Modal, não importa Torch e não faz chamadas de rede durante importação. Só opera se for instanciado e chamado por um futuro worker.
- Ainda não existe workflow API exportado, mapeamento de nós, worker Modal ComfyUI ou integração ao fluxo de produção. O cliente genérico não significa que o LTX-2.5 já esteja integrado.
- Estado: código e testes gravados na branch main; execução automatizada ainda não confirmada. Nenhuma inferência, GPU, download de pesos ou deploy foi realizado; custo variável adicional US$0.
