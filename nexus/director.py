import base64
import json
import re
import time
import requests
from pathlib import Path

SYSTEM = """
Você é o DIRETOR E ROTEIRISTA AUDIOVISUAL do NEXUS VIDEO STUDIO.
Sua primeira obrigação é entregar um ROTEIRO NARRADO COMPLETO, priorizando qualidade editorial e coerência com o briefing. Em seguida, transforme esse roteiro em cenas filmáveis. A duração escolhida é uma referência editorial com margem superior de até 10 segundos, não um número para o qual se deve mutilar ou inflar o texto.

DURAÇÃO E TEXTO:
- O usuário escolhe uma duração de referência. O limite máximo permitido é essa duração + 10 segundos: 30s permite até 40s; 40s permite até 50s; 60s permite até 70s.
- Mire naturalmente a duração escolhida. Use a margem adicional somente quando o raciocínio, os exemplos e a conclusão realmente precisarem dela. Não prolongue um roteiro que já está completo.
- A qualidade, clareza, progressão e força da narração têm prioridade sobre atingir um segundo exato. Não corte uma ideia importante apenas para acertar o cronômetro.
- Para estimar a fala, considere aproximadamente 2,2 a 2,5 palavras por segundo, mas a duração definitiva será medida pela voz selecionada. Essa estimativa não é uma meta rígida.
- Se o usuário fornecer apenas um tema/ideia, desenvolva o roteiro completo com começo forte, progressão lógica e fechamento, sem enchimento.
- Se fornecer um roteiro completo, preserve sua mensagem e os pontos essenciais. Não resuma nem acrescente frases vazias para manipular duração.
- Distribua TODO o texto narrado entre as cenas. Cada cena precisa ter voiceover não vazio, em português brasileiro natural. A soma das falas deve formar o roteiro completo, sem lacunas, repetições ou frases soltas.
- Não tente resolver duração escrevendo menos cenas ou deixando cenas sem fala.

PROFISSIONALISMO EDITORIAL, RETENÇÃO E DESCOBERTA:
- Atue como roteirista profissional de vídeos curtos, estrategista de retenção e editor. Assunto/roteiro, estilo visual e duração do painel são o briefing completo.
- Defina público provável, intenção e transformação/ideia que o espectador deve levar. Não invente fatos, estatísticas, citações ou promessas.
- HOOK: os primeiros 1–3 segundos abrem com pergunta forte, contraste, afirmação específica, quebra de expectativa ou tensão ligada ao tema. Evite saudações, introduções, “você sabia?” genérico e promessas exageradas. O hook precisa estar na primeira fala.
- RETENÇÃO: construa progressão, não lista de frases. Use curiosidade aberta, perguntas que serão respondidas, contrastes, exemplos concretos, mudanças de perspectiva e transições naturais. Entregue valor e recompense a promessa do hook. Sem suspense artificial ou repetição para ocupar tempo.
- NARRAÇÃO: escreva para ser falada por narrador profissional. Frases claras, ritmo variado, vocabulário natural, imagens mentais, pontuação que favoreça entonação e transições suaves. Evite linguagem robótica, clichês e redundância.
- PONTUAÇÃO PARA INTERPRETAÇÃO VOCAL: escreva a pontuação como direção de interpretação para a voz TTS, não como decoração gramatical. Vírgulas marcam pequenas continuidades e respirações naturais; pontos encerram ideias e permitem queda de entonação; dois-pontos preparam explicação, revelação ou lista; travessões criam apartes, contraste ou mudança de pensamento; interrogações devem soar como perguntas reais; exclamações são raras e reservadas a ênfase genuína; reticências só quando houver hesitação ou suspense intencional, nunca para fabricar pausas longas.
- Varie o comprimento das frases para criar cadência humana: combine frases curtas de impacto com frases médias de explicação e frases mais longas quando a ideia exigir continuidade. Evite sequência monótona de frases do mesmo tamanho, fragmentos telegráficos e períodos excessivamente longos.
- Use conectivos falados e transições naturais quando ajudarem o raciocínio. Coloque a palavra de maior impacto no ponto de ênfase da frase; não dependa de MAIÚSCULAS, excesso de exclamações ou reticências para simular emoção.
- Leia mentalmente cada frase em voz alta. A pontuação precisa deixar clara a intenção: onde a voz continua, conclui, pergunta, contrasta, revela ou enfatiza. O texto deve soar como uma pessoa explicando algo a outra, não como texto escrito sendo lido.
- Preserve pontuação e segmentação expressiva em todas as etapas: divisão por cenas, revisão de duração, geração de full_narration e legendas. Nunca remova vírgulas, pontos, interrogações ou travessões que carreguem a intenção da fala. Não acrescente SSML ou marcações técnicas à narração, a menos que o sintetizador e o fluxo de produção suportem isso explicitamente.
- ESTRUTURA: hook → desenvolvimento com progressão e valor → virada/insight ou aplicação prática → fechamento que resolve a promessa. Adapte ao tema.
- CTA: inclua chamada curta, específica e coerente com a intenção, integrada à conclusão. Escolha entre comentar, salvar, compartilhar, seguir ou conhecer um recurso somente quando fizer sentido. Não empilhe pedidos nem invente produto, link, oferta ou benefício. O CTA deve estar na narração e identificado no campo cta.
- SEO SEMÂNTICO: identifique palavra-chave principal e termos secundários reais. Integre-os naturalmente na narração, sem repetição artificial, keyword stuffing ou desvio de sentido. Título, descrição e hashtags refletem o conteúdo efetivamente narrado. Título claro sem clickbait enganoso; descrição fiel; poucas hashtags específicas.
- Consistência: hook, promessa, desenvolvimento, CTA, título, descrição e palavras-chave contam a mesma história. Nunca sacrifique naturalidade ou credibilidade pelo SEO.

CENAS:
- Decida a quantidade a partir da duração e da progressão narrativa. Use pelo menos ceil(duração/5) cenas e prefira ceil(duração/4) ou mais: 50s normalmente 12–15 cenas; 40s 10–12; 60s 15–18.
- Cada cena representa uma unidade narrativa e uma ação concreta. As durações são estimativas: o sistema medirá a voz selecionada e distribuirá a duração real entre as cenas. Não sacrifique a narrativa para tentar fazer a soma matemática.
- Cada cena deve representar exatamente o trecho narrado com ação, objeto, pessoa, ambiente ou processo diretamente relacionado. Não use cenas genéricas só porque combinam com a emoção.
- Para image-to-video, gere também `video_motion_prompt` em inglês: uma única tomada contínua de 2–5 segundos, com 1–3 movimentos físicos concretos e observáveis, indicando quem/o que se move, direção e ritmo. Preserve a identidade, o rosto, a roupa, o cenário e a composição da imagem-base; não introduza novos sujeitos, objetos, cortes ou mudanças de cena. Evite instruções abstratas como "make it cinematic".
- Leia e compreenda o roteiro inteiro antes de planejar cenas. Identifique ideia central, progressão, afirmações, exemplos e emoção de cada trecho.
- Priorize ações filmáveis e específicas. Evite slideshows, colagens, infográficos escolares, imagens abstratas sem função e repetição de enquadramentos.
- Cada cena precisa de busca visual própria, derivada da ação, objeto, ambiente e significado EXATOS daquele trecho. Nunca reutilize conjunto fixo de palavras-chave nem force objetos que não estejam no roteiro. Buscas principal e alternativa devem ser distintas, concretas, em inglês. A consulta deve descrever o que a câmera verá literalmente (sujeito + ação + objeto/ambiente), nunca conceitos abstratos como sucesso, mudança, motivação ou medo isolados. Se a fala for abstrata, crie uma ação humana específica que demonstre a ideia, sem usar paisagens genéricas como substituto.
- Respeite rigorosamente o estilo visual selecionado. Traduza-o em fotografia, paleta, luz, textura, lente, movimento e atmosfera em TODAS as cenas. Inclua visual_style e style_search_terms.
- O estilo é uma GRAMÁTICA VISUAL, nunca um catálogo de temas ou cenas. Não deduza personagem, objeto, cenário, profissão, época ou ação a partir do nome do estilo.
- Não repita exemplos, motivos, metáforas, sujeitos ou composições como fórmulas. Não existe cena-padrão para nenhum estilo; referências conceituais descrevem possibilidades, não instruções de conteúdo.
- Para cada cena, determine primeiro a intenção semântica do trecho, a ação observável mais adequada e o contexto narrativo. Só então aplique a gramática visual do estilo escolhido.
- Planeje o vídeo como uma sequência completa: varie sujeitos, ambientes, distâncias, ações, composição e metáforas. Evite repetir o mesmo motivo visual ou protagonista sem justificativa narrativa.
- style_search_terms deve conter somente características formais do estilo (meio, fotografia, cor, luz, textura e linguagem visual), nunca impor objetos, pessoas ou cenários. A busca principal e a alternativa continuam sendo específicas ao conteúdo da cena.
- Toda cena deve ter pelo menos dois microeventos visuais.

DIREÇÃO CINEMATOGRÁFICA EXECUTÁVEL (scene_direction):
Para cada cena, entregue também um objeto scene_direction estruturado. Não use instruções vagas como "cinematic movement". Ele deve conter:
  "camera": {"move":"push_in|pull_out|pan_left|pan_right|tilt_up|tilt_down|static","intensity":0.0,"start_scale":1.0,"end_scale":1.0,"focus":"subject|foreground|background"},
  "depth_layers": {"foreground":"...","subject":"...","background":"...","parallax_strength":0.0},
  "lighting": {"mood":"...","key_direction":"...","change":"none|subtle_flicker|light_sweep|exposure_ramp"},
  "atmosphere": {"effect":"none|dust|rain|fog|embers|particles","intensity":0.0},
  "transition": {"in":"cut|crossfade|match_cut|fade","out":"cut|crossfade|match_cut|fade","duration_frames":0},
  "beats": [{"at":0.0,"event":"...","visual_target":"..."}]
Use intensity entre 0.65 e 0.95 para cenas com ação; start_scale entre 1.03 e 1.08 e end_scale entre 1.18 e 1.25, salvo quando pull_out justificar o inverso. Use pan/tilt de forma alternada entre cenas vizinhas; evite repetir o mesmo movimento em mais de duas cenas seguidas. No máximo 3 beats por cena, com at entre 0 e 1, e posicione-os em momentos que correspondam à fala. Cada motion_event deve descrever um microevento visual observável e específico, não adjetivos vagos. Só escolha efeitos coerentes com o que realmente aparece na cena. Em imagens únicas, descreva movimento de câmera, profundidade e atmosfera; não prometa animação realista de corpo/objeto sem camada separada ou vídeo-fonte. O Remotion usa os beats/motion_events para pulsos de câmera e acentos gráficos; isso não substitui image-to-video para movimento orgânico de personagens. Mantenha fallback seguro: push_in, dust leve ou none, cut.

Retorne somente JSON válido:
{
 "topic_interpretation":"...",
 "creative_thesis":"...",
 "hook":"...",
 "retention_strategy":"...",
 "cta":"...",
 "seo":{"primary_keyword":"...","secondary_keywords":["..."],"title":"...","description":"...","hashtags":["..."]},
 "style_lock":"...",
 "full_narration":"roteiro narrado integral em português brasileiro",
 "scenes":[
  {
   "duration_seconds":4,
   "purpose":"...",
   "voiceover":"trecho contínuo do roteiro integral",
   "visual_action":"ação específica e observável, em sequência",
   "image_prompt":"English image-generation prompt, concrete cinematic scene, 9:16 vertical composition, no text or typography, preserve the global visual style",
   "video_motion_prompt":"English image-to-video prompt for one continuous 2–5 second shot, with specific natural physical movement and camera motion, preserving the exact subject identity and scene",
   "visual_style":"estilo visual aplicado nesta cena",
   "style_search_terms":"English visual-style terms to append to the scene search",
   "semantic_reason":"relação direta entre a fala e a imagem",
   "setting":"...",
   "subjects":"...",
   "shot_type":"...",
   "camera_motion":"push_in, pull_out, pan_left, pan_right, tilt_up ou tilt_down",
   "motion_events":["microevento 1","microevento 2"],
   "scene_direction":{"camera":{"move":"push_in","intensity":0.82,"start_scale":1.04,"end_scale":1.22,"focus":"subject"},"depth_layers":{"foreground":"...","subject":"...","background":"...","parallax_strength":0.2},"lighting":{"mood":"...","key_direction":"...","change":"none"},"atmosphere":{"effect":"none","intensity":0.0},"transition":{"in":"cut","out":"cut","duration_frames":0},"beats":[{"at":0.35,"event":"...","visual_target":"..."}]},
   "asset_search_query":"English query with concrete subject and action",
   "fallback_search_query":"different concrete English query"
  }
 ]
}
"""

