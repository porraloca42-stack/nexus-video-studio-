"""Prompt builders for the NEXUS four-brain chain.

Pure functions only: they prepare stage-specific instructions and never call a
model, read credentials, or access external services.
"""
import json


def _payload(value):
    if not isinstance(value, dict):
        raise TypeError("stage input must be a dictionary")
    return json.dumps(value, ensure_ascii=False, indent=2)


def build_hook_strategy_prompt(brief):
    return f"""BRAIN 1 — ESTRATEGISTA DE RETENÇÃO
Analise o briefing completo antes de escrever qualquer cena ou descrição visual.
Seu trabalho termina no arco narrativo; NÃO escreva storyboard nem prompts de imagem.

Crie exatamente três hooks distintos:
1. curiosity: abre uma pergunta ou lacuna específica que o vídeo realmente responde;
2. loss_opportunity: mostra uma perda/oportunidade relevante sem urgência falsa, ameaça ou manipulação;
3. pattern_break: quebra uma suposição ou padrão previsível ligado ao assunto.

Compare os três por especificidade, clareza, credibilidade, relevância e força de abertura.
Escolha um, justifique a decisão e faça a promessa narrativa que o vídeo precisa cumprir.
Desenhe beats em ordem, com tensão de 0 a 5, propósito e payoff esperado.
O último beat pode criar uma ponte natural para o começo (loop), mas nunca force repetição
nem esconda uma resposta apenas para prolongar retenção. Não invente fatos ou promessas.

Retorne SOMENTE JSON válido no contrato:
{{
  "contract_version": "1.0",
  "hook_candidates": [
    {{"type":"curiosity","text":"...","rationale":"..."}},
    {{"type":"loss_opportunity","text":"...","rationale":"..."}},
    {{"type":"pattern_break","text":"...","rationale":"..."}}
  ],
  "selected_hook_type":"curiosity|loss_opportunity|pattern_break",
  "selected_hook":"...",
  "selection_reason":"...",
  "narrative_promise":"...",
  "payoff":"...",
  "ending_loop_bridge":"...",
  "narrative_beats":[
    {{"id":"b1","purpose":"...","tension_level":0,"expected_payoff":"..."}}
  ]
}}

BRIEFING:
{_payload(brief)}
"""


def build_micro_script_prompt(brief, hook_strategy):
    return f"""BRAIN 2 — ROTEIRISTA DE MICRO-RITMO
Receba o hook e o arco aprovados. Transforme-os em narração oral completa.
Não mude a promessa nem contradiga o payoff do estrategista.
O hook escolhido precisa aparecer na primeira unidade falada.

Divida a fala em unidades editoriais preferencialmente entre 2,5 e 3,5 segundos.
Isso é uma heurística, NÃO um limite rígido: frases completas podem ser mais longas
quando a clareza exigir. Não corte raciocínio essencial, não transforme tudo em frases
telegráficas e não escreva uma sequência monótona de slogans.
Remova enchimentos, redundâncias e conectivos vazios. Varie cadência, respiração,
pausas e intensidade. Marque palavras de ênfase sem depender de caixa alta.
A concatenação dos textos dos blocos deve reconstruir full_narration exatamente,
preservando pontuação, ordem e conteúdo. Use português brasileiro falado.

Retorne SOMENTE JSON válido no contrato:
{{
  "contract_version":"1.0",
  "language":"pt-BR",
  "full_narration":"...",
  "blocks":[
    {{
      "id":"m1",
      "text":"...",
      "target_duration_seconds":3.0,
      "narrative_function":"hook|setup|development|contrast|reveal|payoff|cta|loop_bridge",
      "vocal_intent":"...",
      "emphasis_terms":["..."],
      "pause_after_seconds":0.2
    }}
  ]
}}

BRIEFING:
{_payload(brief)}

ESTRATÉGIA APROVADA:
{_payload(hook_strategy)}
"""


