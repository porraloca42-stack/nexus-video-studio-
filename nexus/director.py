import json
import re
import requests

SYSTEM = """
Você é o DIRETOR E ROTEIRISTA AUDIOVISUAL do NEXUS VIDEO STUDIO.
Sua primeira obrigação é entregar um ROTEIRO NARRADO COMPLETO, dimensionado para a duração escolhida pelo usuário. Em seguida, transforme esse roteiro em cenas filmáveis. Não trate duração como sugestão.

DURAÇÃO E TEXTO:
- O usuário escolhe a duração final. Ela é um requisito obrigatório.
- Para narração natural em português brasileiro, escreva aproximadamente 2,2 a 2,5 palavras por segundo: 40s ≈ 88–100 palavras; 50s ≈ 110–125 palavras; 60s ≈ 132–150 palavras.
- Se o usuário fornecer apenas um tema/ideia, desenvolva o roteiro completo com essa extensão, começo forte, progressão lógica e fechamento.
- Se fornecer um roteiro completo, preserve sua mensagem e os pontos essenciais; ajuste a redação para caber no tempo, sem simplesmente copiar um texto curto ou ignorar a duração.
- Distribua TODO o texto narrado entre as cenas. Cada cena precisa ter voiceover não vazio, em português brasileiro natural. A soma das falas deve formar o roteiro completo, sem lacunas, repetições ou frases soltas.
- Não tente resolver duração escrevendo menos cenas ou deixando cenas sem fala.

CENAS:
- Decida a quantidade a partir da duração e da progressão narrativa. Use pelo menos ceil(duração/5) cenas e prefira ceil(duração/4) ou mais: 50s normalmente 12–15 cenas; 40s 10–12; 60s 15–18.
- Cada cena representa uma unidade narrativa e uma ação concreta. As durações são apenas estimativas: o sistema atribuirá a duração final exata depois. Não sacrifique a narrativa para tentar fazer a soma matemática.
- Cada cena deve representar exatamente o trecho narrado com ação, objeto, pessoa, ambiente ou processo diretamente relacionado. Não use cenas genéricas só porque combinam com a emoção.
- Leia e compreenda o roteiro inteiro antes de planejar cenas. Identifique ideia central, progressão, afirmações, exemplos e emoção de cada trecho.
- Priorize ações filmáveis e específicas. Evite slideshows, colagens, infográficos escolares, imagens abstratas sem função e repetição de enquadramentos.
- Cada cena precisa de busca visual própria, derivada da ação, objeto, ambiente e significado EXATOS daquele trecho. Nunca reutilize conjunto fixo de palavras-chave nem force objetos que não estejam no roteiro. Buscas principal e alternativa devem ser distintas, concretas, em inglês.
- Respeite rigorosamente o estilo visual selecionado. Traduza-o em fotografia, paleta, luz, textura, lente, movimento e atmosfera em TODAS as cenas. Inclua visual_style e style_search_terms.
- Toda cena deve ter pelo menos dois microeventos visuais.

Retorne somente JSON válido:
{
 "topic_interpretation":"...",
 "creative_thesis":"...",
 "style_lock":"...",
 "full_narration":"roteiro narrado integral em português brasileiro",
 "scenes":[
  {
   "duration_seconds":4,
   "purpose":"...",
   "voiceover":"trecho contínuo do roteiro integral",
   "visual_action":"ação específica e observável, em sequência",
   "visual_style":"estilo visual aplicado nesta cena",
   "style_search_terms":"English visual-style terms to append to the scene search",
   "semantic_reason":"relação direta entre a fala e a imagem",
   "setting":"...",
   "subjects":"...",
   "shot_type":"...",
   "camera_motion":"push_in, pull_out, pan_left ou pan_right",
   "motion_events":["microevento 1","microevento 2"],
   "asset_search_query":"English query with concrete subject and action",
   "fallback_search_query":"different concrete English query"
  }
 ]
}
"""

def _model_version(name):
    nums = re.findall(r"\d+", name.lower())
    return tuple(int(n) for n in nums[:3]) if nums else (0,)

def discover_model(api_key, requested="auto"):
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=45,
    )
    if response.status_code in (401, 403):
        raise RuntimeError("A API do Gemini recusou a chave ou não autorizou a listagem de modelos.")
    response.raise_for_status()
    models = response.json().get("models", [])
    supported = [
        m for m in models
        if "generateContent" in m.get("supportedGenerationMethods", [])
        and "embedding" not in m.get("name", "").lower()
    ]
    if not supported:
        raise RuntimeError("A chave não retornou modelos compatíveis com geração de conteúdo.")
    requested = (requested or "auto").strip()
    if requested.lower() not in ("", "auto"):
        match = next((m for m in supported if m.get("name", "").split("/")[-1] == requested.replace("models/", "")), None)
        if match:
            return match["name"].split("/")[-1]
    # Use the model the user confirmed has available quota in their AI Studio project.
    preferred = next(
        (m for m in supported if m.get("name", "").split("/")[-1] == "gemini-3.5-flash-lite"),
        None,
    )
    if preferred:
        return preferred["name"].split("/")[-1]
    # Fallback: prefer stable Flash-Lite before higher tiers that may be quota-blocked.
    def rank(m):
        name = m.get("name", "").split("/")[-1].lower()
        lite = 1 if "flash-lite" in name else 0
        stable = 1 if "preview" not in name and "exp" not in name else 0
        return (lite, stable, _model_version(name))
    supported.sort(key=rank, reverse=True)
    return supported[0]["name"].split("/")[-1]

