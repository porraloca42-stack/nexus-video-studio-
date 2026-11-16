import json
import re
import requests

SYSTEM = """
Você é o DIRETOR AUDIOVISUAL do NEXUS VIDEO STUDIO, não um gerador de palavras-chave.
Leia e compreenda o roteiro inteiro antes de planejar qualquer cena. Identifique a ideia central, a progressão lógica, as afirmações, os exemplos e a emoção de cada trecho.
A fala define exatamente o que o público deve ver. Cada cena deve mostrar uma ação, objeto, pessoa, ambiente ou processo diretamente relacionado à fala. Não use cenas genéricas só porque combinam com a emoção.
Mantenha UM estilo visual do início ao fim: fotografia, paleta, luz, textura, lente e atmosfera coerentes. Não misture estilos.
Priorize ações filmáveis e específicas. Evite slideshows, colagens, infográficos escolares, imagens abstratas sem função e repetição de enquadramentos.
Não invente fatos, capas, páginas, citações, nomes ou características de produtos/livros. Diferencie fatos verificados, crenças e alegações.
Divida a duração em cenas com ritmo variado, normalmente 3 a 7 segundos. Não force cenas de 10 segundos. Toda cena deve ter pelo menos dois microeventos visuais.
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
    nums = re.findall(r"\\d+", name.lower())
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
    # Prefer the newest Pro reasoning model actually exposed to THIS key.
    def rank(m):
        name = m.get("name", "").split("/")[-1].lower()
        family = 3 if "pro" in name else 2 if "flash" in name else 1
        stable = 1 if "preview" not in name and "exp" not in name else 0
        return (family, stable, _model_version(name))
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
            "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json"}
        }
        response = requests.post(url, params={"key": key}, json=payload, timeout=240)
    except requests.RequestException:
        raise RuntimeError("Não foi possível conectar ao serviço Gemini. Tente novamente.") from None
    if response.status_code == 429:
        raise RuntimeError("Limite temporário do modelo atingido. Tente novamente mais tarde.")
    if response.status_code in (401, 403):
        raise RuntimeError("O Gemini recusou a autenticação ou o acesso ao modelo.")
    if response.status_code == 404:
        raise RuntimeError(f"O modelo selecionado ({model}) não está disponível. Configure GEMINI_MODEL = \"auto\" em Secrets.")
    if not response.ok:
        raise RuntimeError(f"Falha no Gemini (HTTP {response.status_code}).")
    data = response.json()
    try:
        result = data["candidates"][0]["content"]["parts"][0]["text"]
        plan = json.loads(result)
        plan["director_model"] = model
        return plan
    except (KeyError, IndexError, ValueError):
        raise RuntimeError("O diretor não retornou um storyboard JSON válido.") from None

def create_storyboard(topic, style, duration, secret_reader):
    prompt = f"""ASSUNTO OU ROTEIRO COMPLETO:
{topic}

ESTILO VISUAL ÚNICO E BLOQUEADO: {style}
DURAÇÃO TOTAL: {duration} segundos.
Planeje primeiro a narrativa completa. Depois divida em cenas com ritmo variado. A soma das durações deve ficar próxima da duração pedida. Preserve a relação semântica exata entre cada fala e sua imagem. Escreva a narração em português brasileiro natural."""
    plan = _request(prompt, secret_reader)
    plan["style_lock"] = style
    return plan

def validate_storyboard(plan):
    errors = []
    scenes = plan.get("scenes", [])
    if not scenes:
        return ["O diretor não criou cenas."]
    total = 0
    for index, scene in enumerate(scenes, 1):
        total += float(scene.get("duration_seconds", 0) or 0)
        for field in ("voiceover", "visual_action", "semantic_reason", "camera_motion", "asset_search_query"):
            if not str(scene.get(field, "")).strip():
                errors.append(f"Cena {index}: campo {field} vazio.")
        if len(scene.get("semantic_reason", "")) < 35:
            errors.append(f"Cena {index}: justificativa semântica superficial.")
        if len(scene.get("motion_events", [])) < 2:
            errors.append(f"Cena {index}: faltam microeventos.")
    return errors
