import json
import re
import requests

SYSTEM = """
Você é o DIRETOR AUDIOVISUAL do NEXUS VIDEO STUDIO, não um gerador de palavras-chave.
Leia e compreenda o roteiro inteiro antes de planejar qualquer cena. Identifique a ideia central, a progressão lógica, as afirmações, os exemplos e a emoção de cada trecho.
A fala define exatamente o que o público deve ver. Cada cena deve mostrar uma ação, objeto, pessoa, ambiente ou processo diretamente relacionado à fala. Não use cenas genéricas só porque combinam com a emoção.
Respeite rigorosamente o estilo visual selecionado pelo usuário. Traduza esse estilo em fotografia, paleta, luz, textura, lente, movimento e atmosfera em TODAS as cenas. Inclua em cada cena visual_style e style_search_terms; as buscas em inglês devem incorporar termos visuais compatíveis com o estilo escolhido, sem sacrificar assunto e ação.
Priorize ações filmáveis e específicas. Evite slideshows, colagens, infográficos escolares, imagens abstratas sem função e repetição de enquadramentos.
Não invente fatos, capas, páginas, citações, nomes ou características de produtos/livros. Diferencie fatos verificados, crenças e alegações.
A QUANTIDADE DE CENAS É DECIDIDA A PARTIR DA DURAÇÃO E DA DENSIDADE DO ROTEIRO, nunca por uma lista fixa de temas. Para vídeos de 40–60 segundos, crie no mínimo ceil(duração/5) cenas e prefira ceil(duração/4) ou mais: 50s deve gerar pelo menos 10 cenas, com meta de 12–15; 40s pelo menos 8, meta 10–12; 60s pelo menos 12, meta 15–18. Em geral, cada clipe cobre 3–4 segundos; varie conforme a fala e a ação, sem esticar artificialmente cenas. A soma das durações deve corresponder à duração solicitada. Cada cena precisa de busca visual própria, derivada da ação, objeto, ambiente e significado EXATOS daquele trecho. Nunca reutilize um conjunto fixo de palavras-chave nem force objetos que não estejam no roteiro. As buscas principal e alternativa devem ser distintas, concretas, em inglês e específicas daquela cena. Toda cena deve ter pelo menos dois microeventos visuais.
Para cada cena, descreva: o que aparece, o que acontece em ordem, onde, quem/que objeto, enquadramento, movimento de câmera e duas buscas alternativas de clipes em inglês.
Retorne somente JSON válido:
{
 "topic_interpretation":"...",
 "creative_thesis":"...",
 "style_lock":"...",
 "scenes":[
  {
   "duration_seconds":5,
   "purpose":"...",
   "voiceover":"fala exata desta parte",
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
    """Distribute the requested runtime across existing scenes, keeping clips 2–5s."""
    target = int(round(float(requested_duration)))
    count = len(scenes)
    if not count or target < 2 * count or target > 5 * count:
        raise ValueError(
            f"Não é possível distribuir {target}s em {count} cenas mantendo cada clipe entre 2 e 5 segundos."
        )

    original = [max(0.1, float(scene.get("duration_seconds", 0) or 0)) for scene in scenes]
    durations = [2] * count
    remaining = target - sum(durations)
    capacities = [3] * count

    # Weighted water-filling: preserve the director's relative pacing while
    # respecting the 2–5 second range for every stock-video clip.
    while remaining > 0:
        active = [i for i, capacity in enumerate(capacities) if capacity > 0]
        if not active:
            raise ValueError("As cenas não comportam a duração solicitada.")
        weight_sum = sum(original[i] for i in active)
        shares = {i: remaining * original[i] / weight_sum for i in active}
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
            key=lambda i: (shares[i] - int(shares[i]), original[i]),
            reverse=True,
        )
        if not ranked:
            continue
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
    minimum_acceptable = max(1, target - 5)
    maximum_acceptable = target + 5
    prompt = f"""ASSUNTO OU ROTEIRO COMPLETO:
{topic}