def _request(prompt, secret_reader):
    key = secret_reader("GEMINI_API_KEY")
    requested = secret_reader("GEMINI_MODEL", "auto")
    if not key:
        raise RuntimeError("Diretor de IA indisponível: configure GEMINI_API_KEY.")
    try:
        model = discover_model(key, requested)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.25, "responseMimeType": "application/json", "maxOutputTokens": 8192}
        }
        response = requests.post(url, params={"key": key}, json=payload, timeout=240)
    except requests.RequestException:
        raise RuntimeError("Não foi possível conectar ao serviço Gemini. Tente novamente.") from None
    if response.status_code == 429:
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = ""
        detail = detail[:700] if detail else "A API não informou o detalhe da cota."
        raise RuntimeError(f"Gemini recusou a solicitação por limite/cota (HTTP 429) no modelo {model}. Detalhe: {detail} Confira o limite desse modelo no AI Studio: https://aistudio.google.com/rate-limit")
    if response.status_code in (401, 403):
        raise RuntimeError("O Gemini recusou a autenticação ou o acesso ao modelo.")
    if response.status_code == 404:
        raise RuntimeError(f"O modelo selecionado ({model}) não está disponível. Configure GEMINI_MODEL = \"auto\" em Secrets.")
    if not response.ok:
        raise RuntimeError(f"Falha no Gemini (HTTP {response.status_code}).")
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        feedback = data.get("promptFeedback", {}).get("blockReason")
        suffix = " (bloqueio: " + str(feedback) + ")." if feedback else "."
        raise RuntimeError("O Gemini não gerou o storyboard" + suffix + " Revise o roteiro ou tente novamente.")
    candidate = candidates[0]
    finish_reason = candidate.get("finishReason", "desconhecido")
    parts = candidate.get("content", {}).get("parts", [])
    result = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text"))
    if not result.strip():
        raise RuntimeError("O Gemini retornou uma resposta sem texto (motivo: " + str(finish_reason) + "). Tente novamente.")
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", result.strip(), flags=re.IGNORECASE)
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
        if finish_reason == "MAX_TOKENS":
            raise RuntimeError("O Gemini interrompeu a resposta por limite de saída antes de concluir o storyboard. Tente novamente; a geração agora permite uma resposta maior.")
        preview = re.sub(r"\s+", " ", result)[:350]
        raise RuntimeError("O Gemini não retornou JSON completo e válido (motivo: " + str(finish_reason) + "). Trecho recebido: " + preview)
    plan["director_model"] = model
    return plan

def _fit_scene_durations(scenes, requested_duration):
    """Assign the exact requested runtime using each scene's narration length."""
    target = int(round(float(requested_duration)))
    count = len(scenes)
    if not count or target < 2 * count or target > 5 * count:
        raise ValueError(
            f"O diretor criou {count} cenas, mas {target}s exige entre "
            f"{(target + 4) // 5} e {target // 2} cenas para clipes de 2–5s. "
            "Peça um novo planejamento."
        )

    # Narration length is a better pacing signal than Gemini's rough duration guess.
    weights = []
    for scene in scenes:
        words = len(str(scene.get("voiceover", "")).split())
        weights.append(float(max(words, 1)))
    durations = [2] * count
    remaining = target - 2 * count
    capacities = [3] * count

    while remaining > 0:
        active = [i for i, capacity in enumerate(capacities) if capacity > 0]
        if not active:
            raise ValueError("As cenas não comportam a duração solicitada.")
        weight_sum = sum(weights[i] for i in active)
        shares = {i: remaining * weights[i] / weight_sum for i in active}
        allocated = 0
        for i in active:
            whole = min(capacities[i], int(shares[i]))
            if whole:
                durations[i] += whole
                capacities[i] -= whole
                allocated += whole
        remaining -= allocated
        if remaining <= 0:
            break
        ranked = sorted(
            (i for i in active if capacities[i] > 0),
            key=lambda i: (shares[i] - int(shares[i]), weights[i]),
            reverse=True,
        )
        for i in ranked:
            if remaining <= 0:
                break
            durations[i] += 1
            capacities[i] -= 1
            remaining -= 1

    for scene, seconds in zip(scenes, durations):
        scene["duration_seconds"] = seconds
    return durations