def _model_version(name):
    nums = re.findall(r"\d+", name.lower())
    return tuple(int(n) for n in nums[:3]) if nums else (0,)

def discover_models(api_key, requested="auto"):
    """Return compatible Gemini models in preference order for failover."""
    last_error = None
    response = None
    for attempt in range(3):
        try:
            response = requests.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key},
                timeout=45,
            )
            if response.status_code in (500, 502, 503, 504):
                last_error = f"HTTP {response.status_code}"
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(
                    "Não foi possível consultar os modelos disponíveis do Gemini após 3 tentativas. "
                    "O serviço pode estar temporariamente indisponível."
                ) from None
    if response is None or not response.ok:
        raise RuntimeError(
            "O catálogo de modelos do Gemini está indisponível"
            + (f" ({last_error})." if last_error else ".")
            + " Tente novamente em alguns minutos."
        )

    # This director sends systemInstruction and expects text/JSON. Some Gemini
    # models expose generateContent but are specialized for TTS/audio/image and
    # reject developer/system instructions. Never rank those for storyboard work.
    unsupported_modalities = (
        "-tts", "tts-", "native-audio", "-audio", "audio-",
        "-image", "image-", "embedding", "veo",
    )
    supported = []
    for model in response.json().get("models", []):
        name = model.get("name", "").split("/")[-1].lower()
        methods = model.get("supportedGenerationMethods", [])
        if "generateContent" not in methods:
            continue
        if any(token in name for token in unsupported_modalities):
            continue
        supported.append(model)
    if not supported:
        raise RuntimeError("A chave não retornou modelos compatíveis com geração de conteúdo.")

    requested = (requested or "auto").strip().replace("models/", "")
    selected = None
    if requested.lower() not in ("", "auto"):
        selected = next(
            (m for m in supported if m.get("name", "").split("/")[-1] == requested),
            None,
        )
        # A configured model may be stale or incompatible (for example a TTS
        # model). Never fall back to the API's arbitrary listing order.
        if selected:
            supported = [selected] + [m for m in supported if m is not selected]

    def rank(model):
        name = model.get("name", "").split("/")[-1].lower()
        stable = 1 if "preview" not in name and "exp" not in name else 0
        if "flash-lite" in name:
            family = 4
        elif "flash" in name:
            family = 3
        elif "pro" in name:
            family = 2
        else:
            family = 1
        return (stable, family, _model_version(name))

    if selected is None:
        # Auto mode, or configured model filtered out: choose best compatible
        # text model by capability ranking, not by API response order.
        supported.sort(key=rank, reverse=True)

    names = []
    for item in supported:
        name = item.get("name", "").split("/")[-1]
        if name and name not in names:
            names.append(name)
    return names


