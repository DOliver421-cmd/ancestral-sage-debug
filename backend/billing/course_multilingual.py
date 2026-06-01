"""
Multilingual Course System
Spanish, English, and high-percentage construction field languages.
"""

# Primary languages for construction workforce
# Order: English, Spanish, Portuguese, French, Hindi, Arabic, Pashto, Swahili
COURSE_LANGUAGES = {
    "en": "English",
    "es": "Español",
    "pt": "Português (Brazilian)",
    "fr": "Français",
    "hi": "हिन्दी (Hindi)",
    "ar": "العربية (Arabic)",
    "ps": "پشتو (Pashto)",
    "sw": "Kiswahili (Swahili)",
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
        "hi": {
            "title": "बेसिक सर्किट बिल्डर",
            "summary": "सीरीज़ और पैरेलल रेजिस्टर नेटवर्क बनाएं और कुल प्रतिरोध, करंट और वोल्टेज ड्रॉप के लिए हल करें।",
            "objectives": [
                "सीरीज़ और पैरेलल नेटवर्क के कुल प्रतिरोध की गणना करें",
                "सर्किट करंट खोजने के लिए ओम का नियम लागू करें",
                "प्रत्येक रेजिस्टर में वोल्टेज ड्रॉप की गणना करें",
            ],
            "safety": ["यह एक सिमुलेशन है — वास्तविक सर्किट पर हमेशा डिएनर्जाइज़्ड सत्यापित करें।"],
        },
        "ar": {
            "title": "منشئ الدوائر الأساسية",
            "summary": "قم ببناء شبكات المقاومات في سلسلة وتوازي وحل إجمالي المقاومة والتيار وانخفاض الجهد.",
            "objectives": [
                "حساب المقاومة الكلية لشبكات السلسلة والتوازي",
                "تطبيق قانون أوم للعثور على تيار الدائرة",
                "حساب انخفاض الجهد عبر كل مقاوم",
            ],
            "safety": ["هذه محاكاة — تحقق دائماً من إلغاء الطاقة على الدوائر الحقيقية."],
        },
        "ps": {
            "title": "بنیادی سرکٹ جوڑنے والا",
            "summary": "سیریز او پیرلل مقاومت نیٹ ورک بنایں او کل مقاومت، موجودہ او وولٹیج ڈراپ کے لیے حل کریں۔",
            "objectives": [
                "سیریز او پیرلل نیٹ ورک کی کل مقاومت کا حساب کریں",
                "سرکٹ موجودہ تلاش کرنے کے لیے اوہم کا قانون لاگو کریں",
                "ہر مقاومت میں وولٹیج ڈراپ کا حساب کریں",
            ],
            "safety": ["یہ ایک نقل ہے — حقیقی سرکٹس پر ہمیشہ ڈی انرجائز شدہ تصدیق کریں۔"],
        },
        "sw": {
            "title": "Mjenzi wa Saketi Msingi",
            "summary": "Jenga mitandao ya resistor katika safu na sambamba na kutatua kwa jumla ya upinzani, sasa na kushuka kwa voltage.",
            "objectives": [
                "Hesabu upinzani jumla wa mitandao ya safu na sambamba",
                "Tumia Sheria ya Ohm kupata sasa ya saketi",
                "Hesabu kushuka kwa voltage katika kila resistor",
            ],
            "safety": ["Hii ni simulia — kila wakati thibitisha kuwa na nishati kwenye saketi halisi."],
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
        "hi": {
            "title": "स्विच और रिसेप्टेकल वायरिंग",
            "summary": "सिंगल-पोल, 3-वे और डुप्लेक्स रिसेप्टेकल इंस्टॉलेशन के लिए सही कंडक्टर कनेक्शन की पहचान करें।",
            "objectives": [
                "हॉट, न्यूट्रल और ग्राउंड टर्मिनलों की पहचान करें",
                "एक सिंगल-पोल स्विच लूप को सही तरीके से वायर करें",
                "गलत वायरिंग को पहचानें जो शॉक या शॉर्ट सर्किट का कारण बनती है",
            ],
            "safety": ["असली रिसेप्टेकल को डिएनर्जाइज़्ड और ग्राउंड-कंटीन्युटी टेस्ट किया जाना चाहिए।"],
        },
        "ar": {
            "title": "توصيل المفاتيح والمقابس",
            "summary": "حدد التوصيلات الصحيحة للموصلات لتثبيتات المقابس أحادية القطب والثلاثية الاتجاه والمزدوجة.",
            "objectives": [
                "تحديد المحطات الساخنة والمحايدة والمؤرضة",
                "تأسيس حلقة مفتاح أحادي القطب بشكل صحيح",
                "التعرف على الأسلاك الخاطئة التي تسبب الصدمات أو الدوائس القصيرة",
            ],
            "safety": ["يجب توصيل المقابس الحقيقية بدون طاقة واختبار استمرارية التأريض."],
        },
        "ps": {
            "title": "سویچ او سکیٹ وائرنگ",
            "summary": "سنگل پول، 3 طریقہ او ڈپلیکس سکیٹ انسٹالیشن کے لیے صحیح کنڈکٹر جڑان کی شناخت کریں۔",
            "objectives": [
                "گرم، غیر جانبدار او زمین کے ٹرمینلز کی شناخت کریں",
                "سنگل پول سویچ لوپ کو صحیح طریقے سے وائر کریں",
                "غلط وائرنگ کی شناخت کریں جو صدمہ یا قلیل مدتی سرکٹ کا سبب بنتی ہے",
            ],
            "safety": ["حقیقی سکیٹ کو بے جان او زمینی تسلسل ٹیسٹ شدہ ہونا ضروری ہے۔"],
        },
        "sw": {
            "title": "Uunganisho wa Swichi na Receptacle",
            "summary": "Tambua unganisho sahihi la wasiliana kwa uongoza wa pole moja, njia tatu na receptacles mbili.",
            "objectives": [
                "Tambua vituo vya joto, udhaiti na ardhi",
                "Unganisha loop ya swichi ya pole moja kwa usahihi",
                "Tambua kaunti mbaya ambayo husababisha mshtuko au mzunguko mfupi",
            ],
            "safety": ["Receptacles halisi lazima ziwe wired bila umeme na mtihani wa kuendelea kwa ardhi."],
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
        "hi": {
            "title": "ब्रेकर पैनल लेबलिंग",
            "summary": "प्रदान की गई शाखा सर्किट सूची के आधार पर आवासीय पैनल में प्रत्येक ब्रेकर स्लॉट को लेबल करें।",
            "objectives": [
                "शाखा सर्किट को ब्रेकर पदों पर मैप करें",
                "NEC 408.4 पठनीयता आवश्यकताओं का पालन करें",
                "चरणों में भार को संतुलित करें",
            ],
            "safety": ["पैनल कवर बंद = ऊर्जावान बस उजागर। वास्तविक पैनलों पर PPE और दूरी नियम लागू होते हैं।"],
        },
        "ar": {
            "title": "تسمية لوحة القاطع",
            "summary": "قم بتسمية كل فتحة قاطع في اللوحة السكنية بناءً على قائمة الدارات الفرعية المقدمة.",
            "objectives": [
                "تعيين الدارات الفرعية لمواضع القاطع",
                "اتبع متطلبات الوضوح NEC 408.4",
                "موازنة الأحمال عبر الطور",
            ],
            "safety": ["أغطية اللوحة المفتوحة = الناقل المنشط المكشوف. تنطبق قواعد PPE والمسافة على اللوحات الحقيقية."],
        },
        "ps": {
            "title": "بریکر پینل لیبلنگ",
            "summary": "فراہم کردہ شاخ سرکٹ لسٹ کی بنیاد پر رہائشی پینل میں ہر بریکر سلاٹ کو لیبل کریں۔",
            "objectives": [
                "شاخ سرکٹس کو بریکر پوزیشنز سے منسلک کریں",
                "NEC 408.4 وضاحت کی ضروریات کی پیروی کریں",
                "مراحل میں بوجھ متوازن کریں",
            ],
            "safety": ["پینل کوریں کھولیں = ہمراہ ناقل نمائش۔ PPE او فاصلہ کے اصول حقیقی پینلز پر لاگو ہوتے ہیں۔"],
        },
        "sw": {
            "title": "Utengezaji wa Paneli ya Breaker",
            "summary": "Jina kila nafasi ya breaker katika paneli ya makazi kulingana na orodha ya mzunguko wa tawi iliyotolewa.",
            "objectives": [
                "Ramani mizunguko ya tawi kwa nafasi za breaker",
                "Fuata mahitaji ya uwazi wa NEC 408.4",
                "Usawa wa mizigo ya kawaida",
            ],
            "safety": ["Makapu ya paneli ya njiani = basi lililoshangilia linachochezana. Kanuni za PPE na umbali zinatumika kwenye paneli halisi."],
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
        "hi": {
            "title": "नलिका बेंडिंग एंगल कैलकुलेटर",
            "summary": "EMT में ऑफसेट और सैडल के लिए सिकुड़न, लाभ और विकसित लंबाई की गणना करें।",
            "objectives": [
                "मानक बेंडिंग कोण के लिए राइज प्रति इंच सिकुड़न की गणना करें",
                "एक ऑफसेट के लिए अंकों के बीच की दूरी निर्धारित करें",
                "बाधा के लिए सही बेंडिंग कोण चुनें",
            ],
            "safety": ["प्रत्येक कट सिरे को डिबर करें; वास्तविक स्थापन पर प्रत्येक बॉक्स के 3 फीट के भीतर सहायता करें।"],
        },
        "ar": {
            "title": "حاسبة زاوية ثني الأنابيب",
            "summary": "حساب الانكماش والكسب والطول المطور للتعويضات والسرج في EMT.",
            "objectives": [
                "حساب الانكماش لكل بوصة من الارتفاع لزوايا الثني القياسية",
                "تحديد المسافة بين العلامات لعوض",
                "اختر زاوية الثني الصحيحة للعقبة",
            ],
            "safety": ["إزالة الشحوم من كل حافة مقطوعة؛ دعم في 3 أقدام من كل صندوق على التثبيتات الحقيقية."],
        },
        "ps": {
            "title": "نلی بندی زاویہ کیلکولیٹر",
            "summary": "EMT میں آفسیٹ او سیڈل کے لیے سکڑن، حاصل او تیار شدہ لمبائی کا حساب کریں۔",
            "objectives": [
                "معیاری بندی کے زوایے کے لیے اٹھائے فی انچ سکڑن کا حساب کریں",
                "آفسیٹ کے لیے نشانات کے درمیان فاصلہ معین کریں",
                "رکاوٹ کے لیے صحیح بندی کا زاویہ منتخب کریں",
            ],
            "safety": ["ہر کٹ سرے سے نہ کریں؛ حقیقی انسٹالز پر ہر باکس کے 3 فٹ کے اندر سہارا دیں۔"],
        },
        "sw": {
            "title": "Kalkuli ya Pembe ya Kuinama kwa Conduit",
            "summary": "Hesabu kupungua, faida na urefu ulioendelea kwa ficho na sadla katika EMT.",
            "objectives": [
                "Hesabu kupungua kwa kila inchi ya kuinua kwa pembe ya kawaida ya kuinama",
                "Tambua umbali kati ya alama kwa ficho",
                "Chagua pembe ya kuinama sahihi kwa kizuizi",
            ],
            "safety": ["Burr kila kukatwa kumaliziwa; msaada ndani ya miguu 3 ya kila sanduku kwenye uongoza halisi."],
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
        "hi": {
            "title": "वोल्टेज ड्रॉप कैलकुलेटर",
            "summary": "वन-वे फीडर्स और शाखा सर्किट के लिए NEC वोल्टेज-ड्रॉप सूत्र का उपयोग करके कंडक्टर आकार चयन को सत्यापित करें।",
            "objectives": [
                "सिंगल-फेज के लिए Vdrop = 2·K·I·L / CM सूत्र लागू करें",
                "एक कंडक्टर चुनें जो शाखा सर्किट पर ड्रॉप ≤ 3% रखता है",
                "Cu और Al के लिए K मान समझें",
            ],
            "safety": ["कम वोल्टेज ड्रॉप मोटर्स और इलेक्ट्रॉनिक्स को नुकसान से बचाता है।"],
        },
        "ar": {
            "title": "حاسبة انخفاض الجهد",
            "summary": "تحقق من اختيار حجم الموصل باستخدام صيغة انخفاض الجهد NEC للمغذيات أحادية الاتجاه والدارات الفرعية.",
            "objectives": [
                "تطبيق الصيغة Vdrop = 2·K·I·L / CM للأحادي",
                "اختر موصلاً يحافظ على انخفاض ≤ 3٪ على الدارات الفرعية",
                "فهم قيم K للنحاس والألومنيوم",
            ],
            "safety": ["انخفاض الجهد المنخفض يحمي المحركات والإلكترونيات من التلف."],
        },
        "ps": {
            "title": "وولٹیج ڈراپ کیلکولیٹر",
            "summary": "ایک طریقہ فیڈرز او شاخ سرکٹس کے لیے NEC وولٹیج ڈراپ فارمولا استعمال کرتے ہوئے کنڈکٹر سائز انتخاب کی تصدیق کریں۔",
            "objectives": [
                "سنگل فیز کے لیے Vdrop = 2·K·I·L / CM فارمولا لاگو کریں",
                "ایک کنڈکٹر منتخب کریں جو شاخ سرکٹس پر ڈراپ ≤ 3٪ رکھے",
                "Cu او Al کے لیے K اقدار سمجھیں",
            ],
            "safety": ["کم وولٹیج ڈراپ موٹرز او الیکٹرانکس کو نقصان سے بچاتا ہے۔"],
        },
        "sw": {
            "title": "Kalkuli ya Kushuka kwa Voltage",
            "summary": "Thibitisha uteuzi wa ukubwa wa wasiliana kwa kutumia fomula ya kushuka kwa voltage ya NEC kwa wasiliana wa njia moja na mizunguko ya tawi.",
            "objectives": [
                "Tumia fomula Vdrop = 2·K·I·L / CM kwa moja",
                "Chagua wasiliana ambaye huwezi kusimama ≤ 3% kwenye mizunguko ya tawi",
                "Elewa maadili ya K kwa Cu na Al",
            ],
            "safety": ["Kushuka kwa voltage kwa chini kunakulinda injini na elektroniki kutokana na ndhifa."],
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
        "hi": {
            "title": "सुरक्षा और PPE फंडामेंटल्स",
            "summary": "खतरे की पहचान, NFPA 70E अनुपालन, LOTO प्रक्रियाएं और उचित PPE चयन सीखें।",
            "objectives": [
                "विद्युत खतरों और आर्क फ्लैश जोखिम को पहचानें",
                "वोल्टेज स्तरों के लिए उचित PPE चुनें",
                "LOTO (लॉकआउट/टैगआउट) प्रक्रियाएं लागू करें",
                "NFPA 70E सुरक्षा मानकों को समझें",
            ],
            "safety": ["सुरक्षा उल्लंघन घातक हो सकते हैं। कभी भी शॉर्टकट न लें।"],
        },
        "ar": {
            "title": "أساسيات الأمان والمعدات الشخصية",
            "summary": "تعلم تحديد المخاطر والامتثال NFPA 70E وإجراءات LOTO واختيار المعدات الشخصية المناسبة.",
            "objectives": [
                "التعرف على المخاطر الكهربائية وخطر القوس الكهربائي",
                "اختر المعدات الشخصية المناسبة لمستويات الجهد",
                "تطبيق إجراءات LOTO (الإغلاق والعلامات)",
                "فهم معايير الأمان NFPA 70E",
            ],
            "safety": ["انتهاكات الأمان يمكن أن تكون قاتلة. لا تأخذ اختصارات."],
        },
        "ps": {
            "title": "حفاظت او PPE بنیاد",
            "summary": "خطرے کی شناخت، NFPA 70E موافقت، LOTO طریقہ کاری او مناسب PPE انتخاب سیکھیں۔",
            "objectives": [
                "الكهرباء کے خطرات او آرک فلیش خطرے کو پہچانیں",
                "وولٹیج کی سطحوں کے لیے مناسب PPE منتخب کریں",
                "LOTO (بند کریں/ٹیگ کریں) طریقہ کاری لاگو کریں",
                "NFPA 70E حفاظت کے معیارات سمجھیں",
            ],
            "safety": ["حفاظت کی خلاف ورزیاں مہلک ہو سکتی ہیں۔ کبھی بھی شارٹ کٹ نہ لیں۔"],
        },
        "sw": {
            "title": "Misingi ya Usalama na Vifaa vya Ulinzi",
            "summary": "Jifunze kutambua hatari, kufuata NFPA 70E, taratibu za LOTO na uchaguzi sahihi wa vifaa vya ulinzi.",
            "objectives": [
                "Tambua hatari za umeme na hatari ya arc flash",
                "Chagua vifaa vya ulinzi vya ziada kwa viwango vya voltage",
                "Tumia taratibu za LOTO (Kukaramu/Kuandika),",
                "Elewa viwango vya usalama vya NFPA 70E",
            ],
            "safety": ["Uvunjaji wa usalama unaweza kufa. Usichukue njia fupi."],
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
        "hi": {
            "title": "उपकरण और उपकरण निरीक्षण",
            "summary": "बिजली के उपकरण, मल्टीमीटर और परीक्षण उपकरण का उचित उपयोग, निरीक्षण और रखरखाव।",
            "objectives": [
                "नुकसान और सुरक्षा के लिए उपकरण का निरीक्षण करें",
                "मल्टीमीटर का सुरक्षित और सही तरीके से उपयोग करें",
                "दीर्घायु के लिए उपकरण बनाए रखें",
                "पहचानें कि उपकरण को कब बदलने की आवश्यकता है",
            ],
            "safety": ["क्षतिग्रस्त उपकरण खतरनाक उपकरण हैं। प्रत्येक उपयोग से पहले निरीक्षण करें।"],
        },
        "ar": {
            "title": "فحص الأدوات والمعدات",
            "summary": "الاستخدام الصحيح والفحص والصيانة لأدوات كهربائي ومقاييس متعددة ومعدات اختبار.",
            "objectives": [
                "فحص الأدوات للضرر والسلامة",
                "استخدم مقاييس متعددة بأمان وبشكل صحيح",
                "الحفاظ على المعدات طويلة العمر",
                "التعرف على متى تحتاج الأدوات إلى الاستبدال",
            ],
            "safety": ["الأدوات التالفة أدوات خطرة. فحص قبل كل استخدام."],
        },
        "ps": {
            "title": "آلات او سامان کی جانچ",
            "summary": "الکھڑا کے آلات، ملٹی میٹر او ٹیسٹ کرنے والے سامان کا مناسب استعمال، جانچ او دیکھ بھال۔",
            "objectives": [
                "نقصان او حفاظت کے لیے آلات کی جانچ کریں",
                "ملٹی میٹر کو محفوظ طریقے سے او صحیح طریقے سے استعمال کریں",
                "طویل مدتی کے لیے سامان برقرار رکھیں",
                "پہچانیں کہ آلات کو کب بدلنے کی ضرورت ہے",
            ],
            "safety": ["نقصان والے آلات خطرناک آلات ہیں۔ ہر استعمال سے پہلے جانچ کریں۔"],
        },
        "sw": {
            "title": "Ufanyaji wa Njia Kazi na Vifaa",
            "summary": "Matumizi sahihi, ufanyaji na uendeshaji wa zana za umeme, multimeters na vifaa vya mtihani.",
            "objectives": [
                "Fumbia zana kwa ndhifa na usalama",
                "Tumia multimeters kwa usalama na sawasawa",
                "Viongeza vifaa kwa usimu mrefu",
                "Tambua wakati zana zinahitaji kubadilishwa",
            ],
            "safety": ["Zana zilizoharibiwa ni zana zenye hatari. Fumbia kabla ya kila matumizi."],
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
        "hi": {
            "title": "समस्या निवारण तर्क",
            "summary": "व्यवस्थित दोष अलगाव, निरंतरता और वोल्टेज परीक्षण, और तार्किक समस्या समाधान।",
            "objectives": [
                "व्यवस्थित समस्या निवारण दृष्टिकोण का उपयोग करें",
                "सुरक्षित रूप से निरंतरता का परीक्षण करें",
                "वोल्टेज को सही तरीके से मापें",
                "दोषों को तार्किक रूप से अलग करें",
            ],
            "safety": ["हमेशा मान लें कि सर्किट तब तक ऊर्जावान हैं जब तक कि अन्यथा साबित न हो।"],
        },
        "ar": {
            "title": "منطق استكشاف الأخطاء",
            "summary": "عزل الأعطال المنهجي واختبار الاستمرارية والجهد وحل المشاكل المنطقية.",
            "objectives": [
                "استخدم منهج استكشاف الأخطاء المنهجي",
                "اختبر الاستمرارية بأمان",
                "قياس الجهد بشكل صحيح",
                "عزل الأعطال منطقياً",
            ],
            "safety": ["افترض دائماً أن الدوائس مضغوطة حتى يثبت خلاف ذلك."],
        },
        "ps": {
            "title": "خرابی کے ازالے کی منطق",
            "summary": "منطقی طریقے سے خرابی کو الگ کرنا، تسلسل او وولٹیج ٹیسٹنگ، او منطقی مسئلے کے حل۔",
            "objectives": [
                "منطقی طریقے سے خرابی کے ازالے کے طریقے کا استعمال کریں",
                "محفوظ طریقے سے مسلسل ٹیسٹ کریں",
                "وولٹیج کو صحیح طریقے سے ماپیں",
                "منطقی طریقے سے خرابیوں کو الگ کریں",
            ],
            "safety": ["ہمیشہ فرض کریں کہ سرکٹس سے توانائی دی جا رہی ہے جب تک ثابت نہ ہو۔"],
        },
        "sw": {
            "title": "Mantiki ya Ukanuzi wa Shida",
            "summary": "Jisambulishe la shida la utaratibu, mtihani wa kuendelea na voltage, na suluhu ya shida la mantiki.",
            "objectives": [
                "Tumia mbinu ya kutafuta shida iliyoumbwa",
                "Jaribu kuendelea kwa usalama",
                "Pima voltage kwa usahihi",
                "Jisambulishe shida mantiki",
            ],
            "safety": ["Daima fikiria kwamba mzunguko una nishati hadi kuthibitishwa na kinyume."],
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
        "hi": {
            "title": "सौर और ऑफ-ग्रिड सिस्टम",
            "summary": "PV सिजिंग, चार्ज कंट्रोलर, बैटरी बैंक और इनवर्टर इंस्टॉलेशन और सुरक्षा।",
            "objectives": [
                "PV arrays को सही तरीके से आकार दें",
                "चार्ज कंट्रोलर चुनें और प्रोग्राम करें",
                "बैटरी बैंक सिस्टम डिजाइन करें",
                "इनवर्टर को सुरक्षित रूप से स्थापित करें",
            ],
            "safety": ["DC सिस्टम अत्यंत खतरनाक हो सकते हैं। वोल्टेज और एम्पीयरेज का सम्मान करें।"],
        },
        "ar": {
            "title": "أنظمة الطاقة الشمسية والنظام المستقل",
            "summary": "تحديد حجم PV وأجهزة التحكم بالشحن وبنوك البطاريات وتثبيت ومأمنة العاكسات.",
            "objectives": [
                "حجم المصفوفات الكهروضوئية بشكل صحيح",
                "اختر وبرمج وحدات تحكم الشحن",
                "تصميم أنظمة بنك البطاريات",
                "تثبيت المحولات بأمان",
            ],
            "safety": ["أنظمة التيار المستمر يمكن أن تكون خطرة جداً. احترم الجهد و الأمبير."],
        },
        "ps": {
            "title": "سولر او آف ګریڈ سسٹم",
            "summary": "PV سائزنگ، چارج کنٹرولرز، بیٹری بینکس او انورٹر انسٹالیشن او حفاظت۔",
            "objectives": [
                "PV arrays کو صحیح طریقے سے سائز کریں",
                "چارج کنٹرولرز منتخب او پروگرام کریں",
                "بیٹری بینک سسٹمز ڈیزائن کریں",
                "انورٹرز کو محفوظ طریقے سے انسٹال کریں",
            ],
            "safety": ["DC سسٹمز بہت خطرناک ہو سکتے ہیں۔ وولٹیج او amperage کا احترام کریں۔"],
        },
        "sw": {
            "title": "Mifumo ya Jua na Nje ya Mtandao",
            "summary": "Ukubwa wa PV, wazo wa kusambaza chaji, benki la betri na uongoza salama wa inverter.",
            "objectives": [
                "Ukubwa wa safu za PV kwa usahihi",
                "Chagua na mchinapishi wazo wa kusambaza chaji",
                "Mifumo ya kubuniaj benki la betri",
                "Uongoza inverter kwa usalama",
            ],
            "safety": ["Mifumo ya DC inaweza kuwa hatari sana. Heshima voltage na amperage."],
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
    "hi": {
        "select_language": "भाषा चुनें",
        "course_library": "कोर्स लाइब्रेरी",
        "start_course": "कोर्स शुरू करें",
        "complete_course": "कोर्स पूरा करें",
        "certification": "प्रमाणन",
        "team_members": "टीम के सदस्य",
        "progress": "प्रगति",
        "time_spent": "समय व्यतीत",
        "score": "स्कोर",
        "license_tier": "लाइसेंस स्तर",
        "seats_available": "उपलब्ध सीटें",
        "view_certificate": "प्रमाणपत्र देखें",
        "download_certificate": "प्रमाणपत्र डाउनलोड करें",
        "share_certificate": "LinkedIn पर साझा करें",
    },
    "ar": {
        "select_language": "اختيار اللغة",
        "course_library": "مكتبة الدورات",
        "start_course": "ابدأ الدورة",
        "complete_course": "إكمال الدورة",
        "certification": "الشهادة",
        "team_members": "أعضاء الفريق",
        "progress": "التقدم",
        "time_spent": "الوقت المستغرق",
        "score": "النقاط",
        "license_tier": "مستوى الترخيص",
        "seats_available": "المقاعد المتاحة",
        "view_certificate": "عرض الشهادة",
        "download_certificate": "تحميل الشهادة",
        "share_certificate": "شارك على LinkedIn",
    },
    "ps": {
        "select_language": "ژبہ انتخاب کریں",
        "course_library": "کورس لائبریری",
        "start_course": "کورس شروع کریں",
        "complete_course": "کورس مکمل کریں",
        "certification": "سرٹیفیکیشن",
        "team_members": "ٹیم کے اراکین",
        "progress": "ترقی",
        "time_spent": "وقت لگایا",
        "score": "نمبر",
        "license_tier": "لائسنس سطح",
        "seats_available": "دستیاب نشستیں",
        "view_certificate": "سرٹیفکیٹ دیکھیں",
        "download_certificate": "سرٹیفکیٹ ڈاؤن لوڈ کریں",
        "share_certificate": "LinkedIn پر شیئر کریں",
    },
    "sw": {
        "select_language": "Chagua Lugha",
        "course_library": "Maktaba ya Kozi",
        "start_course": "Anza Kozi",
        "complete_course": "Kamata Kozi",
        "certification": "Cheti",
        "team_members": "Wanachama wa Timu",
        "progress": "Mwendelezo",
        "time_spent": "Muda Uliotumika",
        "score": "Alama",
        "license_tier": "Kiwango cha Leseni",
        "seats_available": "Viti Inayopatikana",
        "view_certificate": "Angalia Cheti",
        "download_certificate": "Pakua Cheti",
        "share_certificate": "Shiriki kwenye LinkedIn",
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