def create_storyboard(topic, style, duration, secret_reader):
    target = int(round(float(duration)))
    minimum_scenes = max(1, (target + 4) // 5)
    preferred_scenes = max(minimum_scenes, (target + 3) // 4)
    min_words = int(round(target * 2.2))
    max_words = int(round(target * 2.5))
    prompt = f"""PEDIDO/ROTEIRO DO USUÁRIO:
{topic}

DURAÇÃO FINAL ESCOLHIDA: {target} segundos (OBRIGATÓRIA).
ESTILO VISUAL: {style}

Primeiro escreva um roteiro narrado completo de aproximadamente {min_words} a {max_words} palavras, adequado a {target} segundos de fala natural em português brasileiro.
Se o usuário forneceu apenas um tema, crie o roteiro completo. Se forneceu um texto, preserve as ideias essenciais e adapte a extensão ao tempo, sem ignorar o pedido.
Depois divida esse roteiro em {minimum_scenes} a {preferred_scenes + 3} cenas narrativas. Meta: cerca de {preferred_scenes} cenas. Cada cena deve ter voiceover preenchido e conter um trecho contínuo do roteiro. O campo full_narration deve ser exatamente a concatenação das falas das cenas, com pontuação natural.
As durações de cena são estimativas; NÃO tente fechar a soma matemática. O sistema atribuirá a duração exata depois. Não encurte a narração para fazer a soma bater.
Cada cena deve mostrar ação concreta diretamente ligada à fala, com duas buscas visuais diferentes e específicas em inglês, estilo aplicado e pelo menos dois microeventos. Retorne o JSON completo conforme o esquema do sistema."""

    plan = _request(prompt, secret_reader)
    plan["style_lock"] = style
    scenes = plan.get("scenes", [])
    if not scenes:
        raise RuntimeError("O diretor não criou nenhuma cena. Tente planejar novamente.")

    def missing_voiceovers(items):
        return [i for i, scene in enumerate(items, 1)
                if not str(scene.get("voiceover", "") or "").strip()]

    # Ask the model to rewrite the missing narration, rather than accepting a
    # storyboard with silent scenes. Retry twice; duration itself is handled
    # deterministically and never depends on Gemini's duration estimates.
    for attempt in range(2):
        missing = missing_voiceovers(scenes)
        if not missing:
            break
        repair_prompt = f"""Você é roteirista. Corrija o storyboard abaixo.
Duração final escolhida: {target}s. Tema/roteiro original: {topic}
As cenas sem narração são: {", ".join(map(str, missing))}.
Reescreva o storyboard COMPLETO, mantendo a ordem e as cenas, mas preenchendo TODAS as falas voiceover com texto natural em português brasileiro. Distribua a narração de forma contínua, sem falas vazias. Escreva uma narração total de aproximadamente {min_words}–{max_words} palavras adequada a {target}s. Inclua full_narration como concatenação exata das falas. Não use duration_seconds para limitar o roteiro; o sistema atribuirá os tempos.
Estilo visual: {style}
Storyboard a corrigir:
{json.dumps(plan, ensure_ascii=False)}
Retorne somente JSON válido no formato do sistema."""
        plan = _request(repair_prompt, secret_reader)
        plan["style_lock"] = style
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

    # The AI creates the script and narrative structure; code owns exact timing.
    original_total = sum(float(scene.get("duration_seconds", 0) or 0) for scene in scenes)
    fitted = _fit_scene_durations(scenes, target)
    plan["requested_duration_seconds"] = target
    plan["full_narration"] = " ".join(
        str(scene["voiceover"]).strip() for scene in scenes
    )
    plan["duration_adjustment"] = {
        "ai_estimated_seconds": round(original_total, 2),
        "requested_seconds": target,
        "scene_durations": fitted,
        "timing_source": "narration_weighted_exact_allocation",
    }
    return plan

def validate_storyboard(plan, requested_duration=None):
    errors = []
    scenes = plan.get("scenes", [])
    if not scenes:
        return ["O diretor não criou cenas."]
    total = 0
    minimum_scenes = max(1, int((float(requested_duration) + 4) // 5)) if requested_duration else 1
    if len(scenes) < minimum_scenes:
        errors.append(f"O diretor criou {len(scenes)} cenas, mas são necessárias pelo menos {minimum_scenes} para cobrir {requested_duration}s sem segmentos longos.")
    for index, scene in enumerate(scenes, 1):
        total += float(scene.get("duration_seconds", 0) or 0)
        for field in ("voiceover", "visual_action", "semantic_reason", "camera_motion", "asset_search_query", "visual_style", "style_search_terms"):
            if not str(scene.get(field, "")).strip():
                errors.append(f"Cena {index}: campo {field} vazio.")
        if len(scene.get("semantic_reason", "")) < 35:
            errors.append(f"Cena {index}: justificativa semântica superficial.")
        if len(scene.get("motion_events", [])) < 2:
            errors.append(f"Cena {index}: faltam microeventos.")
    if requested_duration:
        if abs(total - float(requested_duration)) > 0.75:
            errors.append(f"A soma das cenas é {total:.1f}s; a duração solicitada é {requested_duration}s.")
        if any(float(scene.get("duration_seconds", 0) or 0) > 5.0 for scene in scenes):
            errors.append("Há cenas acima de 5 segundos. Divida a ação em mais clipes específicos.")
    return errors