def discover_model(api_key, requested="auto"):
    """Backward-compatible single-model selector."""
    return discover_models(api_key, requested)[0]


def _request(prompt, secret_reader):
    key = secret_reader("GEMINI_API_KEY")
    requested = secret_reader("GEMINI_MODEL", "auto")
    if not key:
        raise RuntimeError("Diretor de IA indisponível: configure GEMINI_API_KEY.")

    models = discover_models(key, requested)
    # A transient outage on one model must not abort the user's planning request.
    # Try up to two times per model, then fail over to another compatible model.
    attempted = []
    last_status = None
    last_detail = ""

    for model in models[:5]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        request_prompt = prompt
        for attempt in range(2):
            payload = {
                "systemInstruction": {"parts": [{"text": SYSTEM}]},
                "contents": [{"role": "user", "parts": [{"text": request_prompt}]}],
                "generationConfig": {
                    "temperature": 0.2 if attempt else 0.25,
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 8192,
                },
            }
            try:
                response = requests.post(
                    url, params={"key": key}, json=payload, timeout=240
                )
            except requests.RequestException:
                if attempt == 0:
                    time.sleep(2)
                    continue
                last_status = "conexão"
                last_detail = f"{model}: falha de conexão após duas tentativas."
                break

            if response.status_code in (429, 500, 502, 503, 504):
                last_status = response.status_code
                try:
                    detail = response.json().get("error", {}).get("message", "")
                except (ValueError, AttributeError):
                    detail = ""
                last_detail = str(detail)[:500] or "Sem detalhe adicional informado pela API."
                attempted.append(f"{model} (HTTP {response.status_code})")
                if attempt == 0:
                    time.sleep(2)
                    continue
                # Try the next model instead of showing a fatal error immediately.
                break

            if response.status_code in (401, 403):
                raise RuntimeError(
                    "O Gemini recusou a autenticação ou o acesso à API. "
                    "Verifique GEMINI_API_KEY e as permissões do projeto."
                )
            if response.status_code == 400:
                try:
                    detail = response.json().get("error", {}).get("message", "")
                except (ValueError, AttributeError):
                    detail = ""
                if "developer instruction is not enabled" in str(detail).lower():
                    last_status = 400
                    last_detail = (
                        f"{model}: modelo incompatível com instruções do diretor. "
                        + str(detail)[:300]
                    )
                    attempted.append(f"{model} (incompatível com systemInstruction)")
                    break
                raise RuntimeError(
                    f"Falha no Gemini (HTTP 400) no modelo {model}. "
                    + (str(detail)[:500] if detail else "Requisição inválida.")
                )
            if response.status_code == 404:
                last_status = 404
                last_detail = f"O modelo {model} não está disponível."
                attempted.append(f"{model} (HTTP 404)")
                break
            if not response.ok:
                detail = ""
                try:
                    detail = response.json().get("error", {}).get("message", "")
                except (ValueError, AttributeError):
                    pass
                raise RuntimeError(
                    f"Falha no Gemini (HTTP {response.status_code}) no modelo {model}. "
                    + (str(detail)[:500] if detail else "")
                )

            data = response.json()
            candidates = data.get("candidates") or []
            if not candidates:
                feedback = data.get("promptFeedback", {}).get("blockReason")
                suffix = " (bloqueio: " + str(feedback) + ")." if feedback else "."
                raise RuntimeError(
                    "O Gemini não gerou o storyboard" + suffix
                    + " Revise o roteiro ou tente novamente."
                )

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "desconhecido")
            parts = candidate.get("content", {}).get("parts", [])
            result = "\n".join(
                part.get("text", "")
                for part in parts
                if isinstance(part, dict) and part.get("text")
            )
            if not result.strip():
                raise RuntimeError(
                    "O Gemini retornou uma resposta sem texto (motivo: "
                    + str(finish_reason) + "). Tente novamente."
                )

            cleaned = re.sub(
                r"^\s*```(?:json)?\s*|\s*```\s*$",
                "",
                result.strip(),
                flags=re.IGNORECASE,
            )
            try:
                plan = json.loads(cleaned)
            except json.JSONDecodeError:
                start_json = cleaned.find("{")
                if start_json >= 0:
                    try:
                        plan, _ = json.JSONDecoder().raw_decode(cleaned[start_json:])
                    except json.JSONDecodeError:
                        plan = None
                else:
                    plan = None

            if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list):
                # Gemini may stop with malformed JSON even when finishReason is
                # STOP. Retry once with a compact JSON-only instruction, then
                # fail over to another compatible model if needed.
                if attempt == 0:
                    request_prompt = (
                        prompt
                        + "\n\nRETRY OBRIGATÓRIO: a resposta anterior não formou JSON válido. "
                        "Gere novamente o objeto COMPLETO desde a primeira chave até a última. "
                        "Retorne apenas JSON, sem Markdown nem comentários. Preserve todos os "
                        "campos e todas as cenas, mas mantenha descrições concisas: purpose até "
                        "12 palavras; visual_action até 20; semantic_reason até 24; setting, "
                        "subjects, shot_type e camera_motion curtos; buscas em inglês com até "
                        "12 palavras cada; exatamente dois microeventos curtos por cena. "
                        "Não interrompa strings nem deixe vírgulas finais."
                    )
                    continue
                last_status = "invalid_json"
                last_detail = (
                    f"{model}: JSON inválido após duas tentativas "
                    f"(finishReason={finish_reason})."
                )
                attempted.append(f"{model} (JSON inválido)")
                break
            plan["director_model"] = model
            plan["model_failover"] = attempted
            return plan

    tried = ", ".join(attempted) if attempted else "nenhum modelo"
    if last_status == 503 or last_status in (500, 502, 504):
        raise RuntimeError(
            "O Gemini está temporariamente sobrecarregado ou indisponível. "
            f"Tentei novamente e recorri a outros modelos compatíveis ({tried}), "
            "mas nenhum respondeu. Aguarde um minuto e tente outra vez."
        )
    if last_status == 429:
        raise RuntimeError(
            "Os modelos Gemini disponíveis recusaram a solicitação por limite de uso/cota. "
            f"Modelos tentados: {tried}. Confira os limites no AI Studio: "
            "https://aistudio.google.com/rate-limit"
        )
    if last_status == 404:
        raise RuntimeError(
            "O modelo configurado não está disponível e os modelos alternativos também falharam. "
            f"Modelos tentados: {tried}. Configure GEMINI_MODEL = \"auto\" em Secrets."
        )
    if last_status == "invalid_json":
        raise RuntimeError(
            "O Gemini respondeu, mas não conseguiu entregar um JSON completo mesmo após "
            "uma nova tentativa automática e o teste de outros modelos compatíveis. "
            f"Modelos verificados: {tried}. Nenhum roteiro incompleto foi aceito. "
            "Tente novamente em instantes; a duração escolhida foi preservada."
        )
    raise RuntimeError(
        "Não foi possível obter resposta do Gemini após tentar modelos alternativos. "
        f"Último detalhe: {last_detail}"
    )

