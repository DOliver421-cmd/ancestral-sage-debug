"""Economics of Extraction: The True Ledger of Western Growth (published course).

Traces resource extraction, industrialization, colonialism, and wealth
accumulation through economic evidence, from plantation capital to global
commodity chains.
"""

ECONOMICS_OF_EXTRACTION = {
    "slug": "economics-of-extraction",
    "title": "Economics of Extraction: The True Ledger of Western Growth",
    "summary": (
        "Examines industrialization, labor, resource extraction, colonialism, "
        "and wealth accumulation through the lens of economic evidence."
    ),
    "description": (
        "Students follow the ledger from resource extraction through industrial "
        "development, colonialism, and global trade to understand how wealth was "
        "accumulated. The course teaches students to examine evidence rather than "
        "accepting either pro- or anti-Western narratives uncritically."
    ),
    "subject": "social_studies",
    "subject_label": "Social Studies",
    "track": "scholar",
    "tracks": ["scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": (
        "High school students studying economics, history, and global development."
    ),
    "est_hours": 20,
    "passing_score": 80,
    "learning_objectives": [
        "Define economic extraction and value capture.",
        "Explain how enslaved labor contributed to capital formation.",
        "Analyze colonial resource systems.",
        "Trace industrialization's dependence on raw materials and labor.",
        "Follow a global commodity chain from resource to consumer.",
        "Explain unequal trade relationships.",
        "Analyze the role of finance in capital accumulation.",
        "Identify externalized costs of production.",
        "Calculate approximate value distribution in a commodity chain.",
        "Construct an economic flowchart showing extraction and ownership.",
    ],
    "units": [
        {
            "slug": "foundations",
            "title": "Unit 1 — Foundations",
            "summary": "Core concepts of extraction and the link between labor and capital.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-is-economic-extraction",
                    "title": "What Is Economic Extraction?",
                    "order": 1,
                    "minutes": 20,
                    "summary": (
                        "Resources, labor, capital, value creation, and value capture."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Economic extraction occurs when value is taken from a "
                                "source — land, labor, or minerals — and captured by an "
                                "entity that does not bear the full cost. Value creation "
                                "is the actual work of producing goods; value capture is "
                                "who pockets the surplus."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Resources: raw materials taken from the earth.",
                                "Labor: human work that transforms resources into goods.",
                                "Capital: accumulated wealth used to produce more wealth.",
                                "Value capture: the surplus taken by owners, investors, or intermediaries.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Surplus value",
                            "text": (
                                "A worker picks cotton worth $1,000. The factory "
                                "sells the finished shirt for $50. The $49 surplus is "
                                "captured by the owner — that is the extraction mechanism."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Map the flow",
                            "text": (
                                "Draw a simple flow: resource → labor → product → "
                                "consumer. Mark where value is created and where it is "
                                "captured. Who owns each step?"
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of economic extraction.",
                        "questions": [
                            {
                                "q": "Value capture means…",
                                "options": [
                                    "who receives the surplus from production",
                                    "how much labor time goes into a product",
                                    "the raw cost of materials",
                                ],
                                "answer": "who receives the surplus from production",
                                "explain": (
                                    "Capture is about ownership and distribution, "
                                    "not the physical act of producing."
                                ),
                            },
                            {
                                "q": "Economic extraction most directly involves…",
                                "options": [
                                    "taking resources or labor while shifting costs elsewhere",
                                    "voluntary exchange between equals",
                                    "government tax policy alone",
                                ],
                                "answer": "taking resources or labor while shifting costs elsewhere",
                                "explain": (
                                    "Extraction is defined by asymmetry: one party "
                                    "bears the cost while another captures the gain."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "enslaved-labor-and-capital-formation",
                    "title": "Enslaved Labor and Capital Formation",
                    "order": 2,
                    "minutes": 20,
                    "summary": (
                        "How plantation economies, commodity production, banking, "
                        "insurance, and trade financed industrialization."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "The transatlantic slave system moved roughly 12.5 million "
                                "Africans to the Americas. Enslaved labor produced cotton, "
                                "sugar, tobacco, and coffee — commodities that became the "
                                "raw materials for European factories and the collateral for "
                                "banks and insurance companies."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Cotton exports from the U.S. South fed British textile mills.",
                                "Slave collateral financed railroads and real estate.",
                                "Insurance companies profited from policies on enslaved people.",
                                "Banking houses in London and New York built capital on slave-backed credit.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Counting the value",
                            "text": (
                                "By 1860, enslaved people in the U.S. were valued at "
                                "roughly $3 billion — more than all the railroads and "
                                "factories combined. That wealth migrated into post-war "
                                "finance and industry."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Follow the money",
                            "text": (
                                "Trace one cotton shipment from a Southern plantation to "
                                "a British factory. List three ways profit was extracted "
                                "from enslaved labor at each step."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of capital formation from slavery.",
                        "questions": [
                            {
                                "q": "Enslaved labor contributed most directly to capital formation by…",
                                "options": [
                                    "producing raw commodities that financed industry",
                                    "building roads with their own wages",
                                    "inventing factory machinery",
                                ],
                                "answer": "producing raw commodities that financed industry",
                                "explain": (
                                    "The commodity output, not wages, was the vehicle "
                                    "for capital accumulation."
                                ),
                            },
                            {
                                "q": "Insurance companies profited from slavery by…",
                                "options": [
                                    "selling policies on enslaved people as property",
                                    "insuring slave ships against storms only",
                                    "providing free coverage to plantations",
                                ],
                                "answer": "selling policies on enslaved people as property",
                                "explain": (
                                    "Enslaved individuals were listed as insured assets, "
                                    "making insurance a direct financial beneficiary."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "colonial-systems",
            "title": "Unit 2 — Colonial Systems",
            "summary": "How colonial powers extracted land, minerals, and labor.",
            "order": 2,
            "lessons": [
                {
                    "slug": "colonial-resource-systems",
                    "title": "Colonial Resource Systems",
                    "order": 3,
                    "minutes": 18,
                    "summary": (
                        "Land, minerals, agricultural commodities, and forced labor."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Colonialism institutionalized extraction. European powers "
                                "claimed land, mineral rights, and labor through a mix of "
                                "force, treaties signed under duress, and administrative "
                                "reorganization. Cash-crop agriculture replaced food crops, "
                                "binding colonies to volatile world markets."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Land alienation: fertile land seized for European settlers and plantations.",
                                "Cash crops: cocoa, coffee, cotton, rubber grown for export, not local food.",
                                "Forced labor: colonial taxes paid only in cash forced people into wage labor.",
                                "Mineral concessions: mines given to European companies with local royalty rates near zero.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "The Congo Free State",
                            "text": (
                                "Under King Leopold II, the Congo extracted rubber through "
                                "a terror system. Population declines reached 10 million. "
                                "Revenue from rubber financed Belgian public works and "
                                "private wealth — while the Congo received almost nothing in return."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Resource-flow map",
                            "text": (
                                "Pick one colony. List the three most valuable exports, "
                                "the European companies that controlled them, and what "
                                "percentage of profits stayed in the colony."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of colonial resource systems.",
                        "questions": [
                            {
                                "q": "Colonial cash-crop systems primarily benefited…",
                                "options": [
                                    "European firms and colonial administrations",
                                    "local subsistence farmers",
                                    "indigenous manufacturing",
                                ],
                                "answer": "European firms and colonial administrations",
                                "explain": (
                                    "Export crops generated profit for the colonizer; "
                                    "local food security was frequently sacrificed."
                                ),
                            },
                            {
                                "q": "Forced labor in colonies was often enforced through…",
                                "options": [
                                    "taxes payable only in cash earned by wage labor",
                                    "free market employment contracts",
                                    "local democratic elections",
                                ],
                                "answer": "taxes payable only in cash earned by wage labor",
                                "explain": (
                                    "The tax system was engineered to push people into "
                                    "the colonial wage economy."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "industrialization",
                    "title": "Industrialization",
                    "order": 4,
                    "minutes": 20,
                    "summary": (
                        "Factories, energy, transportation, raw materials, and labor."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Industrialization did not emerge from domestic savings "
                                "alone. Raw cotton, rubber, metals, and energy from colonial "
                                "territories supplied European and American factories. The "
                                "steam engine, railroads, and telegraph all depended on "
                                "materials and labor systems built on extraction."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Raw cotton: Southern U.S. slavery and Egyptian colonial cotton fed mills.",
                                "Metals: copper from Central Africa, tin from Malaya, iron from India.",
                                "Energy: coal from Britain, oil from the Middle East and Baku.",
                                "Railroads: built with colonial steel and indentured labor, exporting raw goods.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "The Lancashire mills",
                            "text": (
                                "By 1860, 90 percent of cotton imported to British mills "
                                "came from the American South. When the Union blockade "
                                "cut off supply, British merchants turned to Egypt and India — "
                                "both under coercive labor regimes."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Supply-chain trace",
                            "text": (
                                "Trace one manufactured good in your classroom (a phone, "
                                "a chair, a backpack). Identify the raw materials, where "
                                "they came from, and who likely performed the extraction labor."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of industrialization's inputs.",
                        "questions": [
                            {
                                "q": "Industrialization depended most directly on…",
                                "options": [
                                    "raw materials extracted from colonized and coerced regions",
                                    "pure domestic savings with no foreign inputs",
                                    "a sudden technological leap unrelated to resources",
                                ],
                                "answer": "raw materials extracted from colonized and coerced regions",
                                "explain": (
                                    "Factory output was limited by inputs — cotton, metals, "
                                    "and energy — all shaped by extraction networks."
                                ),
                            },
                            {
                                "q": "Railroads in the 19th century primarily served…",
                                "options": [
                                    "moving raw materials from interior to ports for export",
                                    "urban mass transit for workers",
                                    "tourism between European capitals",
                                ],
                                "answer": "moving raw materials from interior to ports for export",
                                "explain": (
                                    "Colonial railroads were export-oriented, not designed "
                                    "for internal economic integration."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "global-chains",
            "title": "Unit 3 — Global Chains",
            "summary": "Commodity chains, unequal trade, and African mineral wealth.",
            "order": 3,
            "lessons": [
                {
                    "slug": "global-commodity-chains",
                    "title": "Global Commodity Chains",
                    "order": 5,
                    "minutes": 18,
                    "summary": (
                        "Following products from resource through distribution to consumer."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "A global commodity chain maps every stage: extraction, "
                                "processing, manufacturing, distribution, and retail. Each "
                                "stage adds value — and each stage is a point of extraction "
                                "when wages are suppressed or environmental costs are dumped."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Resource extraction: mining, logging, farming with little local value added.",
                                "Processing: basic refinement, still low-margin and labor-intensive.",
                                "Manufacturing: assembly and branding — the highest-value stage, usually in wealthy nations.",
                                "Distribution: logistics and retail captured by global corporations.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "A chocolate bar",
                            "text": (
                                "Cocoa grown in Ivory Coast, fermented and dried there, "
                                "shipped to Europe for roasting and grinding, turned into "
                                "chocolate by a multinational, then sold back to West "
                                "African consumers at a higher price than it sold for export."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Trace a product",
                            "text": (
                                "Take a common item (a T-shirt, coffee, phone). List every "
                                "country involved in its chain and identify which stage "
                                "adds the most value and which pays the least."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of commodity chains.",
                        "questions": [
                            {
                                "q": "In a commodity chain, the highest-value stage is usually…",
                                "options": [
                                    "branding and retail in wealthy consumer markets",
                                    "raw extraction in the producing country",
                                    "transport across oceans",
                                ],
                                "answer": "branding and retail in wealthy consumer markets",
                                "explain": (
                                    "Processing and assembly add little margin; design, "
                                    "marketing, and retail in rich countries capture most profit."
                                ),
                            },
                            {
                                "q": "A commodity chain is useful for understanding…",
                                "options": [
                                    "who profits at each stage of production",
                                    "only the final price paid by consumers",
                                    "how many workers are employed globally",
                                ],
                                "answer": "who profits at each stage of production",
                                "explain": (
                                    "Chain analysis reveals the distribution of value — "
                                    "and therefore the distribution of power."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "unequal-trade",
                    "title": "Unequal Trade",
                    "order": 6,
                    "minutes": 18,
                    "summary": (
                        "Tariffs, trade monopolies, colonial trade rules, and terms of trade."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Trade rules are not neutral. Colonial systems forced colonies "
                                "to sell raw materials cheaply and buy finished goods at high "
                                "prices. Post-independence tariffs and subsidies continued to "
                                "favor wealthy nations, locking poorer countries into export "
                                "commodity dependence."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Monocrop dependence: one export crop makes a country vulnerable to price swings.",
                                "Tariff escalation: processed goods face higher tariffs than raw materials.",
                                "Subsidies: rich nations subsidize their own farmers, undercutting global prices.",
                                "Terms of trade: the ratio of export prices to import prices, historically declining for commodities.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Coffee price collapse",
                            "text": (
                                "In the 1980s and 1990s, coffee prices fell 70 percent due "
                                "to overproduction and market deregulation. Smallholder "
                                "farmers in Ethiopia and Colombia could not cover costs — "
                                "while roasters and retailers in rich nations kept their margins."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Terms-of-trade calculation",
                            "text": (
                                "In 1980, a coffee exporter needed 10 tons to buy a tractor. "
                                "By 2000, they needed 30 tons. Calculate the percentage "
                                "decline in purchasing power and explain what that means for development."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of unequal trade.",
                        "questions": [
                            {
                                "q": "Terms of trade measure…",
                                "options": [
                                    "the ratio of export prices to import prices",
                                    "how many ships a country owns",
                                    "the total value of GDP",
                                ],
                                "answer": "the ratio of export prices to import prices",
                                "explain": (
                                    "A declining ratio means a country must sell more exports "
                                    "to buy the same imports — a squeeze on development."
                                ),
                            },
                            {
                                "q": "Tariff escalation disadvantages developing countries by…",
                                "options": [
                                    "charging higher tariffs on processed goods than raw materials",
                                    " banning all agricultural exports",
                                    "requiring colonies to trade only with the metropole",
                                ],
                                "answer": "charging higher tariffs on processed goods than raw materials",
                                "explain": (
                                    "It is cheaper to export raw cocoa than chocolate bars, "
                                    "preventing value-added industrialization."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "africa-and-mineral-wealth",
                    "title": "Africa and Mineral Wealth",
                    "order": 7,
                    "minutes": 18,
                    "summary": (
                        "Gold, diamonds, copper, oil, and critical minerals in Africa."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Africa holds roughly 30 percent of global mineral reserves, "
                                "including 40 percent of gold, 60 percent of cobalt, and 90 "
                                "percent of platinum-group metals. Yet mineral-rich nations "
                                "often rank low on human development indices — because "
                                "extraction is structured to export raw ore and import "
                                "finished goods."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Gold: South Africa and Ghana produced wealth that financed European banks.",
                                "Diamonds: Botswana and Sierra Leone — conflict diamonds fueled civil war.",
                                "Cobalt: the Democratic Republic of Congo supplies 70 percent of global supply.",
                                "Lithium and critical minerals: new extraction frontiers with same extraction pattern.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Cobalt chain",
                            "text": (
                                "Cobalt ore mined in Congo for roughly $2 per pound is sold "
                                "to Chinese processors, turned into battery-grade chemicals, "
                                "then built into phones and EVs sold in the U.S. and EU "
                                "for hundreds of dollars per pound of contained metal."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Mineral-tracing",
                            "text": (
                                "Choose one African mineral. Trace it from mine to finished "
                                "product. List each country or company involved and what "
                                "percentage of final value each captures."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of mineral wealth extraction.",
                        "questions": [
                            {
                                "q": "Africa's mineral wealth has not translated into broad development mainly because…",
                                "options": [
                                    "most value is captured outside the continent",
                                    "Africans lack the skills to process minerals",
                                    "there are simply too few minerals to matter",
                                ],
                                "answer": "most value is captured outside the continent",
                                "explain": (
                                    "Exporting raw ore means the high-value processing, "
                                    "manufacturing, and intellectual property stay elsewhere."
                                ),
                            },
                            {
                                "q": "Conflict diamonds are significant because they show…",
                                "options": [
                                    "how mineral wealth can fund violence and instability",
                                    "diamonds are not actually valuable",
                                    "all mining is inherently peaceful",
                                ],
                                "answer": "how mineral wealth can fund violence and instability",
                                "explain": (
                                    "When valuable minerals are controlled by armed groups, "
                                    "resource wealth becomes a driver of war rather than development."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "labor-and-finance",
            "title": "Unit 4 — Labor and Finance",
            "summary": "How labor costs are determined and how finance accumulates capital.",
            "order": 4,
            "lessons": [
                {
                    "slug": "labor-and-cost-of-production",
                    "title": "Labor and the Cost of Production",
                    "order": 8,
                    "minutes": 18,
                    "summary": (
                        "Wages, working conditions, productivity, profit, and labor organization."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "The cost of labor is not simply a market wage — it is "
                                "shaped by bargaining power, legal protections, supply of "
                                "workers, and the threat of substitution. Employers suppress "
                                "costs through subcontracting, automation, immigration policy, "
                                "and outright coercion. Profit equals revenue minus costs, "
                                "so lowering labor costs directly raises profit — and extraction "
                                "begins when the gap widens beyond fair compensation."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Wage suppression: an oversupply of workers weakens negotiating power.",
                                "Subcontracting: avoids benefits, pensions, and legal protections.",
                                "Automation: replaces workers with machines, concentrating profits.",
                                "Labor organization: unions and collective bargaining can restore balance.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Fast fashion wages",
                            "text": (
                                "A $5 T-shirt may have been sewn by a worker earning $3 per day, "
                                "working 12-hour shifts. The brand's profit margin is often "
                                "higher than the sum paid to all workers in the supply chain."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Wage analysis",
                            "text": (
                                "Research the minimum wage in one country that exports garments. "
                                "Calculate how many hours a worker must labor to earn a living wage. "
                                "Compare that to the retail price of a similar item in your country."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of labor and production costs.",
                        "questions": [
                            {
                                "q": "Employers suppress labor costs most effectively through…",
                                "options": [
                                    "creating an oversupply of workers or subcontracting",
                                    "raising the minimum wage",
                                    "voluntary profit-sharing agreements",
                                ],
                                "answer": "creating an oversupply of workers or subcontracting",
                                "explain": (
                                    "Surplus labor weakens bargaining power; subcontracting "
                                    "shifts risk and benefits costs onto workers."
                                ),
                            },
                            {
                                "q": "Labor organization primarily counteracts extraction by…",
                                "options": [
                                    "collectively bargaining for higher wages and safer conditions",
                                    "reducing the total number of workers",
                                    "automating production lines",
                                ],
                                "answer": "collectively bargaining for higher wages and safer conditions",
                                "explain": (
                                    "Unions restore power asymmetry by giving workers "
                                    "a collective voice in setting the terms of their own labor."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "finance-and-capital-accumulation",
                    "title": "Finance and Capital Accumulation",
                    "order": 9,
                    "minutes": 18,
                    "summary": (
                        "Banks, credit, investment, interest, and ownership structures."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Finance does not create new physical value — it moves and "
                                "multiplies existing value through credit, interest, and ownership. "
                                "Banks lend against collateral (often extracted assets). Investors "
                                "buy ownership of productive enterprises and capture dividends "
                                "or capital gains. The financial sector extracts fees, interest, "
                                "and rent from every real economic transaction."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Credit creation: banks create money when they lend, charging interest on created value.",
                                "Ownership concentration: a small shareholder class captures dividends from global production.",
                                "Tax havens: profits shifted to zero-tax jurisdictions, denied to societies where value was created.",
                                "Debt traps: high-interest loans force borrowing nations to cede resources.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Resource-backed loans",
                            "text": (
                                "In the 1970s and 1980s, Western banks lent to developing nations "
                                "at variable rates. When rates spiked, countries like Zambia could "
                                "not repay. Lenders demanded copper mines, railroads, and water "
                                "systems as collateral — transferring public assets to private creditors."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Capital-flow mapping",
                            "text": (
                                "Map how a $100 million mining loan flows from a London bank to "
                                "a mine in Africa and back to investors. Mark every point where "
                                "value leaves the producing country."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of finance and capital.",
                        "questions": [
                            {
                                "q": "Banks create value primarily by…",
                                "options": [
                                    "lending against collateral and charging interest",
                                    "printing physical currency",
                                    "mining raw materials",
                                ],
                                "answer": "lending against collateral and charging interest",
                                "explain": (
                                    "Most money is bank-created credit; interest extracts "
                                    "surplus from productive activity."
                                ),
                            },
                            {
                                "q": "Debt traps extract value by…",
                                "options": [
                                    "forcing asset sales when loans cannot be repaid",
                                    "reducing interest rates for borrowers",
                                    "providing unconditional grants",
                                ],
                                "answer": "forcing asset sales when loans cannot be repaid",
                                "explain": (
                                    "Default converts future production and public assets "
                                    "into creditor property."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "externalized-costs",
                    "title": "Externalized Costs",
                    "order": 10,
                    "minutes": 18,
                    "summary": (
                        "Environmental damage, health effects, displacement, and infrastructure costs."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Externalized costs are costs of production that are not paid "
                                "by the producer — they are passed to workers, communities, or "
                                "future generations. Pollution, soil depletion, water contamination, "
                                "and chronic disease all represent value extracted from the public "
                                "to increase private profit."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Air and water pollution: health costs borne by nearby residents, not the factory.",
                                "Soil depletion: intensive agriculture strips nutrients, leaving future yields lower.",
                                "Displacement: dams, mines, and plantations remove communities from their land.",
                                "Climate damage: carbon emissions externalized to the entire global population.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "The Niger Delta",
                            "text": (
                                "Shell and other oil companies extracted $600 billion worth of "
                                "oil from the Niger Delta since the 1950s. Local communities "
                                "live with poisoned water, gas flaring, and lost farmland. "
                                "The environmental cost was never included in oil's market price."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Cost identification",
                            "text": (
                                "Choose a local industry (farming, manufacturing, energy). "
                                "List three costs it may be passing on to the community or "
                                "environment that are not on its balance sheet."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of externalized costs.",
                        "questions": [
                            {
                                "q": "An externalized cost is…",
                                "options": [
                                    "a cost of production borne by someone other than the producer",
                                    "the profit margin on a finished product",
                                    "the wage paid to workers",
                                ],
                                "answer": "a cost of production borne by someone other than the producer",
                                "explain": (
                                    "Externalities are unpriced harms passed to third parties "
                                    "or to the public."
                                ),
                            },
                            {
                                "q": "Externalized environmental costs most directly affect…",
                                "options": [
                                    "the health and livelihoods of nearby communities",
                                    "the profit margin of the producing firm",
                                    "the cost of advertising",
                                ],
                                "answer": "the health and livelihoods of nearby communities",
                                "explain": (
                                    "The firm avoids the cost; the community absorbs the harm."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "analysis-and-models",
            "title": "Unit 5 — Analysis and Models",
            "summary": "Mapping value distribution and comparing alternative economic models.",
            "order": 5,
            "lessons": [
                {
                    "slug": "who-captures-the-value",
                    "title": "Who Captures the Value?",
                    "order": 11,
                    "minutes": 20,
                    "summary": (
                        "Analyzing commodity chains and calculating approximate value distribution."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Value capture is not always obvious because supply chains are "
                                "complex. Governments, corporations, landowners, financiers, "
                                "and brand owners each take a slice. Workers at the extraction "
                                "end typically receive the smallest share. Mapping value "
                                "distribution reveals where power concentrates and where "
                                "remediation is possible."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Farmers or miners: often 1–5 percent of final retail value.",
                                "Processors: 5–15 percent, depending on barriers to entry.",
                                "Manufacturers: 15–30 percent, higher for high-tech assembly.",
                                "Brands and retailers: 40–70 percent, capturing most consumer surplus.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Banana pricing",
                            "text": (
                                "A banana that sells for 70 cents in a U.S. grocery store "
                                "returns roughly 5–10 cents to the grower. The rest is "
                                "split among shippers, ripeners, distributors, and the retailer."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Value-capture calculation",
                            "text": (
                                "Take a coffee chain where farmers receive 10 cents per dollar "
                                "of retail sales. Calculate the farmer's share as a percentage. "
                                "Identify who captures the remaining 90 percent."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of value capture.",
                        "questions": [
                            {
                                "q": "Workers at the extraction end of a commodity chain typically receive…",
                                "options": [
                                    "the smallest percentage of final retail value",
                                    "the largest percentage of final retail value",
                                    "about the same as brand owners",
                                ],
                                "answer": "the smallest percentage of final retail value",
                                "explain": (
                                    "Because extraction has the fewest barriers to entry "
                                    "and the greatest surplus transfer, producers capture "
                                    "the least."
                                ),
                            },
                            {
                                "q": "Mapping value distribution reveals…",
                                "options": [
                                    "where power and profit concentrate in a chain",
                                    "the exact legal ownership of every firm",
                                    "how to eliminate all trade",
                                ],
                                "answer": "where power and profit concentrate in a chain",
                                "explain": (
                                    "The map does not prescribe solutions — it shows the "
                                    "current structure of extraction."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "building-a-fairer-economic-model",
                    "title": "Building a Fairer Economic Model",
                    "order": 12,
                    "minutes": 20,
                    "summary": (
                        "Comparing extraction, cooperative ownership, local processing, and community investment."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Alternative economic models change where value flows. "
                                "Cooperative ownership gives workers a vote and a share of profits. "
                                "Local processing keeps more value in the producing country. "
                                "Community investment returns a portion of profit to health, "
                                "education, and infrastructure — reducing externalized costs."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Worker cooperatives: labor owns the enterprise and shares in decisions and profits.",
                                "Local processing: refining and manufacturing inside resource-rich nations.",
                                "Community dividends: companies fund schools, clinics, and infrastructure.",
                                "Fair-trade minimums: price floors that cover production costs plus a living margin.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Fair-trade coffee",
                            "text": (
                                "Fair-trade certification guarantees a minimum price plus a "
                                "social premium. In years of low market prices, the floor "
                                "protects farmers from ruin. The premium funds schools and "
                                "clinics — converting what was an externalized cost into an "
                                "internal investment."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Model comparison",
                            "text": (
                                "Compare extraction and cooperative ownership across four "
                                "dimensions: who owns capital, who decides, who bears risk, "
                                "and who receives profit. Which model better aligns incentives "
                                "with community well-being?"
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of alternative economic models.",
                        "questions": [
                            {
                                "q": "A worker cooperative differs from a conventional firm by…",
                                "options": [
                                    "giving workers ownership and a share of profits",
                                    "eliminating all managers",
                                    "guaranteeing higher wages than the market rate",
                                ],
                                "answer": "giving workers ownership and a share of profits",
                                "explain": (
                                    "Ownership and profit-sharing are the defining features; "
                                    "cooperatives can still have managers and market-linked pay."
                                ),
                            },
                            {
                                "q": "Local processing increases value capture by…",
                                "options": [
                                    "adding manufacturing jobs and value inside the producing country",
                                    "reducing shipping costs alone",
                                    "eliminating all foreign investment",
                                ],
                                "answer": "adding manufacturing jobs and value inside the producing country",
                                "explain": (
                                    "Processing transforms raw material into higher-value goods "
                                    "and keeps the associated wages and profits locally."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "capstone",
            "title": "Capstone — The True Ledger Project",
            "summary": (
                "Students produce an economic flowchart showing extraction and ownership."
            ),
            "order": 6,
            "lessons": [
                {
                    "slug": "true-ledger-project",
                    "title": "The True Ledger Project",
                    "order": 13,
                    "minutes": 30,
                    "summary": (
                        "Economic flowchart showing who supplies, labors, owns, receives, "
                        "and pays the costs in a commodity chain."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "For the capstone, choose a real commodity — coffee, cocoa, "
                                "cobalt, or another product with a clear extraction history. "
                                "Produce a flowchart showing who supplies the resource, who "
                                "performs labor at each stage, who owns capital, who receives "
                                "revenue, and where environmental and social costs are placed."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Step 1: Identify the commodity and its origin country.",
                                "Step 2: Map each stage from extraction to consumer.",
                                "Step 3: Label owners, workers, and financiers at each stage.",
                                "Step 4: Annotate externalized costs and who bears them.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Flowchart structure",
                            "text": (
                                "Resource extraction → Primary processing → Export → "
                                "Secondary processing → Manufacturing → Distribution → Retail. "
                                "At each node, list the actor, ownership structure, "
                                "approximate revenue share, and externalized costs."
                            ),
                        },
                        {
                            "type": "tip",
                            "text": (
                                "A strong flowchart uses percentages or dollar estimates. "
                                "If exact figures are unavailable, use ranges and cite sources."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of the capstone project.",
                        "questions": [
                            {
                                "q": "The True Ledger Project asks students to map…",
                                "options": [
                                    "who owns capital, performs labor, and bears costs across a chain",
                                    "the chemical composition of a commodity",
                                    "the historical price of one stock",
                                ],
                                "answer": "who owns capital, performs labor, and bears costs across a chain",
                                "explain": (
                                    "The project's purpose is structural understanding of "
                                    "extraction — not price analysis or chemistry."
                                ),
                            },
                            {
                                "q": "Annotating externalized costs on a ledger is important because it…",
                                "options": [
                                    "reveals who pays the hidden price of production",
                                    "improves the commodity's taste or quality",
                                    "eliminates the need for a conclusion",
                                ],
                                "answer": "reveals who pays the hidden price of production",
                                "explain": (
                                    "Externalized costs are invisible in market prices but "
                                    "real in human and environmental impact."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
    ],
}