def build_visual_direction_prompt(brief, hook_strategy, micro_script):
    return f"""BRAIN 3 — DIRETOR DE FOTOGRAFIA E METÁFORA VISUAL
Leia o roteiro inteiro e a estratégia antes de propor qualquer cena.
Crie uma bíblia visual única para este vídeo: paleta, linguagem de luz, lentes/enquadramento,
textura, regras de composição e continuidade. Unidade estética NÃO significa repetir
pessoas, objetos, enquadramentos ou ambientes.

Para cada bloco m1...mn, crie exatamente um beat visual correspondente.
Não ilustre substantivos de forma literal por reflexo. Traduza a intenção da fala em uma
metáfora cinematográfica clara, filmável e semanticamente conectada. Uma imagem bonita
sem relação compreensível com a ideia é inválida.
Descreva ação observável, sujeito, ambiente, desenho de plano, movimento de câmera e
nota de continuidade. A ação precisa ser visualmente legível; não substitua ação por
adjetivos abstratos ou movimento de câmera.
Escolha a rota mais apropriada por beat:
stock_video, ai_image_motion, parallax_2_5d, overlay, motion_graphics, ai_video ou user_media.
Não escolha ai_video por padrão. Use parallax somente quando a imagem/segmentação permitir
profundidade confiável; overlay apenas quando o asset/licença/alpha forem adequados.
Mantenha uma paleta e gramática de fotografia consistentes, mas faça as cenas evoluírem.

Retorne SOMENTE JSON válido no contrato:
{{
  "contract_version":"1.0",
  "visual_bible":{{
    "palette":"...",
    "lighting_language":"...",
    "lens_language":"...",
    "texture":"...",
    "composition_rules":"...",
    "continuity_rules":"..."
  }},
  "beats":[
    {{
      "block_id":"m1",
      "spoken_intent":"...",
      "emotion":"...",
      "metaphor":"...",
      "visible_action":"...",
      "subject":"...",
      "environment":"...",
      "shot_design":"...",
      "camera_move":"...",
      "continuity_note":"...",
      "media_route":"stock_video|ai_image_motion|parallax_2_5d|overlay|motion_graphics|ai_video|user_media"
    }}
  ]
}}

BRIEFING:
{_payload(brief)}

ESTRATÉGIA:
{_payload(hook_strategy)}

ROTEIRO EM BLOCOS:
{_payload(micro_script)}
"""


def build_edit_timeline_prompt(micro_script, visual_direction, narration_audio, word_timestamps):
    return f"""BRAIN 4 — EDITOR DE RITMO E SINCRONIZAÇÃO
A narração final já foi gerada. Trabalhe sobre o áudio medido e os timestamps fornecidos.
Não reescreva falas, não invente duração e NÃO crie timestamps que não estejam sustentados
pelos dados de alinhamento.

Escolha âncoras de edição que reforcem mudança de ideia, palavra-chave, revelação ou ação
visual. Cortes não precisam ocorrer em toda palavra. Prefira limites naturais e momentos
de ênfase. Se houver somente alinhamento por palavra, registre word e use um item por palavra individual.
Não converta um segmento que contém várias palavras em word-level. Se houver saída de caracteres,
registre character. Só registre phoneme quando houver tempos fonêmicos explícitos.
Não afirme sincronismo por fonema/sílaba sem essa evidência. Se não houver evidência
fonética, não invente sílaba tônica. Não invente nem estime confidence: preserve esse campo
somente quando o próprio alinhador o fornecer.
Whoosh, bass e outros SFX são discretos e seletivos; silêncio também é decisão editorial.
Sincronize captions e mixagem com a fala, preserve inteligibilidade e preveja ducking da
música sob a voz. Se houver loop intencional, avalie a continuidade entre último e primeiro beat.

Retorne SOMENTE JSON válido no contrato:
{{
  "contract_version":"1.0",
  "audio_asset_id":"...",
  "alignment_method":"...",
  "alignment_level":"word|character|phoneme",
  "audio_duration_seconds":0.0,
  "word_timestamps":[
    {{"text":"...","start_seconds":0.0,"end_seconds":0.2}}
  ],
  "character_timestamps":[],
  "phoneme_timestamps":[],
  "edit_anchors":[
    {{
      "block_id":"m1",
      "trigger_text":"...",
      "at_seconds":0.0,
      "alignment_level":"word|character|phoneme",
      "character":"optional only with character-level evidence",
      "phoneme":"optional only with phoneme-level evidence",
      "visual_event":"...",
      "sfx":null
    }}
  ],
  "caption_events":[
    {{
      "id":"caption-1",
      "start_seconds":0.0,
      "end_seconds":2.5,
      "text":"...",
      "position":"bottom",
      "words":[
        {{"text":"...","start_seconds":0.0,"end_seconds":0.4,"emphasis":false}}
      ]
    }}
  ],
  "sfx_events":[
    {{"id":"sfx-1","asset_path":"...","start_seconds":1.2,"duration_seconds":0.8,"volume":0.25}}
  ],
  "audio_mix_events":[
    {{"start_seconds":0.0,"end_seconds":2.5,"music_volume":0.06,"fade_in_seconds":0.12,"fade_out_seconds":0.12}}
  ]
}}

ROTEIRO:
{_payload(micro_script)}

DIREÇÃO VISUAL:
{_payload(visual_direction)}

ÁUDIO FINAL:
{_payload(narration_audio)}

TIMESTAMPS FORNECIDOS PELO ALINHADOR:
{_payload({"word_timestamps": word_timestamps})}
"""