def _fit_scene_durations(scenes, measured_duration):
    """Allocate the measured narration runtime across scenes without changing the audio."""
    total = float(measured_duration)
    count = len(scenes)
    minimum_per_scene = 1.5
    maximum_per_scene = 5.0
    if not count or total < minimum_per_scene * count or total > maximum_per_scene * count:
        raise ValueError(
            f"A narração medida ({total:.1f}s) não cabe nas {count} cenas "
            f"com duração visual entre {minimum_per_scene:.1f}s e {maximum_per_scene:.1f}s. "
            "O planejamento precisa de uma segmentação diferente."
        )

    weights = [
        float(max(1, len(str(scene.get("voiceover", "")).split())))
        for scene in scenes
    ]
    durations = [minimum_per_scene] * count
    capacities = [maximum_per_scene - minimum_per_scene] * count
    remaining = total - minimum_per_scene * count

    while remaining > 1e-8:
        active = [i for i, capacity in enumerate(capacities) if capacity > 1e-8]
        if not active:
            raise ValueError("As cenas não comportam a duração medida da narração.")
        weight_sum = sum(weights[i] for i in active)
        shares = {i: remaining * weights[i] / weight_sum for i in active}
        saturated = [i for i in active if shares[i] >= capacities[i] - 1e-8]
        if saturated:
            for i in saturated:
                allocation = capacities[i]
                durations[i] += allocation
                remaining -= allocation
                capacities[i] = 0.0
        else:
            for i in active:
                durations[i] += shares[i]
                capacities[i] -= shares[i]
            remaining = 0.0

    for scene, seconds in zip(scenes, durations):
        scene["duration_seconds"] = round(seconds, 4)
    return [scene["duration_seconds"] for scene in scenes]

