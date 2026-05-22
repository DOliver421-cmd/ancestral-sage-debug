"""
Multilingual Course System
Spanish, English, and high-percentage construction field languages.
"""

# Primary languages for construction workforce
COURSE_LANGUAGES = {
    "en": "English",
    "es": "Español",
    "pt": "Português (Brazilian)",
    "fr": "Français",
}

# Course content in multiple languages
ONLINE_LABS_MULTILINGUAL = {
    "basic-circuit-sim": {
        "en": {
            "title": "Basic Circuit Builder",
            "summary": "Build series and parallel resistor networks and solve for total resistance, current, and voltage drops.",
            "objectives": [
                "Calculate total resistance of series and parallel networks",
                "Apply Ohm's Law to find circuit current",
                "Compute voltage drop across each resistor",
            ],
            "safety": ["This is a simulation — always verify de-energized on real circuits."],
        },
        "es": {
            "title": "Constructor Básico de Circuitos",
            "summary": "Construye redes de resistores en serie y paralelo y resuelve la resistencia total, corriente y caídas de voltaje.",
            "objectives": [
                "Calcular la resistencia total de redes en serie y paralelo",
                "Aplicar la Ley de Ohm para encontrar la corriente del circuito",
                "Computar la caída de voltaje en cada resistor",
            ],
            "safety": ["Esta es una simulación — siempre verifica desenergizado en circuitos reales."],
        },
        "pt": {
            "title": "Construtor Básico de Circuitos",
            "summary": "Construa redes de resistores em série e paralelo e resolva resistência total, corrente e quedas de tensão.",
            "objectives": [
                "Calcular a resistência total de redes em série e paralelo",
                "Aplicar a Lei de Ohm para encontrar a corrente do circuito",
                "Calcular a queda de tensão em cada resistor",
            ],
            "safety": ["Esta é uma simulação — sempre verifique desenergizado em circuitos reais."],
        },
    },
    "switch-wiring-sim": {
        "en": {
            "title": "Switch & Receptacle Wiring",
            "summary": "Identify correct conductor connections for single-pole, 3-way, and duplex receptacle installations.",
            "objectives": [
                "Identify hot, neutral, and ground terminals",
                "Wire a single-pole switch loop correctly",
                "Recognize miswires that cause shock or short circuits",
            ],
            "safety": ["Real receptacles must be wired de-energized and ground-continuity tested."],
        },
        "es": {
            "title": "Cableado de Interruptores y Receptáculos",
            "summary": "Identifica las conexiones correctas de conductores para instalaciones de receptáculos de un polo, de 3 vías y dobles.",
            "objectives": [
                "Identificar terminales calientes, neutros y de tierra",
                "Cablear correctamente un bucle de interruptor de un polo",
                "Reconocer conexiones incorrectas que causan choques o cortocircuitos",
            ],
            "safety": ["Los receptáculos reales deben cablearse desenergizados y probarse continuidad de tierra."],
        },
        "pt": {
            "title": "Fiação de Interruptores e Receptáculos",
            "summary": "Identifique as conexões corretas de condutores para instalações de receptáculos de uma via, 3 vias e duplos.",
            "objectives": [
                "Identificar terminais quentes, neutros e aterrados",
                "Cabear corretamente um circuito de interruptor de uma via",
                "Reconhecer fiações incorretas que causam choques ou curtos-circuitos",
            ],
            "safety": ["Receptáculos reais devem ser cabeados desenergizados e testados para continuidade de aterramento."],
        },
    },
    "panel-labeling-sim": {
        "en": {
            "title": "Breaker Panel Labeling",
            "summary": "Label each breaker slot in a residential panel based on the provided branch circuit list.",
            "objectives": [
                "Map branch circuits to breaker positions",
                "Follow NEC 408.4 legibility requirements",
                "Balance loads across phases",
            ],
            "safety": ["Panel covers off = energized bus exposed. PPE and distance rules apply on real panels."],
        },
        "es": {
            "title": "Etiquetado de Panel de Disyuntores",
            "summary": "Etiqueta cada ranura de disyuntor en un panel residencial según la lista de circuitos de rama proporcionada.",
            "objectives": [
                "Mapear circuitos de rama a posiciones de disyuntor",
                "Seguir los requisitos de legibilidad NEC 408.4",
                "Equilibrar cargas en fases",
            ],
            "safety": ["Cubiertas de panel abiertas = bus energizado expuesto. Las reglas de EPP y distancia se aplican en paneles reales."],
        },
        "pt": {
            "title": "Rotulagem do Painel de Disjuntores",
            "summary": "Rotule cada slot de disjuntor em um painel residencial com base na lista de circuitos de ramo fornecida.",
            "objectives": [
                "Mapear circuitos de ramo para posições de disjuntor",
                "Seguir os requisitos de legibilidade NEC 408.4",
                "Equilibrar cargas em fases",
            ],
            "safety": ["Capas do painel abertas = barramento energizado exposto. Regras de EPI e distância se aplicam em painéis reais."],
        },
    },
    "conduit-bending-calc": {
        "en": {
            "title": "Conduit Bending Angle Calculator",
            "summary": "Compute shrink, gain, and developed length for offsets and saddles in EMT.",
            "objectives": [
                "Calculate shrink per inch of rise for standard bend angles",
                "Determine distance between marks for an offset",
                "Pick the right bend angle for the obstacle",
            ],
            "safety": ["Deburr every cut end; support within 3 ft of every box on real installs."],
        },
        "es": {
            "title": "Calculadora de Ángulo de Doblado de Conducto",
            "summary": "Calcula contracción, ganancia y longitud desarrollada para compensaciones y sillas de montar en EMT.",
            "objectives": [
                "Calcular contracción por pulgada de levantamiento para ángulos de curvatura estándar",
                "Determinar la distancia entre marcas para una compensación",
                "Elegir el ángulo de curvatura correcto para el obstáculo",
            ],
            "safety": ["Desbarba cada extremo cortado; soporta dentro de 3 pies de cada caja en instalaciones reales."],
        },
        "pt": {
            "title": "Calculadora de Ângulo de Flexão de Conduíte",
            "summary": "Calcula encolhimento, ganho e comprimento desenvolvido para compensações e selas em EMT.",
            "objectives": [
                "Calcular encolhimento por polegada de levantamento para ângulos de curvatura padrão",
                "Determinar a distância entre marcas para uma compensação",
                "Escolher o ângulo de curvatura correto para o obstáculo",
            ],
            "safety": ["Remova rebarbas em cada extremidade cortada; suporte dentro de 3 pés de cada caixa em instalações reais."],
        },
    },
    "voltage-drop-calc": {
        "en": {
            "title": "Voltage Drop Calculator",
            "summary": "Verify conductor size selection using the NEC voltage-drop formula for one-way feeders and branch circuits.",
            "objectives": [
                "Apply Vdrop = 2·K·I·L / CM formula for single-phase",
                "Select a conductor that keeps drop ≤ 3% on branch circuits",
                "Understand K values for Cu and Al",
            ],
            "safety": ["Low voltage drop protects motors and electronics from damage."],
        },
        "es": {
            "title": "Calculadora de Caída de Voltaje",
            "summary": "Verifica la selección de tamaño de conductor usando la fórmula de caída de voltaje NEC para alimentadores unidireccionales y circuitos de rama.",
            "objectives": [
                "Aplicar fórmula Vdrop = 2·K·I·L / CM para monofásico",
                "Seleccionar un conductor que mantenga caída ≤ 3% en circuitos de rama",
                "Comprender valores de K para Cu y Al",
            ],
            "safety": ["La baja caída de voltaje protege motores y electrónica del daño."],
        },
        "pt": {
            "title": "Calculadora de Queda de Tensão",
            "summary": "Verifique a seleção de tamanho de condutor usando a fórmula de queda de tensão NEC para alimentadores unidirecionais e circuitos de ramo.",
            "objectives": [
                "Aplicar fórmula Vdrop = 2·K·I·L / CM para monofásico",
                "Selecionar um condutor que mantenha queda ≤ 3% em circuitos de ramo",
                "Entender valores de K para Cu e Al",
            ],
            "safety": ["A baixa queda de tensão protege motores e eletrônicos de danos."],
        },
    },
    "safety-ppe": {
        "en": {
            "title": "Safety & PPE Fundamentals",
            "summary": "Learn hazard recognition, NFPA 70E compliance, LOTO procedures, and proper PPE selection.",
            "objectives": [
                "Recognize electrical hazards and arc flash risk",
                "Select appropriate PPE for voltage levels",
                "Apply LOTO (Lockout/Tagout) procedures",
                "Understand NFPA 70E safety standards",
            ],
            "safety": ["Safety violations can be fatal. Never take shortcuts."],
        },
        "es": {
            "title": "Fundamentos de Seguridad y EPP",
            "summary": "Aprende reconocimiento de peligros, cumplimiento NFPA 70E, procedimientos LOTO y selección adecuada de EPP.",
            "objectives": [
                "Reconocer peligros eléctricos y riesgos de arco eléctrico",
                "Seleccionar EPP apropiado para niveles de voltaje",
                "Aplicar procedimientos LOTO (Bloqueo/Etiquetado)",
                "Comprender los estándares de seguridad NFPA 70E",
            ],
            "safety": ["Las violaciones de seguridad pueden ser fatales. Nunca tomes atajos."],
        },
        "pt": {
            "title": "Fundamentos de Segurança e EPI",
            "summary": "Aprenda reconhecimento de perigos, conformidade NFPA 70E, procedimentos LOTO e seleção apropriada de EPI.",
            "objectives": [
                "Reconhecer perigos elétricos e risco de arco elétrico",
                "Selecionar EPI apropriado para níveis de tensão",
                "Aplicar procedimentos LOTO (Bloqueio/Etiquetagem)",
                "Entender os padrões de segurança NFPA 70E",
            ],
            "safety": ["Violações de segurança podem ser fatais. Nunca corte atalhos."],
        },
    },
    "tools-equipment": {
        "en": {
            "title": "Tools & Equipment Inspection",
            "summary": "Proper use, inspection, and maintenance of electrician tools, multimeters, and testing equipment.",
            "objectives": [
                "Inspect tools for damage and safety",
                "Use multimeters safely and correctly",
                "Maintain equipment for longevity",
                "Recognize when tools need replacement",
            ],
            "safety": ["Damaged tools are dangerous tools. Inspect before every use."],
        },
        "es": {
            "title": "Inspección de Herramientas y Equipos",
            "summary": "Uso adecuado, inspección y mantenimiento de herramientas de electricista, multímetros y equipos de prueba.",
            "objectives": [
                "Inspeccionar herramientas para daño y seguridad",
                "Usar multímetros de forma segura y correcta",
                "Mantener equipos para durabilidad",
                "Reconocer cuándo las herramientas necesitan reemplazo",
            ],
            "safety": ["Las herramientas dañadas son herramientas peligrosas. Inspecciona antes de cada uso."],
        },
        "pt": {
            "title": "Inspeção de Ferramentas e Equipamentos",
            "summary": "Uso adequado, inspeção e manutenção de ferramentas de eletricista, multímetros e equipamento de teste.",
            "objectives": [
                "Inspecionar ferramentas para danos e segurança",
                "Usar multímetros com segurança e corretamente",
                "Manter equipamento para longevidade",
                "Reconhecer quando ferramentas precisam ser substituídas",
            ],
            "safety": ["Ferramentas danificadas são ferramentas perigosas. Inspecione antes de cada uso."],
        },
    },
    "troubleshooting": {
        "en": {
            "title": "Troubleshooting Logic",
            "summary": "Systematic fault isolation, continuity and voltage testing, and logical problem-solving.",
            "objectives": [
                "Use systematic troubleshooting approach",
                "Test continuity safely",
                "Measure voltage correctly",
                "Isolate faults logically",
            ],
            "safety": ["Always assume circuits are live until proven otherwise."],
        },
        "es": {
            "title": "Lógica de Resolución de Problemas",
            "summary": "Aislamiento sistemático de fallas, pruebas de continuidad y voltaje, y resolución lógica de problemas.",
            "objectives": [
                "Usar enfoque sistemático de resolución de problemas",
                "Probar continuidad de forma segura",
                "Medir voltaje correctamente",
                "Aislar fallas lógicamente",
            ],
            "safety": ["Siempre asume que los circuitos están activos hasta que se demuestre lo contrario."],
        },
        "pt": {
            "title": "Lógica de Resolução de Problemas",
            "summary": "Isolamento sistemático de falhas, testes de continuidade e tensão, e resolução de problemas lógica.",
            "objectives": [
                "Usar abordagem sistemática de resolução de problemas",
                "Testar continuidade com segurança",
                "Medir tensão corretamente",
                "Isolar falhas logicamente",
            ],
            "safety": ["Sempre assuma que os circuitos estão energizados até serem comprovados o contrário."],
        },
    },
    "solar-off-grid": {
        "en": {
            "title": "Solar & Off-Grid Systems",
            "summary": "PV sizing, charge controllers, battery banks, and inverter installation and safety.",
            "objectives": [
                "Size PV arrays correctly",
                "Select and program charge controllers",
                "Design battery bank systems",
                "Install inverters safely",
            ],
            "safety": ["DC systems can be extremely dangerous. Respect the voltage and amperage."],
        },
        "es": {
            "title": "Sistemas Solares y Fuera de la Red",
            "summary": "Dimensionamiento de PV, controladores de carga, bancos de baterías e instalación segura de inversores.",
            "objectives": [
                "Dimensionar matrices de PV correctamente",
                "Seleccionar y programar controladores de carga",
                "Diseñar sistemas de banco de baterías",
                "Instalar inversores de forma segura",
            ],
            "safety": ["Los sistemas DC pueden ser extremadamente peligrosos. Respeta el voltaje y amperaje."],
        },
        "pt": {
            "title": "Sistemas Solares e Fora da Rede",
            "summary": "Dimensionamento de PV, controladores de carga, bancos de bateria e instalação segura de inversores.",
            "objectives": [
                "Dimensionar matrizes de PV corretamente",
                "Selecionar e programar controladores de carga",
                "Projetar sistemas de banco de bateria",
                "Instalar inversores com segurança",
            ],
            "safety": ["Sistemas DC podem ser extremamente perigosos. Respeite a tensão e amperagem."],
        },
    },
}