ESTILO VISUAL ESCOLHIDO PELO USUÁRIO (OBRIGATÓRIO EM TODAS AS CENAS): {style}
DURAÇÃO ESCOLHIDA PELO USUÁRIO: {target} segundos.
REGRA DE PLANEJAMENTO: a primeira versão do storyboard pode somar entre {minimum_acceptable} e {maximum_acceptable} segundos. Trabalhe dentro dessa margem de cinco segundos para menos ou para mais. Nunca ignore a duração escolhida. Depois o sistema ajustará proporcionalmente a linha do tempo para a duração final exata de {target} segundos.
Use no mínimo ceil(duração/5) cenas e prefira ceil(duração/4) ou mais. Para 50 segundos, planeje 12–15 cenas. Cada cena deve durar entre 2 e 5 segundos. A soma deve ficar dentro da margem informada.
Cada cena PRECISA conter uma fala real em português brasileiro no campo voiceover. Não deixe voiceover vazio, nulo ou apenas espaços. Distribua todo o conteúdo narrado do roteiro entre as cenas, sem perder trechos nem repetir frases. Se o assunto for curto, desenvolva a explicação com conteúdo coerente, sem inventar fatos.
Planeje primeiro a narrativa completa. Cada cena precisa de ação filmável específica, relacionada diretamente à fala. Para cada trecho, gere buscas principal e alternativa próprias, específicas e diferentes, em inglês. Preserve estilo visual, coerência semântica e continuidade narrativa. Retorne somente JSON válido no formato solicitado pelo sistema."""

    plan = _request(prompt, secret_reader)
    plan["style_lock"] = style
    scenes = plan.get("scenes", [])
    if not scenes:
        raise RuntimeError("O diretor não criou nenhuma cena. Tente planejar novamente.")

    def missing_voiceovers(items):
        return [
            index for index, scene in enumerate(items, 1)
            if not str(scene.get("voiceover", "") or "").strip()
        ]

    original_total = sum(float(scene.get("duration_seconds", 0) or 0) for scene in scenes)
    missing = missing_voiceovers(scenes)
    outside_margin = not (minimum_acceptable <= original_total <= maximum_acceptable)

    # One targeted correction pass gives the director a chance to fix incomplete
    # narration or a runtime estimate outside the user's five-second tolerance.
    if missing or outside_margin:
        issues = []
        if missing:
            issues.append("voiceover vazio nas cenas: " + ", ".join(map(str, missing)))
        if outside_margin:
            issues.append(
                f"a soma atual é {original_total:.1f}s, fora da faixa "
                f"{minimum_acceptable}–{maximum_acceptable}s"
            )
        repair_prompt = f"""O storyboard anterior precisa de correção antes de ser aceito.

ROTEIRO ORIGINAL:
{topic}

DURAÇÃO ESCOLHIDA: {target}s
FAIXA ACEITÁVEL PARA ESTA RESPOSTA: {minimum_acceptable}–{maximum_acceptable}s
ESTILO VISUAL: {style}

PROBLEMAS ENCONTRADOS:
{'; '.join(issues)}

STORYBOARD A CORRIGIR:
{json.dumps(plan, ensure_ascii=False)}

Recrie o storyboard completo em JSON válido, preservando a progressão narrativa e as ações visuais que já estão corretas. Corrija todos os problemas listados. TODA cena deve ter voiceover preenchido com uma fala natural em português brasileiro, coerente com o roteiro e com a cena. Não deixe nenhum campo voiceover vazio. A soma de duration_seconds precisa ficar entre {minimum_acceptable} e {maximum_acceptable} segundos. Use cenas entre 2 e 5 segundos. Não omita cenas nem campos obrigatórios. Retorne somente o JSON completo no formato do sistema."""
        corrected = _request(repair_prompt, secret_reader)
        corrected["style_lock"] = style
        corrected_scenes = corrected.get("scenes", [])
        if not corrected_scenes:
            raise RuntimeError("O diretor não conseguiu corrigir o storyboard. Gere o planejamento novamente.")
        still_missing = missing_voiceovers(corrected_scenes)
        if still_missing:
            raise RuntimeError(
                "O diretor ainda deixou a narração vazia nas cenas "
                + ", ".join(map(str, still_missing))
                + ". O planejamento foi interrompido para não produzir vídeo sem fala."
            )
        corrected_total = sum(
            float(scene.get("duration_seconds", 0) or 0) for scene in corrected_scenes
        )
        if not (minimum_acceptable <= corrected_total <= maximum_acceptable):
            raise RuntimeError(
                f"Após a correção, a IA retornou {corrected_total:.1f}s. "
                f"A faixa permitida para {target}s é {minimum_acceptable}–{maximum_acceptable}s. "
                "Tente planejar novamente."
            )
        plan = corrected
        scenes = corrected_scenes
        original_total = corrected_total

    # The AI may land anywhere inside the requested ±5s tolerance. The final
    # timeline is then normalized to the exact duration selected by the user.
    fitted = _fit_scene_durations(scenes, target)
    plan["duration_adjustment"] = {
        "ai_seconds": round(original_total, 2),
        "requested_seconds": target,
        "tolerance_seconds": 5,
        "scene_durations": fitted,
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