def _repair_semantic_justifications(plan, topic, style, target, secret_reader):
    """Repair weak scene-to-narration links without rewriting approved narration."""
    scenes = plan.get("scenes", [])
    weak = [
        index for index, scene in enumerate(scenes, 1)
        if len(str(scene.get("semantic_reason", "")).strip()) < 80
    ]
    if not weak:
        return

    selected = []
    for index in weak:
        scene = scenes[index - 1]
        selected.append({
            "scene_number": index,
            "voiceover": scene.get("voiceover", ""),
            "visual_action": scene.get("visual_action", ""),
            "setting": scene.get("setting", ""),
            "subjects": scene.get("subjects", ""),
            "semantic_reason": scene.get("semantic_reason", ""),
        })

    repair_prompt = f"""Você é editor de continuidade e coerência semântica audiovisual.
Reescreva SOMENTE as justificativas e, se necessário, a ação visual das cenas indicadas, explicando precisamente como a imagem materializa o trecho narrado.
Duração: {target}s. Tema original: {topic}. Estilo visual: {style}.
Direção de arte obrigatória: {build_visual_style_directive(style)}
Leia a fala de cada cena e descreva a relação concreta entre o que é dito e o que aparece. Não use frases vagas como "transmite a emoção", "representa a mensagem" ou "combina com o tema". Cite o objeto, gesto, pessoa, ambiente ou consequência visual que corresponde à fala.
Cada semantic_reason deve ter 80 a 160 caracteres e ser específica para aquela fala. Se a ação atual não corresponder à fala, substitua-a por uma ação filmável que corresponda.
Cenas para reparar:
{json.dumps(selected, ensure_ascii=False)}
Retorne somente JSON válido:
{{"scene_repairs":[{{"scene_number":1,"semantic_reason":"...","visual_action":"...","setting":"...","subjects":"..."}}]}}
Não altere narração, ordem das cenas, duração, estilo geral nem qualquer cena que não esteja na lista."""

    try:
        repaired = _request(repair_prompt, secret_reader)
        for item in repaired.get("scene_repairs", []):
            try:
                index = int(item.get("scene_number", 0)) - 1
            except (TypeError, ValueError):
                continue
            if index < 0 or index >= len(scenes) or index + 1 not in weak:
                continue
            scene = scenes[index]
            for field in ("semantic_reason", "visual_action", "setting", "subjects"):
                value = str(item.get(field, "") or "").strip()
                if value:
                    scene[field] = value
    except Exception:
        # Preserve original scene data; the grounded fallback below prevents
        # a short editorial explanation from aborting the whole storyboard.
        pass

    for index in weak:
        scene = scenes[index - 1]
        reason = str(scene.get("semantic_reason", "") or "").strip()
        if len(reason) >= 80:
            continue
        # Build only from this scene's own narration and visual fields.
        voice = str(scene.get("voiceover", "") or "").strip()
        action = str(scene.get("visual_action", "") or "").strip()
        setting = str(scene.get("setting", "") or "").strip()
        subjects = str(scene.get("subjects", "") or "").strip()
        scene["semantic_reason"] = (
            f'A fala "{voice}" é visualizada por meio de {action}. '
            f'{("No ambiente " + setting + ", ") if setting else ""}'
            f'{("a presença de " + subjects + " ") if subjects else ""}'
            "torna observável o ponto específico narrado, em vez de usar uma imagem genérica."
        )


from nexus.visual_styles import STYLE_SEARCH_TERMS, build_visual_style_directive

def apply_visual_style_lock(plan, style):
    """Enforce the selected global visual style on every scene, independent of LLM compliance."""
    plan["style_lock"] = style
    style_terms = STYLE_SEARCH_TERMS.get(style, f"{style}, consistent visual style")
    plan["style_profile_version"] = "2.0"
    plan["style_directive"] = build_visual_style_directive(style)
    for scene in plan.get("scenes", []):
        scene["visual_style"] = style
        # Keep any scene-specific formal treatment generated by the director,
        # then append only non-prescriptive style grammar. Never inject motifs.
        scene_terms = str(scene.get("style_search_terms") or "").strip()
        if style_terms and style_terms not in scene_terms:
            scene_terms = ", ".join(part for part in (scene_terms, style_terms) if part)
        scene["style_search_terms"] = scene_terms or style_terms
        # The image worker consumes image_prompt directly; carry the full internal
        # art direction into that exact prompt rather than relying only on metadata.
        image_marker = "\n\nNEXUS STYLE DIRECTION:"
        image_prompt = str(scene.get("image_prompt") or "").split(image_marker, 1)[0].rstrip()
        if image_prompt:
            scene["image_prompt"] = (
                image_prompt + image_marker + "\n" + plan["style_directive"]
            )
    return plan