# UI strings in multiple languages
UI_STRINGS = {
    "en": {
        "select_language": "Select Language",
        "course_library": "Course Library",
        "start_course": "Start Course",
        "complete_course": "Complete Course",
        "certification": "Certification",
        "team_members": "Team Members",
        "progress": "Progress",
        "time_spent": "Time Spent",
        "score": "Score",
        "license_tier": "License Tier",
        "seats_available": "Seats Available",
        "view_certificate": "View Certificate",
        "download_certificate": "Download Certificate",
        "share_certificate": "Share on LinkedIn",
    },
    "es": {
        "select_language": "Seleccionar Idioma",
        "course_library": "Biblioteca de Cursos",
        "start_course": "Iniciar Curso",
        "complete_course": "Completar Curso",
        "certification": "Certificación",
        "team_members": "Miembros del Equipo",
        "progress": "Progreso",
        "time_spent": "Tiempo Dedicado",
        "score": "Puntuación",
        "license_tier": "Nivel de Licencia",
        "seats_available": "Asientos Disponibles",
        "view_certificate": "Ver Certificado",
        "download_certificate": "Descargar Certificado",
        "share_certificate": "Compartir en LinkedIn",
    },
    "pt": {
        "select_language": "Selecionar Idioma",
        "course_library": "Biblioteca de Cursos",
        "start_course": "Iniciar Curso",
        "complete_course": "Completar Curso",
        "certification": "Certificação",
        "team_members": "Membros da Equipe",
        "progress": "Progresso",
        "time_spent": "Tempo Gasto",
        "score": "Pontuação",
        "license_tier": "Nível de Licença",
        "seats_available": "Assentos Disponíveis",
        "view_certificate": "Ver Certificado",
        "download_certificate": "Baixar Certificado",
        "share_certificate": "Compartilhar no LinkedIn",
    },
}

def get_course_content(lab_slug: str, language: str = "en") -> dict:
    """Get course content in requested language, fall back to English if unavailable"""
    if lab_slug not in ONLINE_LABS_MULTILINGUAL:
        return None

    lab = ONLINE_LABS_MULTILINGUAL[lab_slug]

    if language in lab:
        return lab[language]

    # Fallback to English
    return lab.get("en", None)

def get_ui_string(key: str, language: str = "en") -> str:
    """Get UI string in requested language"""
    if language not in UI_STRINGS:
        language = "en"

    return UI_STRINGS[language].get(key, key)
