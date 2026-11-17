"""Internal visual style library for NEXUS. Technical art direction is never exposed in the UI."""

_STYLE_ROWS = [
  [
    "Quântico & Cósmico",
    "Universo, manifestação e geometria luminosa.",
    "cinematic cosmic surrealism, deep space nebula, sacred geometry, golden light",
    "deep indigo, midnight blue, violet, restrained gold",
    "volumetric rays, luminous nebula backlight, controlled bloom, readable silhouettes",
    "monumental wides, human silhouettes, slow orbital moves, measured push-ins",
    "cosmic dust, layered nebula clouds, subtle sacred geometry",
    "Humanos em relação à vastidão do cosmos; caminhos de luz e padrões geométricos devem representar a ideia narrada. Linguagem sofisticada de ficção científica, com metáforas claras e escala cinematográfica.",
    "horoscope graphics, random equations, busy HUD, rainbow galaxies, generic stars, alegações de prova científica",
    "spaceship",
    [
      "#11152f",
      "#d9b4ff",
      "#3b3975"
    ]
  ],
  [
    "Sonho Lúcido",
    "Surrealismo, subconsciente e realidades paralelas.",
    "cinematic lucid dream surrealism, impossible architecture, floating clocks, infinite mirrors",
    "midnight blue, lavender, pearl, desaturated teal, amber",
    "soft sunlight through haze, dreamlike shafts, reflective highlights",
    "slow dolly through impossible spaces, deliberate reveals, uncanny symmetry",
    "thin mist, glass reflections, floating dust, cloud layers",
    "Um elemento impossível por cena — escadas nas nuvens, portas repetidas, relógios suspensos ou espelhos para outro espaço. O elemento surreal precisa expressar o trecho narrado, não decorar aleatoriamente.",
    "random collages, melting faces, childish fantasy, visual glitches, kaleidoscope excess",
    "surreal",
    [
      "#26213f",
      "#c4a7ff",
      "#756b9b"
    ]
  ],
  [
    "Dark Psychology",
    "Psicologia sombria, sombra e tensão interior.",
    "neo noir psychological thriller, chiaroscuro, solitary silhouette, cold blue amber",
    "near-black, graphite, cold navy, steel blue, restrained amber",
    "hard chiaroscuro, narrow practical lights, rim lighting, detailed shadows",
    "controlled close-ups, over-shoulder, negative space, slow push-ins",
    "subtle grain, rain on glass, tactile concrete and dark wood",
    "Mostrar conflito interno por comportamento humano concreto: confronto com o espelho, hesitação, isolamento, decisão difícil. Psicologia realista e ambiguidade; luz e composição carregam a tensão.",
    "gore, demonic clichés, hooded hackers, red eyes, sensational manipulation, crushed blacks",
    "detective",
    [
      "#10141d",
      "#a9b8d4",
      "#39475d"
    ]
  ],
  [
    "Épico Espiritual",
    "Despertar, propósito e escala monumental.",
    "epic spiritual cinematic scale, monumental ancient temple, vast desert, golden dust",
    "sandstone, bronze, muted gold, umber, twilight violet",
    "golden-hour sun, volumetric beams, atmospheric haze",
    "extreme wide shots, slow crane/aerial reveals, tiny human figures",
    "windblown sand, weathered stone, drifting dust",
    "Expressar despertar e propósito com arquitetura monumental, paisagens vastas, viajantes e limiares. A escala épica precisa servir à mensagem e manter plausibilidade física.",
    "imposed religious icons, game castles, random planets, lens flare excess, landscape filler",
    "castle",
    [
      "#292238",
      "#e8c47a",
      "#826c55"
    ]
  ],
  [
    "Aura Neon",
    "Energia, chakras e experiências meditativas.",
    "bioluminescent energy art, cyan violet golden aura, glowing waveforms, black background",
    "black, electric cyan, ultraviolet, indigo, balanced gold",
    "self-illuminated forms, neon edge light, controlled glow",
    "slow macro pushes, symmetry, fluid lateral and orbital motion",
    "bioluminescent filaments, particles, translucent energy waves",
    "Traduzir estados internos em formas luminosas elegantes ou silhuetas humanas com campos de luz. Usar cores de chakras apenas quando pertinentes; variar as soluções visuais.",
    "cheap chakra charts, rainbow gradients everywhere, nightclub, neon clutter, pseudo-science as fact",
    "neon_city",
    [
      "#10172a",
      "#55e7f2",
      "#6d43a0"
    ]
  ],
  [
    "Hermetismo Clássico",
    "Filosofia antiga, simbolismo e sabedoria.",
    "classical baroque oil painting, Rembrandt chiaroscuro, hermetic symbolism, antique library",
    "burnt umber, deep brown, antique gold, olive black, parchment",
    "candle/window source, Rembrandt chiaroscuro, warm highlights",
    "painterly frames, slow push-ins, still-life inserts, classical geometry",
    "oil brushwork, aged canvas, carved wood, parchment, patinated metal",
    "Evocar pintura histórica de museu. Usar estudiosos, manuscritos, instrumentos e objetos simbólicos discretos quando sustentarem a fala; símbolos integrados ao cenário, nunca adesivos gráficos.",
    "random occult sigils, wizard props, modern objects, fake readable text, excessive gold, symbolism as scientific evidence",
    "watch",
    [
      "#211a17",
      "#d5ad68",
      "#6d5140"
    ]
  ],
  [
    "Visual ASMR / Hipnótico",
    "Macro, fluidos e estímulo visual sensorial.",
    "hypnotic macro cinematography, molten liquid gold, fluid dynamics, neon ink, dark water",
    "black, liquid gold, violet, cyan, selective pigments",
    "precise specular highlights, glossy reflections, backlit fluids",
    "extreme macro, smooth tracking, slow motion, stable compositions",
    "viscous liquid, metallic surfaces, pigment diffusion, bubbles, ripples",
    "Um evento físico hipnótico por cena: metal líquido, tinta difundindo, gotas colidindo, pigmento em espiral. Usar como pontuação sensorial ou abstração pertinente, não como substituto de toda a narrativa.",
    "kaleidoscope loops, abstract filler, impossible physics, repeated gold liquid, flashing/strobing",
    "droplet",
    [
      "#11151c",
      "#e4c46f",
      "#5945a1"
    ]
  ],
  [
    "Cinematográfico",
    "Fotografia de cinema realista e versátil.",
    "cinematic realistic film still, natural motivated light, 35mm lens, shallow depth of field",
    "natural restrained colors, balanced skin tones, warm-cool contrast",
    "motivated natural/practical light, soft directional key",
    "24–50mm perspective, intentional medium/wide shots, restrained dolly/handheld",
    "organic grain, realistic skin/materials, subtle atmospheric depth",
    "Live-action convincente, ambientes autênticos, performance natural. Escolher lente, enquadramento e movimento para apoiar a ação e variar composições com continuidade.",
    "plastic CGI, excessive teal-orange, artificial flares, generic stock poses, fake text",
    "mountain",
    [
      "#182638",
      "#d59b58",
      "#526b78"
    ]
  ],
  [
    "Dark Cinematográfico",
    "Cinema dramático com sombras profundas.",
    "dark cinematic film still, deep shadows, dramatic rim light, moody atmosphere",
    "charcoal, midnight blue, desaturated green, restrained amber/cold white",
    "low-key, practical sources, rim light, preserved shadow detail",
    "measured push-ins, silhouettes, selective close-ups, layered frames",
    "subtle grain, motivated haze/rain/smoke",
    "Ambientes realistas com registro emocional escuro. O sujeito e a ação permanecem legíveis; escuridão direciona o olhar, não esconde a cena.",
    "underexposure, horror clichés, constant smoke, crushed blacks, arbitrary neon",
    "silhouette",
    [
      "#101522",
      "#8b76a8",
      "#30384f"
    ]
  ],
  [
    "Ilustração Editorial",
    "Metáforas visuais e arte conceitual sofisticada.",
    "premium editorial illustration, conceptual visual metaphor, refined graphic shapes",
    "limited 3–5 color palette, deliberate accent",
    "illustrative tonal modeling, clean separation, negative space",
    "graphic composition, strong silhouette, clear hierarchy",
    "paper grain, screenprint or painterly digital texture",
    "Converter ideias abstratas em uma metáfora imediatamente compreensível, com linguagem de capa de revista sofisticada e poucos detalhes bem escolhidos.",
    "clip-art, generic icons, school infographic, text-heavy poster, inconsistent technique",
    "editorial",
    [
      "#e4d6b9",
      "#d78b63",
      "#63818a"
    ]
  ],
  [
    "Filme Noir",
    "Mistério, contraste e linguagem noir clássica.",
    "classic film noir cinematography, black and white, hard side light, venetian blind shadows",
    "monochrome black, charcoal, silver, nuanced gray",
    "hard directional light, long shadows, silhouettes, pools of practical light",
    "low angles, reflective surfaces, door frames, deliberate close-ups",
    "silver-gelatin grain, wet pavement, motivated smoke",
    "Linguagem noir clássica para segredo, tensão moral, isolamento e escolhas difíceis. Cues de época apenas quando coerentes; não transformar tudo em história de detetive.",
    "color neon, cyberpunk, fedora clichés, unreadable darkness, random crime props",
    "detective",
    [
      "#101319",
      "#d6d1c5",
      "#454b56"
    ]
  ],
  [
    "Aquarela Artística",
    "Pintura delicada, orgânica e contemplativa.",
    "fine art watercolor illustration, translucent pigment washes, organic paper texture",
    "muted pigments, watercolor transparency, warm paper white",
    "soft diffuse light, luminous paper, gentle transitions",
    "illustrative framing, breathing room, clear focal point",
    "pigment blooms, granulation, paper fibers, wet-on-wet edges",
    "Cena reconhecível em aquarela refinada. Preservar sujeito e ação enquanto as lavagens e bordas pigmentadas criam atmosfera; manter papel e pincel consistentes.",
    "photorealistic inserts, muddy colors, splashes hiding subjects, childish clip-art",
    "vase",
    [
      "#c4d9d2",
      "#edc58e",
      "#8aaeb1"
    ]
  ],
  [
    "Fantasia Cinematográfica",
    "Fantasia imersiva com escala e encantamento.",
    "cinematic fantasy film still, atmospheric magical realism, ancient worlds, volumetric glow",
    "earthy natural colors, deep teal, forest green, muted violet, gold",
    "motivated moonlight/firelight, magical practical glow, volumetric beams",
    "immersive wides, character-led tracking, revealing moves, depth",
    "weathered stone, organic landscapes, mist, embers, tactile costumes",
    "Mundo de fantasia crível, com regras visuais consistentes. Elementos mágicos têm propósito narrativo; priorizar lugares tangíveis e ações de personagens em vez de espetáculo decorativo.",
    "generic game art, random dragons/castles, particle excess, cartoon proportions",
    "castle",
    [
      "#29264c",
      "#f0c16e",
      "#78689d"
    ]
  ],
  [
    "Graphic Novel",
    "Narrativa ilustrada, traço forte e impacto.",
    "premium graphic novel illustration, expressive ink linework, dramatic shadow blocks",
    "limited dramatic palette, ink black, warm paper, accent colors",
    "graphic chiaroscuro, hard-edged shadows, strong silhouettes",
    "dynamic perspective, expressive angles, single-frame storytelling",
    "ink hatching, brush strokes, restrained halftone, paper texture",
    "Uma ilustração cinematográfica completa por cena, não uma página de quadrinhos. Ação clara, linguagem de traço e design de personagens consistentes.",
    "comic panels, speech bubbles, captions, lettering, sound effects, collage",
    "comic",
    [
      "#252b38",
      "#e5b44f",
      "#a94d50"
    ]
  ],
  [
    "Minimalista Clean",
    "Composição limpa, elegante e essencial.",
    "minimalist clean visual composition, uncluttered frame, refined neutral palette",
    "soft neutrals, off-white, stone, muted gray, one accent",
    "soft diffused light, gentle shadows, clean separation",
    "restrained movement, negative space, precise subject placement",
    "matte surfaces, subtle natural materials, low visual noise",
    "Reduzir a imagem ao mínimo necessário para comunicar a cena. Espaço negativo e hierarquia clara sem remover ação humana ou contexto significativo.",
    "empty decorative frames, generic gradients, excess props, tiny subjects, UI mockups, text overlays",
    "vase",
    [
      "#dce5e8",
      "#f2c987",
      "#9bb1b8"
    ]
  ],
  [
    "Realismo Humano Emocional",
    "Pessoas reais, emoções e transformação cotidiana.",
    "cinematic emotional human realism, authentic candid portrait, natural performance",
    "natural skin tones, warm neutrals, earthy colors, gentle cool shadows",
    "window light, practical lamps, soft backlight, believable exposure",
    "intimate close-ups, observational medium shots, eye-level, subtle handheld",
    "real skin, natural imperfections, tactile clothing, lived-in spaces",
    "Pessoas verossímeis expressando emoções por gestos específicos: hesitar, aliviar-se, concentrar-se, refletir, conectar-se, decidir. Atuação contida, diversidade de pessoas e ambientes.",
    "plastic retouching, stock smiles, staged handshakes, melodrama, uncanny faces, anonymous same person",
    "silhouette",
    [
      "#302b2a",
      "#e6b18a",
      "#6f7779"
    ]
  ],
  [
    "Reconstituição Histórica",
    "Épocas, personagens e ambientes historicamente coerentes.",
    "historical period cinematic reconstruction, authentic architecture, period costume",
    "period-appropriate muted pigments, natural dyes, aged wood, stone, bronze",
    "firelight, candlelight, window daylight, plausible practical sources",
    "observational wides, medium character scenes, tactile tool/manuscript inserts",
    "aged paper, worn stone, hand-forged metal, woven fabrics",
    "Reconstrução plausível somente quando roteiro indicar época, pessoa ou contexto. Compatibilizar roupas, ferramentas, arquitetura e materiais. Se houver incerteza, usar referência de época genérica sem inventar fatos específicos.",
    "anachronisms, fantasy armor, fake manuscript text, unsupported likenesses, mixing centuries",
    "watch",
    [
      "#342a24",
      "#c8a36a",
      "#79624c"
    ]
  ],
  [
    "Natureza Contemplativa",
    "Natureza, serenidade e reflexão.",
    "cinematic contemplative nature, misty forest, calm water, golden sunrise",
    "moss green, muted teal, mist gray, sunrise gold, earth tones",
    "soft dawn/dusk, diffused sun, natural haze, gentle reflections",
    "slow stable tracking, landscape reveals, water-level details",
    "moving leaves, ripples, mist, wet stone, natural surface detail",
    "Natureza como ambiente emocional ou metáfora pertinente. Variar locais e movimentos naturais; ligar paisagem à narração. Silhueta humana apenas quando acrescentar sentido.",
    "repeated generic sunsets, fantasy glowing forests, oversaturated greens, unrelated wallpaper landscapes",
    "waterfall",
    [
      "#193b35",
      "#e6c77b",
      "#668d62"
    ]
  ]
]