def create_storyboard(topic, style, duration, secret_reader):
    target = int(round(float(duration)))
    maximum_duration = target + 10
    minimum_scenes = max(10, (maximum_duration + 4) // 5)
    preferred_scenes = max(minimum_scenes, (target + 3) // 4)
    min_words = int(round(target * 2.1))
    max_words = int(round(maximum_duration * 2.4))
    prompt = f"""PEDIDO/ROTEIRO DO USUÁRIO:
{topic}

DURAÇÃO DE REFERÊNCIA: {target} segundos. LIMITE MÁXIMO: {maximum_duration} segundos (margem editorial de até +10s).
ESTILO VISUAL: {style}
DIREÇÃO DE ARTE OBRIGATÓRIA (instruções internas; não mostrar ao usuário):
{build_visual_style_directive(style)}

REGRA DE LIBERDADE CRIATIVA:
O estilo define a gramática visual, não define o conteúdo da cena. Não use um personagem, objeto, cenário ou metáfora como resposta automática ao estilo. Não copie motivos de descrições ou referências como se fossem exemplos obrigatórios. Interprete cada trecho de forma independente, determine o que precisa ser comunicado e invente uma solução visual nova e específica. Ao longo do vídeo, monitore a variedade: não repita protagonista, gesto, objeto simbólico, ambiente ou composição sem necessidade narrativa. A mesma identidade estética deve comportar muitas soluções visuais diferentes.

Primeiro interprete o briefing completo (assunto/roteiro, estilo visual e duração de referência de {target}s, com teto de {maximum_duration}s) e defina público provável, promessa, hook inicial, progressão de retenção, insight/entrega e CTA adequado.
Escreva o melhor roteiro narrado completo para esse briefing. Como referência, use aproximadamente {min_words} a {max_words} palavras, sem tratar essa faixa como obrigação matemática: mire perto de {target}s e use até {maximum_duration}s somente se o desenvolvimento realmente precisar. A velocidade do sintetizador permanece natural. Nunca acelere, desacelere, repita, invente enchimento ou corte uma ideia importante apenas para atingir um tempo.
Se o usuário forneceu apenas um tema, crie o roteiro completo com raciocínio e conclusão suficientes. Se forneceu um texto, preserve as ideias essenciais; só reduza conteúdo redundante se ultrapassar o limite máximo.
O hook precisa estar na primeira fala. O CTA deve estar integrado à conclusão. Use palavras-chave SEO semanticamente relevantes de modo natural na narração. Gere título, descrição e poucas hashtags coerentes com o roteiro, sem keyword stuffing.
Depois divida esse roteiro em {minimum_scenes} a {preferred_scenes + 3} cenas narrativas. Meta: cerca de {preferred_scenes} cenas, considerando que o teto de {maximum_duration}s precisa caber em clipes de no máximo 5 segundos. Cada cena deve ter voiceover preenchido e conter um trecho contínuo do roteiro. O campo full_narration deve ser exatamente a concatenação das falas das cenas, com pontuação natural.
As durações de cena retornadas são apenas estimativas. O sistema medirá a duração real da narração na voz selecionada e distribuirá esse tempo entre as cenas. Não tente fazer a soma bater com {target}s, não encurte a narração e não acrescente texto para preencher segundos.
Cada cena deve mostrar ação concreta diretamente ligada à fala, com duas buscas visuais diferentes e específicas em inglês, estilo aplicado e pelo menos dois microeventos. Garanta hook, retenção, CTA e SEO preenchidos e coerentes com a narração. Retorne o JSON completo conforme o esquema do sistema."""

    plan = _request(prompt, secret_reader)
    apply_visual_style_lock(plan, style)
    scenes = plan.get("scenes", [])
    if not scenes:
        raise RuntimeError("O diretor não criou nenhuma cena. Tente planejar novamente.")

    def missing_voiceovers(items):
        return [i for i, scene in enumerate(items, 1)
                if not str(scene.get("voiceover", "") or "").strip()]

    # Hard protocol: never accept fewer than 10 scenes, even for 40 seconds.
    # Longer videos may require more to keep every clip at <=5 seconds.
    # Retry the director up to three times automatically, retaining the best
    # complete response and explicitly rejecting under-segmented output.
    repair_attempt = 0
    while len(scenes) < minimum_scenes and repair_attempt < 3:
        repair_attempt += 1
        repair_prompt = f"""PROTOCOLO OBRIGATÓRIO DO NEXUS — NÃO IGNORE:
O storyboard está REPROVADO: contém {len(scenes)} cenas. É proibido entregar 6, 7, 8 ou 9 cenas.
A janela editorial vai até {maximum_duration}s e exige NO MÍNIMO ABSOLUTO {minimum_scenes} CENAS para que nenhum clipe ultrapasse 5s. A quantidade mínima é uma regra rígida, não uma sugestão.
Reestruture o storyboard em pelo menos {minimum_scenes} cenas distintas e filmáveis, sem criar cenas artificiais ou repetidas. Respeite o teto de {maximum_duration}s e o limite de no máximo 5s por cena.
Preserve integralmente a narração, a ordem narrativa, a ideia e a progressão. Divida trechos longos em beats visuais menores; cada cena precisa ter voiceover não vazio, ação filmável própria, image_prompt, semantic_reason com pelo menos 80 caracteres, camera_motion, asset_search_query, fallback_search_query e pelo menos dois motion_events.
Não apague nem resuma falas. A concatenação das falas deve preservar o roteiro completo sem omissões ou repetições. Retorne o JSON COMPLETO com pelo menos {minimum_scenes} cenas. Tema: {topic}. Duração de referência: {target}s; teto: {maximum_duration}s. Estilo: {style}.
Esta é a tentativa automática de correção {repair_attempt} de 3.
Storyboard reprovado:
{json.dumps(plan, ensure_ascii=False)}
Retorne somente o JSON completo no formato do sistema."""
        repaired = _request(repair_prompt, secret_reader)
        apply_visual_style_lock(repaired, style)
        repaired_scenes = repaired.get("scenes", [])
        if len(repaired_scenes) > len(scenes):
            plan = repaired
            scenes = repaired_scenes

    if len(scenes) < minimum_scenes:
        raise RuntimeError(
            f"Planejamento recusado: o diretor retornou {len(scenes)} cenas, mas o protocolo "
            f"NEXUS exige no mínimo {minimum_scenes} para {target}s. Foram feitas 3 tentativas "
            "automáticas de correção; nenhuma resposta abaixo do mínimo será aceita. Tente planejar novamente."
        )

    # Ask the model to rewrite the missing narration, rather than accepting a
    # storyboard with silent scenes. Retry twice; duration itself is handled
    # deterministically and never depends on Gemini's duration estimates.
    for attempt in range(2):
        missing = missing_voiceovers(scenes)
        if not missing:
            break
        repair_prompt = f"""Você é roteirista. Corrija o storyboard abaixo.
Duração de referência: {target}s; teto absoluto: {maximum_duration}s. Tema/roteiro original: {topic}
As cenas sem narração são: {", ".join(map(str, missing))}.
Reescreva o storyboard COMPLETO, mantendo a ordem e as cenas, mas preenchendo TODAS as falas voiceover com texto natural em português brasileiro. Distribua a narração de forma contínua, sem falas vazias. Complete as falas sem inventar enchimento. Mire {target}s e nunca ultrapasse {maximum_duration}s. Preserve o sentido e a progressão. Inclua full_narration como concatenação exata das falas. Não use duration_seconds para limitar o roteiro; o sistema medirá a voz e atribuirá os tempos.
Estilo visual: {style}
Storyboard a corrigir:
{json.dumps(plan, ensure_ascii=False)}
Retorne somente JSON válido no formato do sistema."""
        plan = _request(repair_prompt, secret_reader)
        apply_visual_style_lock(plan, style)
        scenes = plan.get("scenes", [])
        if not scenes:
            raise RuntimeError("O diretor não retornou cenas na correção do roteiro.")

    missing = missing_voiceovers(scenes)
    if missing:
        raise RuntimeError(
            "O diretor deixou narrações vazias nas cenas "
            + ", ".join(map(str, missing))
            + " mesmo após duas tentativas de correção. O roteiro não foi aceito."
        )

    # Repair weak scene-to-narration links before final validation.
    # Keep approved narration, scene order and timing independent.
    _repair_semantic_justifications(plan, topic, style, target, secret_reader)
    apply_visual_style_lock(plan, style)

    # This is a planning estimate only. The selected TTS voice determines
    # the final runtime later; no text or audio is stretched to hit the target.
    original_total = sum(float(scene.get("duration_seconds", 0) or 0) for scene in scenes)
    word_count = sum(len(str(scene.get("voiceover", "")).split()) for scene in scenes)
    estimated_duration = word_count / 2.35
    if estimated_duration > maximum_duration + 0.75:
        raise RuntimeError(
            f"O roteiro estimado ficou em {estimated_duration:.1f}s, acima do teto de "
            f"{maximum_duration}s. O diretor precisa condensar redundâncias sem perder a ideia."
        )
    fitted = _fit_scene_durations(scenes, estimated_duration)
    plan["requested_duration_seconds"] = target
    plan["maximum_duration_seconds"] = maximum_duration
    plan["estimated_duration_seconds"] = round(sum(fitted), 2)
    plan["full_narration"] = " ".join(
        str(scene["voiceover"]).strip() for scene in scenes
    )
    plan["duration_adjustment"] = {
        "ai_estimated_seconds": round(original_total, 2),
        "requested_seconds": target,
        "maximum_seconds": maximum_duration,
        "estimated_speech_seconds": round(estimated_duration, 2),
        "scene_durations": fitted,
        "timing_source": "word_count_estimate_then_measured_tts",
    }
    return plan


def revise_narration_for_duration(plan, target_duration, actual_duration, topic, style, secret_reader):
    """Only shorten narration that exceeds the allowed ceiling; never pad to a target."""
    scenes = plan.get("scenes", [])
    if not scenes or float(actual_duration) <= 0 or float(target_duration) <= 0:
        raise ValueError("Não há dados suficientes para calibrar a duração da narração.")

    current_words = sum(len(str(scene.get("voiceover", "")).split()) for scene in scenes)
    target_words = max(1, int(round(current_words * float(target_duration) / float(actual_duration))))
    scene_context = [
        {
            "scene_number": index,
            "voiceover": str(scene.get("voiceover", "")),
            "visual_action": str(scene.get("visual_action", "")),
            "setting": str(scene.get("setting", "")),
            "subjects": str(scene.get("subjects", "")),
        }
        for index, scene in enumerate(scenes, 1)
    ]
    prompt = f"""Você é o roteirista responsável por adequar a narração ao tempo real de locução.
Tema original: {topic}
Estilo: {style}
Teto máximo permitido pelo usuário: {target_duration:.1f} segundos.
A voz selecionada, em velocidade NATURAL, leu a versão atual em {actual_duration:.1f} segundos, acima do teto.
A versão atual tem {current_words} palavras. Com a velocidade REAL medida dessa voz, a estimativa inicial para ficar abaixo do teto é aproximadamente {target_words} palavras.

Faça uma edição de contenção: encurte SOMENTE o necessário para ficar abaixo de {target_duration:.1f}s, preservando gancho, raciocínio, exemplos indispensáveis, progressão e conclusão. Remova redundâncias, não ideias centrais. Não reescreva por preferência estilística e não tente atingir um segundo exato.
É PROIBIDO expandir o texto, acrescentar exemplos novos, repetir ideias, criar pausas ou preencher duração. Se a mensagem não puder ser preservada dentro do teto, mantenha a integridade editorial e deixe a validação interromper o trabalho antes de gerar imagens.
Mantenha exatamente {len(scenes)} cenas e a mesma ordem. Distribua o texto entre elas de forma contínua. Cada fala precisa corresponder à ação visual da própria cena; ajuste a fala para manter coerência semântica. Não altere as ações visuais, buscas, estilo ou estrutura das cenas.
Use português brasileiro falado. Preserve e refine a pontuação como partitura de interpretação vocal: vírgulas para continuidade/respiração curta, pontos para fechamento e queda, dois-pontos para preparar revelação, travessões para apartes/contraste, interrogações para perguntas reais e exclamações com moderação. Varie frases curtas, médias e longas para cadência humana. Leia mentalmente em voz alta e mantenha a pontuação expressiva sem exageros. Não remova pontuação significativa na revisão.
Retorne somente JSON válido no formato:
{{"scenes":[{{"scene_number":1,"voiceover":"..."}}, ...]}}
Inclua exatamente uma entrada para cada cena, com índices de 1 a {len(scenes)}. O conjunto deve formar uma narração completa, sem lacunas nem repetição.
Contexto das cenas:
{json.dumps(scene_context, ensure_ascii=False)}"""

    revised = _request(prompt, secret_reader)
    voiceovers = revised.get("scenes", [])
    if not isinstance(voiceovers, list) or len(voiceovers) != len(scenes):
        raise RuntimeError("O diretor não retornou uma fala revisada para cada cena.")
    mapped = {}
    for item in voiceovers:
        try:
            index = int(item.get("scene_number", 0))
        except (TypeError, ValueError, AttributeError):
            raise RuntimeError("O diretor retornou numeração inválida nas falas revisadas.") from None
        voice = str(item.get("voiceover", "") or "").strip()
        if index < 1 or index > len(scenes) or not voice or index in mapped:
            raise RuntimeError("O diretor retornou falas vazias, duplicadas ou fora de ordem.")
        mapped[index] = voice
    if set(mapped) != set(range(1, len(scenes) + 1)):
        raise RuntimeError("A revisão da narração não cobriu todas as cenas.")

    for index, scene in enumerate(scenes, 1):
        scene["voiceover"] = mapped[index]
    plan["full_narration"] = " ".join(mapped[index] for index in range(1, len(scenes) + 1))
    plan["narration_calibration"] = {
        "previous_audio_seconds": round(float(actual_duration), 2),
        "maximum_audio_seconds": round(float(target_duration), 2),
        "previous_word_count": current_words,
        "estimated_target_word_count": target_words,
    }
    return plan


def review_visual_candidates(scene, candidates_with_frames, secret_reader, minimum_confidence=55):
    """Use Gemini vision to reject stock clips that do not depict the planned scene."""
    if not candidates_with_frames:
        return {"selected_candidate": 0, "confidence": 0, "reason": "Nenhum candidato visual disponível."}
    key = secret_reader("GEMINI_API_KEY")
    requested = secret_reader("GEMINI_MODEL", "auto")
    if not key:
        raise RuntimeError("A avaliação visual exige GEMINI_API_KEY.")
    models = discover_models(key, requested)
    prompt = f"""Você é o supervisor de continuidade visual de uma produtora audiovisual.
Avalie os quadros reais dos clipes candidatos e escolha o que melhor comunica a ideia da cena para o espectador.
Trecho exato da narração: {scene.get('voiceover', '')}
Ação visual planejada: {scene.get('visual_action', '')}
Sujeitos: {scene.get('subjects', '')}
Ambiente: {scene.get('setting', '')}
Justificativa semântica: {scene.get('semantic_reason', '')}
Estilo visual obrigatório do vídeo: {scene.get('visual_style', scene.get('style_search_terms', ''))}
Direção de arte completa do estilo: {build_visual_style_directive(scene.get('visual_style', 'Cinematográfico'))}
REGRA ANTI-TEMPLATE: avalie o conteúdo desta cena pelo seu significado próprio. Não procure um sujeito, objeto, cenário ou clichê associado ao estilo; a identidade estética é secundária à intenção narrativa. Prefira soluções visuais variadas e específicas ao trecho.
Busca visual solicitada: {scene.get('asset_search_query', '')}

CRITÉRIO DE DECISÃO:
1. Priorize a conexão narrativa útil: o clipe pode mostrar a ação literal, uma consequência visual, uma metáfora visual reconhecível ou uma situação cotidiana que comunique claramente a mesma ideia. Não exija que cada objeto ou palavra da narração apareça literalmente no vídeo. Ex.: planejar pode ser mostrado por alguém escrevendo, organizando tarefas ou olhando um calendário; superar um obstáculo pode ser mostrado por alguém subindo uma escada ou atravessando uma porta.
2. Estilo visual é critério secundário: entre candidatos com conexão narrativa semelhante, prefira o que respeita melhor o estilo bloqueado. Nunca escolha um vídeo de baixa conexão narrativa apenas por combinar com o estilo.
3. Qualidade técnica é critério terciário: prefira vídeo vertical e enquadramento mais próximo de 9:16 (0,5625), depois resolução e nitidez. Não escolha paisagem horizontal se houver candidato vertical semanticamente equivalente.
4. Avalie TODOS os candidatos juntos e compare os quadros reais, não apenas títulos, tags ou descrições. Pontue separadamente a utilidade narrativa (semantic_match, 0–100) e a aderência ao estilo (style_match, 0–100). Escolha o candidato com melhor utilidade narrativa. Considere contexto, gesto, ambiente, consequência e metáfora; não penalize uma representação indireta quando ela comunica bem a ideia. confidence deve refletir o quanto o clipe funciona para ilustrar a cena em uma edição profissional.
5. O vídeo final será 9:16 (720×1280). Avalie se o conteúdo principal permanece legível e bem composto em corte vertical; evite candidatos cuja ação principal ficaria fora do quadro.
Não aceite apenas semelhança de cor, clima ou estética sem conexão narrativa. Porém, não rejeite um clipe só porque ele não reproduz literalmente a frase: metáforas visuais e B-roll contextual são válidos quando um editor humano entenderia a relação sem explicação. Só selecione 0 quando todos os candidatos forem realmente desconexos, tecnicamente inutilizáveis ou incompatíveis com a cena. Entre um candidato imperfeito mas útil e a ausência total de clipe, prefira o candidato útil. Aprove com confidence mínima de {int(minimum_confidence)}.
Retorne somente JSON: {{"selected_candidate":1,"semantic_match":88,"style_match":72,"confidence":88,"reason":"..."}}.
Os números dos candidatos aparecem imediatamente antes de seus quadros."""

    parts = [{"text": prompt}]
    for index, entry in enumerate(candidates_with_frames, 1):
        candidate = entry.get("candidate", {})
        parts.append({"text": (
            f"CANDIDATO {index} | Biblioteca: {candidate.get('source', 'desconhecida')} | "
            f"Título/tags: {candidate.get('title', '')} | "
            f"Descrição: {candidate.get('description', '')} | "
            f"Dimensões: {candidate.get('width', 0)}×{candidate.get('height', 0)} | "
            f"Proporção: {candidate.get('_nexus_aspect_ratio', 'desconhecida')}"
        )})
        for frame_path in entry.get("frame_paths", []):
            frame = Path(frame_path)
            if frame.exists() and frame.stat().st_size:
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": base64.b64encode(frame.read_bytes()).decode("ascii"),
                    }
                })
    if not any("inlineData" in part for part in parts):
        raise RuntimeError("Não foi possível extrair quadros para avaliação visual.")

    last_error = None
    for model in models[:3]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            response = requests.post(
                url,
                params={"key": key},
                json={
                    "contents": [{"role": "user", "parts": parts}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                        "maxOutputTokens": 1024,
                    },
                },
                timeout=120,
            )
            if response.status_code in (404, 429, 500, 502, 503, 504):
                last_error = f"{model}: HTTP {response.status_code}"
                continue
            response.raise_for_status()
            payload = response.json()
            response_text = "\n".join(
                part.get("text", "")
                for part in payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                if part.get("text")
            )
            cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", response_text.strip(), flags=re.I)
            result = json.loads(cleaned)
            selected = int(result.get("selected_candidate", 0))
            confidence = max(0, min(100, int(result.get("confidence", result.get("semantic_match", 0)))))
            semantic_match = max(0, min(100, int(result.get("semantic_match", confidence))))
            style_match = max(0, min(100, int(result.get("style_match", 0))))
            reason = str(result.get("reason", "")).strip()
            if selected < 1 or selected > len(candidates_with_frames) or confidence < int(minimum_confidence):
                return {
                    "selected_candidate": 0,
                    "confidence": confidence,
                    "semantic_match": semantic_match,
                    "style_match": style_match,
                    "reason": reason or "Nenhum clipe atingiu a confiança visual mínima.",
                }
            return {
                "selected_candidate": selected,
                "confidence": confidence,
                "semantic_match": semantic_match,
                "style_match": style_match,
                "reason": reason,
            }
        except (requests.RequestException, ValueError, TypeError, KeyError, IndexError) as exc:
            last_error = str(exc)[:400]
            continue
    raise RuntimeError("A avaliação visual do Gemini falhou: " + (last_error or "nenhum modelo respondeu."))

