"""Eco-Systems and Indigenous Land Stewardship in Africa (published course).

Science course covering African ecological regions and the agricultural, water-
management, pastoral, and land-stewardship systems developed by communities
living within them.
"""

AFRICAN_ECOSYSTEMS_LAND_STEWARDSHIP = {
    "slug": "african-ecosystems-land-stewardship",
    "title": "Eco-Systems and Indigenous Land Stewardship in Africa",
    "summary": "Studies African ecological regions and the agricultural, water-management, pastoral, and land-stewardship systems developed by communities living within them.",
    "description": (
        "Students study African ecological regions and the technologies developed by communities "
        "for agriculture, water management, and land stewardship. Emphasis is on technology, "
        "observation, adaptation, and ecological knowledge rather than folklore."
    ),
    "subject": "science",
    "subject_label": "Science",
    "track": "foundations",
    "tracks": ["foundations", "scholar"],
    "grades": ["7", "8", "9", "10"],
    "grade_label": "Grades 7–10",
    "status": "published",
    "audience": "Middle and high school students studying ecology and environmental science.",
    "est_hours": 15,
    "passing_score": 80,
    "learning_objectives": [
        "Identify major African biomes and climate zones.",
        "Explain indigenous ecological knowledge systems.",
        "Describe Sahel agriculture and soil conservation techniques.",
        "Explain African agroforestry principles.",
        "Describe rainforest agricultural practices.",
        "Explain pastoral water management systems.",
        "Describe indigenous water technologies.",
        "Analyze colonial environmental transformation.",
        "Evaluate modern climate resilience strategies.",
        "Design a climate-resilient agricultural system.",
    ],
    "units": [
        {
            "slug": "africas-ecological-diversity",
            "title": "Africa's Ecological Diversity",
            "summary": "Major biomes, climate zones, and how communities adapted to them.",
            "order": 1,
            "lessons": [
                {
                    "slug": "africas-ecological-diversity",
                    "title": "Africa's Ecological Diversity",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Major African biomes, climate zones, rainfall patterns, soil systems, and human adaptation.",
                    "learn": [
                        {"type": "p", "text": "Africa spans all major climate zones. The Sahara Desert dominates the north, while tropical rainforests cover the Congo Basin, savannas stretch across East and Southern Africa, and the Cape region holds Mediterranean-type shrubland. Rainfall patterns follow seasonal wind shifts, creating wet and dry seasons that drive agriculture, migration, and settlement patterns across the continent."},
                        {"type": "list", "items": [
                            "Savanna: the largest biome, characterized by grasslands with scattered trees and pronounced wet/dry seasons.",
                            "Tropical rainforest: high rainfall, multi-layered canopy, high biodiversity, nutrient-poor soils.",
                            "Sahel: transition zone between Sahara and savanna, semi-arid with seasonal rainfall.",
                            "Mediterranean: winter rainfall, summer drought, diverse shrubland and fynbos vegetation.",
                        ]},
                        {"type": "tip", "text": "Biomes are defined by the plants that survive there, and plants are defined by climate and soil. To understand a biome, look at what grows and why."},
                        {"type": "activity", "title": "Biome mapping", "text": "Use a blank outline map of Africa. Place each biome in its correct region, then add one community adaptation for each biome."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of African biomes.",
                        "questions": [
                            {"q": "The African savanna is best defined by…", "options": ["grasslands with scattered trees and distinct wet/dry seasons", "continuous dense forest canopy", "year-round frozen ground"], "answer": "grasslands with scattered trees and distinct wet/dry seasons", "explain": "Savannas cover the largest African area and are shaped by seasonal rainfall."},
                            {"q": "Rainforest soils in Africa tend to be…", "options": ["nutrient-poor despite high biomass", "deep and mineral-rich", "arid and salty"], "answer": "nutrient-poor despite high biomass", "explain": "Rapid decomposition cycles keep nutrients in vegetation, not in the soil."},
                        ],
                    },
                },
                {
                    "slug": "indigenous-ecological-knowledge",
                    "title": "Indigenous Ecological Knowledge",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Observation, seasonal cycles, biodiversity, traditional environmental indicators, scientific knowledge vs scientific method.",
                    "learn": [
                        {"type": "p", "text": "Indigenous ecological knowledge (IEK) is systematic observation accumulated over generations. Farmers tracking animal behavior to predict rain, herders reading plant phenology to time migration, and fishers noting water clarity to locate spawning grounds are all applying a scientific habit of mind: observe, record, test, transmit. The difference from textbook science is often the medium — oral, experiential, community-held — not the rigor."},
                        {"type": "list", "items": [
                            "Seasonal indicators: flowering trees, insect swarms, and bird migrations signal agricultural timing.",
                            "Biodiversity management: taboos on harvesting certain species at certain times act as conservation rules.",
                            "Oral transmission: knowledge is encoded in proverbs, songs, and apprenticeship rather than journals.",
                        ]},
                        {"type": "example", "title": "Scientific method comparison", "text": "A researcher studying crop yields and a farmer timing planting both form hypotheses, collect data, and revise predictions. The farmer's dataset is generational; the researcher's is recorded in papers."},
                        {"type": "activity", "title": "Observation log", "text": "Choose a local plant or animal. Write a five-entry observation log that could function as ecological knowledge: what you see, when, what it signals."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of indigenous ecological knowledge.",
                        "questions": [
                            {"q": "Indigenous ecological knowledge is best described as…", "options": ["systematic, generational observation of the environment", "random folklore with no practical basis", "identical to Western laboratory science"], "answer": "systematic, generational observation of the environment", "explain": "IEK uses observation, hypothesis, and transmission — methods shared with science."},
                            {"q": "A key difference between IEK and textbook science is often…", "options": ["the medium of recording and transmission", "the absence of observation", "that one is factual and the other is not"], "answer": "the medium of recording and transmission", "explain": "Rigor is found in both; what differs is how knowledge is stored and passed on."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "agricultural-systems",
            "title": "Agricultural Systems",
            "summary": "Sahelian techniques, agroforestry, and rainforest farming systems.",
            "order": 2,
            "lessons": [
                {
                    "slug": "sahel-agriculture",
                    "title": "Sahel Agriculture",
                    "order": 3,
                    "minutes": 20,
                    "summary": "Desertification, soil conservation, terracing, water capture, and agroforestry.",
                    "learn": [
                        {"type": "p", "text": "The Sahel stretches across Africa just south of the Sahara. Rainfall is erratic — one bad season can mean famine. Farmers developed systems to hold soil and water: stone lines slow runoff, zaï pits concentrate moisture around individual plants, and trees planted along field boundaries hold soil and drop leaf litter. These techniques are now recognized as among the earliest forms of conservation agriculture."},
                        {"type": "list", "items": [
                            "Zaï pits: small planting pits filled with organic matter that capture and hold rainwater.",
                            "Stone bunds: low stone walls that slow runoff and trap sediment.",
                            "Agroforestry integration: Faidherbia albida trees fix nitrogen and drop leaves in the growing season.",
                        ]},
                        {"type": "example", "title": "Modern validation", "text": "Satellite data since the 1980s shows that farmer-managed natural regeneration in the Sahel has restored millions of hectares — reversing desertification at low cost."},
                        {"type": "activity", "title": "Terracing design", "text": "Design a simple terraced plot for a 15-degree Sahel slope. Show water flow, crop placement, and how organic matter is conserved."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of Sahel agriculture.",
                        "questions": [
                            {"q": "Zaï pits primarily help farmers by…", "options": ["capturing and concentrating rainwater around plants", "attracting pollinating insects", "repelling herbivores"], "answer": "capturing and concentrating rainwater around plants", "explain": "In semi-arid zones, moisture is the limiting factor; pits concentrate scarce rain."},
                            {"q": "Farmer-managed natural regeneration in the Sahel demonstrates…", "options": ["indigenous techniques can reverse desertification at scale", "that trees cannot grow in the Sahel", "that modern technology is always superior"], "answer": "indigenous techniques can reverse desertification at scale", "explain": "Satellite evidence confirms large-scale regrowth from farmer-led agroforestry."},
                        ],
                    },
                },
                {
                    "slug": "african-agroforestry",
                    "title": "African Agroforestry",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Trees and crops, soil fertility, shade, food systems, and biodiversity.",
                    "learn": [
                        {"type": "p", "text": "Agroforestry mixes trees, crops, and sometimes livestock on the same land. In sub-Saharan Africa, farmers have practiced agroforestry for centuries because trees supply fuelwood, fruit, medicine, nitrogen, and shade while crops grow beneath them. The system builds soil fertility through leaf litter and root turnover, increases biodiversity by creating layered habitats, and stabilizes food supply because multiple products are harvested across seasons."},
                        {"type": "list", "items": [
                            "Soil fertility: leguminous trees fix atmospheric nitrogen, reducing need for external fertilizer.",
                            "Shade and microclimate: canopy trees lower ground temperature and reduce evaporation.",
                            "Biodiversity: multi-species systems support more birds, insects, and soil organisms than monocultures.",
                        ]},
                        {"type": "activity", "title": "System design", "text": "Design a half-hectare agroforestry plot for a community with five needs: food, fuel, medicine, soil improvement, and income. List the tree and crop species you would include and their roles."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of agroforestry.",
                        "questions": [
                            {"q": "Leguminous trees improve soil mainly by…", "options": ["fixing nitrogen from the atmosphere", "blocking sunlight to reduce evaporation", "attracting pests away from crops"], "answer": "fixing nitrogen from the atmosphere", "explain": "Legumes host bacteria that convert atmospheric nitrogen into plant-available form."},
                            {"q": "Compared to monocultures, agroforestry systems typically…", "options": ["support more biodiversity across soil, plants, and animals", "produce higher yields of a single crop", "require more purchased inputs"], "answer": "support more biodiversity across soil, plants, and animals", "explain": "Layered vegetation creates habitats and niches for more species."},
                        ],
                    },
                },
                {
                    "slug": "rainforest-agriculture",
                    "title": "Rainforest Agriculture",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Nutrient cycling, multi-layer agriculture, crop diversity, and forest management.",
                    "learn": [
                        {"type": "p", "text": "In the Congo Basin and West African rainforests, farmers developed systems that work with dense canopy and poor soils. Multi-layer agriculture plants crops at different heights — tall trees, shorter trees, shrubs, root crops — mimicking forest structure and maximizing light capture at every level. Crop diversity is not incidental but functional: it spreads risk, manages pests, and uses different soil depths."},
                        {"type": "list", "items": [
                            "Multi-layer system: upper canopy trees, understory shrubs, ground-level tubers — each layer uses different light and soil zones.",
                            "Nutrient cycling: leaf litter and root turnover quickly recycle organic matter, but when forest is cleared, nutrients are lost within years.",
                            "Shifting cultivation with long fallow: small plots farmed for a few years, then left to regenerate for decades.",
                        ]},
                        {"type": "activity", "title": "Layer mapping", "text": "Sketch a cross-section of a rainforest farm and label three layers, the crops or trees in each, and what each layer contributes to the system."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of rainforest agriculture.",
                        "questions": [
                            {"q": "Multi-layer agriculture in rainforests is effective because…", "options": ["different plants capture light at different heights", "all plants need the same light level", "only the tallest layer matters for yield"], "answer": "different plants capture light at different heights", "explain": "Stacking crops vertically makes better use of limited sunlight in dense forests."},
                            {"q": "A long fallow period in shifting cultivation primarily…", "options": ["lets soil nutrients and forest structure recover", "increases annual crop yield", "eliminates all pests permanently"], "answer": "lets soil nutrients and forest structure recover", "explain": "Extended fallow rebuilds the organic matter and biodiversity the system depends on."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "water-and-pastoral-systems",
            "title": "Water and Pastoral Systems",
            "summary": "Pastoral water management and indigenous water technologies.",
            "order": 3,
            "lessons": [
                {
                    "slug": "pastoral-water-management",
                    "title": "Pastoral Water Management",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Seasonal migration, grazing management, wells, water-sharing systems, and carrying capacity.",
                    "learn": [
                        {"type": "p", "text": "Pastoralists in the Sahel, Horn of Africa, and Kalahari move livestock across seasonal ranges to match rainfall and pasture availability. Water sources — wells, ponds, and rivers — are managed collectively, with rules about who draws water, when, and in what quantity. Carrying capacity calculations embedded in these rules prevent overgrazing and ensure the resource survives drought cycles."},
                        {"type": "list", "items": [
                            "Transhumance: seasonal movement between wet-season and dry-season pastures.",
                            "Water-sharing rules: community agreements governing access, often tied to kinship or cooperative labor.",
                            "Carrying capacity: the maximum livestock number the land and water can sustain without degradation.",
                        ]},
                        {"type": "activity", "title": "Carrying-capacity calculation", "text": "Given a well producing 10,000 liters per day and cattle drinking 40 liters per day each, calculate the maximum herd size. Then adjust if a three-month drought halves the well output."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of pastoral water management.",
                        "questions": [
                            {"q": "Transhumance primarily helps pastoralists by…", "options": ["matching livestock to seasonal pasture and water availability", "preventing all diseases", "eliminating the need for water storage"], "answer": "matching livestock to seasonal pasture and water availability", "explain": "Seasonal movement spreads pressure and uses resources when they are available."},
                            {"q": "Community water-sharing rules are important because…", "options": ["they prevent over-extraction and conflict during scarcity", "they guarantee every animal gets unlimited water", "they are required by all governments"], "answer": "they prevent over-extraction and conflict during scarcity", "explain": "Rules distribute scarce resources fairly and protect the resource itself."},
                        ],
                    },
                },
                {
                    "slug": "indigenous-water-technologies",
                    "title": "Indigenous Water Technologies",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Wells, irrigation, water storage, flood management, and community distribution systems.",
                    "learn": [
                        {"type": "p", "text": "Across Africa, communities engineered water systems without modern pumps or concrete. The qanats of the Horn of Africa channel groundwater through gently sloping tunnels. Check dams across seasonal streams slow floodwater and recharge groundwater. Community-managed reservoirs and tanks store runoff for dry seasons. Distribution rules — often managed by elders or water committees — allocate water by need, contribution, or lineage."},
                        {"type": "list", "items": [
                            "Qanats: gently sloping underground tunnels that tap groundwater and deliver it by gravity.",
                            "Check dams: low barriers across stream beds that slow floodwater, deposit silt, and recharge aquifers.",
                            "Community distribution: water rights tied to labor, kinship, or mutual aid rather than purchase alone.",
                        ]},
                        {"type": "activity", "title": "Technology comparison", "text": "Compare qanats, check dams, and modern boreholes on cost, maintenance, community involvement, and drought resilience. Which is best suited for a community with no electricity?"},
                    ],
                    "check": {
                        "prompt": "Check your understanding of indigenous water technologies.",
                        "questions": [
                            {"q": "A qanat delivers water primarily by…", "options": ["gravity through a gently sloping underground tunnel", "wind-powered pumps", "manual bucket brigades only"], "answer": "gravity through a gently sloping underground tunnel", "explain": "The tunnel's gradient moves water without mechanical energy."},
                            {"q": "Community-managed water distribution often differs from market systems because…", "options": ["it allocates water by need or contribution rather than price alone", "it charges higher rates for luxury use", "it eliminates the need for storage"], "answer": "it allocates water by need or contribution rather than price alone", "explain": "Social rules, not only prices, govern access in many traditional systems."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "soil-and-modern-challenges",
            "title": "Soil and Modern Challenges",
            "summary": "Soil management, food security, and colonial environmental transformation.",
            "order": 4,
            "lessons": [
                {
                    "slug": "soil-and-food-security",
                    "title": "Soil and Food Security",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Soil erosion, composting, crop rotation, indigenous and modern techniques.",
                    "learn": [
                        {"type": "p", "text": "African soils range from the ancient, weathered oxisols of the tropics to the fertile volcanic soils of the highlands. Erosion by wind and water removes topsoil, while continuous cropping drains nutrients. Indigenous responses included contour ridging, mixed cropping, fallowing, and composting with ash and animal manure. Modern soil management combines these with soil testing, cover crops, and mineral fertilizer where affordable."},
                        {"type": "list", "items": [
                            "Contour ridging: furrows along slope lines that trap runoff and prevent sheet erosion.",
                            "Mixed cropping: different root depths and nutrient needs planted together reduce depletion.",
                            "Composting: integrating crop residues and manure rebuilds organic matter and structure.",
                        ]},
                        {"type": "activity", "title": "Soil strategy design", "text": "A community has a 5-hectare plot on a 10-degree slope with 800 mm annual rainfall. Design a soil management plan using three techniques from this lesson. Explain why each is suited to this slope and rainfall."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of soil and food security.",
                        "questions": [
                            {"q": "Contour ridging is effective on slopes because…", "options": ["it traps runoff along the contour line rather than letting it carve channels downslope", "it increases wind speed", "it removes all weeds"], "answer": "it traps runoff along the contour line rather than letting it carve channels downslope", "explain": "Slowing water flow reduces erosion and gives soil time to absorb moisture."},
                            {"q": "Mixed cropping helps soil fertility because…", "options": ["different plants use and replace different nutrients", "all plants deplete the same nutrients equally", "it eliminates the need for any soil management"], "answer": "different plants use and replace different nutrients", "explain": "Diverse root systems and residue types maintain more balanced nutrient cycling."},
                        ],
                    },
                },
                {
                    "slug": "colonial-environmental-transformation",
                    "title": "Colonial Environmental Transformation",
                    "order": 9,
                    "minutes": 18,
                    "summary": "Cash crops, land restructuring, resource extraction, and changes in local food systems.",
                    "learn": [
                        {"type": "p", "text": "Colonial powers restructured African landscapes to serve export economies. Forests were cleared for rubber, cocoa, cotton, and coffee plantations. Communal grazing lands were enclosed for settler ranches. Rivers were dammed for irrigation and mining. Indigenous food systems were replaced by cash-crop monocultures that made local populations dependent on imported food and vulnerable to price swings."},
                        {"type": "list", "items": [
                            "Cash-crop monocultures: high export value but displaced diverse local food systems.",
                            "Land enclosure: communal lands privatized for plantations, reducing access for smallholders.",
                            "Ecological simplification: diverse ecosystems replaced by single-species fields, increasing pest and drought risk.",
                        ]},
                        {"type": "activity", "title": "Before/after analysis", "text": "Compare one African region before and after colonial cash-crop introduction. What ecological changes occurred? How did food security and farmer autonomy change?"},
                    ],
                    "check": {
                        "prompt": "Check your understanding of colonial environmental transformation.",
                        "questions": [
                            {"q": "A major ecological effect of colonial cash-crop plantations was…", "options": ["simplifying diverse ecosystems into single-species fields", "increasing local biodiversity", "eliminating all soil erosion"], "answer": "simplifying diverse ecosystems into single-species fields", "explain": "Monocultures replaced complex indigenous systems, reducing resilience."},
                            {"q": "Enclosure of communal grazing land most directly harmed…", "options": ["pastoralists who depended on seasonal access", "colonial mining companies", "urban factory owners"], "answer": "pastoralists who depended on seasonal access", "explain": "Removing communal rights disrupted the mobility and water access pastoral systems required."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "resilience-and-capstone",
            "title": "Resilience and Capstone",
            "summary": "Combining modern and traditional approaches for climate resilience.",
            "order": 5,
            "lessons": [
                {
                    "slug": "modern-climate-resilience",
                    "title": "Modern Climate Resilience",
                    "order": 10,
                    "minutes": 20,
                    "summary": "Drought, flooding, climate adaptation, and combining modern technology with indigenous knowledge.",
                    "learn": [
                        {"type": "p", "text": "Climate change is intensifying drought and flood cycles across Africa. Resilience strategies now often blend indigenous knowledge with modern tools: satellite rainfall data combined with traditional seasonal indicators, drip irrigation paired with zaï pits, and drought-resistant crop varieties selected through both breeding programs and farmer seed networks. The most effective programs treat indigenous practitioners as co-designers, not beneficiaries of aid."},
                        {"type": "list", "items": [
                            "Drought resilience: early warning systems, drought-resistant varieties, water-harvesting structures.",
                            "Flood resilience: raised beds, drainage channels, floodplain agriculture timing.",
                            "Co-design: farmers participate in research design, not only technology transfer.",
                        ]},
                        {"type": "activity", "title": "Resilience design", "text": "For a Sahel community facing projected 20% rainfall decline, combine one indigenous and one modern technique into a single resilience strategy. Explain how each reinforces the other."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of climate resilience.",
                        "questions": [
                            {"q": "The most effective climate-resilience programs typically…", "options": ["combine indigenous knowledge with modern tools and treat farmers as co-designers", "replace all traditional practices with imported technology", "focus only on emergency relief after disasters"], "answer": "combine indigenous knowledge with modern tools and treat farmers as co-designers", "explain": "Hybrid approaches that respect local knowledge are more durable and locally adapted."},
                            {"q": "Drought-resistant crop varieties are most effective when…", "options": ["developed through both breeding programs and farmer seed selection", "imported from other continents without local testing", "replaced every local variety immediately"], "answer": "developed through both breeding programs and farmer seed selection", "explain": "Local adaptation and farmer preference determine whether a new variety is actually adopted."},
                        ],
                    },
                },
                {
                    "slug": "climate-resilient-agricultural-system-capstone",
                    "title": "Climate-Resilient Agricultural System Design",
                    "order": 11,
                    "minutes": 30,
                    "summary": "Students design a climate-resilient community agricultural system for one African ecological region.",
                    "learn": [
                        {"type": "p", "text": "In this capstone you will design a climate-resilient agricultural system for a real African ecological region. Your system must address: climate (rainfall patterns, temperature, extreme events), water source (surface water, groundwater, rainwater harvesting), crops and livestock (what is grown or grazed and why), soil strategy (how fertility and erosion are managed), food storage (how surplus is preserved through lean seasons), environmental risks (drought, flood, pest), and a sustainability strategy (how the system renews itself without degrading the land)."},
                        {"type": "list", "items": [
                            "Climate analysis: describe the region's rainfall, temperature, and projected climate stresses.",
                            "Water source: identify the primary water source and how it is protected and managed.",
                            "Crops and soil: select species and techniques suited to the soil and climate.",
                            "Sustainability: show how the system maintains or improves soil, water, and biodiversity over decades.",
                        ]},
                        {"type": "activity", "title": "Design your system", "text": "Choose one African biome. Produce a one-page system design with labeled sections for climate, water, crops, soil strategy, storage, risk management, and sustainability. Justify every choice with ecological reasoning."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of the capstone design process.",
                        "questions": [
                            {"q": "A climate-resilient system design must address all of these EXCEPT…", "options": ["the farmer's favorite color", "climate, water, crops, soil, storage, and risk management"], "answer": "the farmer's favorite color", "explain": "A complete design addresses the ecological and practical constraints of the system."},
                            {"q": "Sustainability in an agricultural system means…", "options": ["the system can maintain or improve soil, water, and biodiversity over decades", "maximizing yield in one good season regardless of later damage", "importing all needed inputs from outside the community"], "answer": "the system can maintain or improve soil, water, and biodiversity over decades", "explain": "Sustainable systems do not mine the land; they keep it productive for future seasons."},
                        ],
                    },
                },
            ],
        },
    ],
}