STYLE_PROFILES = {
    row[0]: {
        "short": row[1], "search_terms": row[2], "palette": row[3],
        "lighting": row[4], "camera": row[5], "texture": row[6],
        "direction": row[7], "avoid": row[8], "preview_scene": row[9], "ui": tuple(row[10]),
    }
    for row in _STYLE_ROWS
}
STYLE_OPTIONS = list(STYLE_PROFILES)
STYLE_SEARCH_TERMS = {name: p["search_terms"] for name, p in STYLE_PROFILES.items()}
STYLE_META = {name: (*p["ui"], p["short"]) for name, p in STYLE_PROFILES.items()}
STYLE_PREVIEW_SCENES = {name: p["preview_scene"] for name, p in STYLE_PROFILES.items()}


def build_visual_style_directive(style):
    """Build the private, detailed art-direction brief injected into Gemini prompts."""
    profile = STYLE_PROFILES.get(style)
    if not profile:
        raise ValueError(f"Estilo visual não cadastrado: {style}")
    return (
        f"ESTILO VISUAL BLOQUEADO: {style}\n"
        f"IDENTIDADE E INTENÇÃO: {profile['direction']}\n"
        f"PALETA: {profile['palette']}\n"
        f"ILUMINAÇÃO: {profile['lighting']}\n"
        f"FOTOGRAFIA E COMPOSIÇÃO: {profile['camera']}\n"
        f"TEXTURAS E ATMOSFERA: {profile['texture']}\n"
        f"TERMOS PARA BUSCA: {profile['search_terms']}\n"
        f"EVITAR: {profile['avoid']}\n"
        "CONTINUIDADE: mantenha a identidade artística em todas as cenas, variando "
        "pessoas, ambientes, planos, ações e enquadramentos. O estilo nunca substitui "
        "a correspondência semântica com a narração. Não inserir texto, legendas, "
        "logotipos ou tipografia nas imagens. Cada cena deve continuar específica "
        "ao trecho narrado."
    )