def validate_storyboard(plan, requested_duration=None):
    errors = []
    scenes = plan.get("scenes", [])
    if not scenes:
        return ["O diretor não criou cenas."]
    total = 0
    maximum_duration = float(requested_duration) + 10 if requested_duration else None
    minimum_scenes = max(10, int((maximum_duration + 4) // 5)) if maximum_duration else 10
    if len(scenes) < minimum_scenes:
        errors.append(f"O diretor criou {len(scenes)} cenas, mas são necessárias pelo menos {minimum_scenes} para cobrir {requested_duration}s sem segmentos longos.")
    for index, scene in enumerate(scenes, 1):
        total += float(scene.get("duration_seconds", 0) or 0)
        for field in ("voiceover", "visual_action", "image_prompt", "semantic_reason", "camera_motion", "asset_search_query", "visual_style", "style_search_terms"):
            if not str(scene.get(field, "")).strip():
                errors.append(f"Cena {index}: campo {field} vazio.")
        if len(scene.get("semantic_reason", "")) < 80:
            errors.append(f"Cena {index}: justificativa semântica insuficiente.")
        if len(scene.get("motion_events", [])) < 2:
            errors.append(f"Cena {index}: faltam microeventos.")
    if requested_duration:
        if total > maximum_duration + 0.75:
            errors.append(
                f"A estimativa de narração é {total:.1f}s, acima do teto editorial "
                f"de {maximum_duration:.0f}s ({requested_duration}s + 10s)."
            )
        if any(float(scene.get("duration_seconds", 0) or 0) > 5.0 for scene in scenes):
            errors.append("Há cenas acima de 5 segundos. Divida a ação em mais clipes específicos.")
    return errors
