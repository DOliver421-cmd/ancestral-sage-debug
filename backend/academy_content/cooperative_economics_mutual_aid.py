"""Cooperative Economics and Mutual Aid Networks (published course).

Students learn how communities create economic infrastructure through shared
ownership, pooled resources, mutual aid, cooperative enterprise, and community
finance. The course covers historical mutual aid societies, credit unions,
worker cooperatives, land trusts, and community capital.
"""

COOPERATIVE_ECONOMICS_MUTUAL_AID = {
    "slug": "cooperative-economics-mutual-aid",
    "title": "Cooperative Economics and Mutual Aid Networks",
    "summary": (
        "How communities build economic infrastructure through shared ownership, "
        "pooled resources, mutual aid, cooperative enterprise, and community finance."
    ),
    "description": (
        "Students learn how communities create economic infrastructure through shared "
        "ownership, pooled resources, mutual aid, cooperative enterprise, and community "
        "finance. The course covers historical mutual aid societies, credit unions, "
        "worker cooperatives, land trusts, and community capital."
    ),
    "subject": "entrepreneurship",
    "subject_label": "Entrepreneurship",
    "track": "entrepreneurship",
    "tracks": ["entrepreneurship", "scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": (
        "High school students and adults interested in cooperative economics "
        "and community enterprise."
    ),
    "est_hours": 15,
    "passing_score": 80,
    "learning_objectives": [
        "Define cooperative economics and mutual aid.",
        "Analyze historical mutual aid institutions.",
        "Explain credit union structure and benefits.",
        "Describe worker cooperative governance and compensation.",
        "Explain consumer cooperative models.",
        "Analyze land cooperative and community land trust structures.",
        "Describe community capital mechanisms.",
        "Build a cooperative mission and ownership model.",
        "Construct a basic cooperative financial model.",
        "Explain cooperative governance and conflict resolution.",
        "Create a miniature cooperative business plan.",
    ],
    "units": [
        {
            "slug": "foundations",
            "title": "Foundations",
            "summary": "Core concepts of cooperative economics and mutual aid.",
            "order": 1,
            "lessons": [
                {
                    "slug": "what-is-cooperative-economics",
                    "title": "What Is Cooperative Economics?",
                    "order": 1,
                    "minutes": 20,
                    "summary": (
                        "Individual ownership versus cooperative ownership, collective "
                        "decision-making, and shared risk."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Cooperative economics is the study of how people organize "
                                "economic activity collectively rather than through "
                                "individual ownership. In a cooperative, members pool "
                                "resources, share profits, and make decisions together. "
                                "This model distributes risk and reward more equitably "
                                "across the group."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Individual ownership: one person controls capital, profit, and decisions.",
                                "Cooperative ownership: members jointly control capital and decisions.",
                                "Collective decision-making: votes are typically one-member-one-vote.",
                                "Shared risk: losses and gains are distributed across members.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Compare ownership models",
                            "text": (
                                "Pick one product or service you use regularly. "
                                "Compare how it might be organized under individual ownership "
                                "versus a cooperative. List two advantages and two disadvantages "
                                "of each model."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of cooperative economics.",
                        "questions": [
                            {
                                "q": "What is the main decision rule in most cooperatives?",
                                "options": [
                                    "one-member-one-vote",
                                    "one-dollar-one-vote",
                                    "owner decides alone",
                                ],
                                "answer": "one-member-one-vote",
                                "explain": (
                                    "Cooperatives typically use one-member-one-vote so that "
                                    "control is not tied to wealth."
                                ),
                            },
                            {
                                "q": "Shared risk means…",
                                "options": [
                                    "losses and gains are spread across members",
                                    "only the owner bears all risk",
                                    "risk is eliminated entirely",
                                ],
                                "answer": "losses and gains are spread across members",
                                "explain": (
                                    "Pooling resources means members share both the upside and "
                                    "the downside of the enterprise."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "historical-mutual-aid",
                    "title": "Historical Mutual Aid",
                    "order": 2,
                    "minutes": 18,
                    "summary": (
                        "Mutual aid societies, burial societies, community organizations, "
                        "and Black economic institutions."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Long before modern welfare systems, communities relied on "
                                "mutual aid — voluntary cooperation to meet shared needs. "
                                "Burial societies, benevolent associations, and rotating "
                                "savings groups provided safety nets that formal institutions "
                                "denied to many. These networks were especially vital in Black "
                                "and immigrant communities excluded from mainstream finance."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Burial societies pooled dues to cover funeral costs for members.",
                                "Benevolent associations offered sickness benefits and mutual support.",
                                "Rotating savings and credit associations (ROSCAs) provided access to capital.",
                                "Black mutual aid institutions built schools, hospitals, and banks.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Case study: Free African Society",
                            "text": (
                                "Founded in 1787 by Richard Allen and Absalom Jones in Philadelphia, "
                                "the Free African Society provided burial assistance, care for the "
                                "sick, and support for widows and orphans when mainstream institutions "
                                "refused service."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Investigate a local society",
                            "text": (
                                "Research one historical mutual aid society in your area or a "
                                "region you study. Write three sentences on who it served and "
                                "what needs it met."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of historical mutual aid.",
                        "questions": [
                            {
                                "q": "Mutual aid is best defined as…",
                                "options": [
                                    "voluntary cooperation to meet shared community needs",
                                    "government welfare programs",
                                    "charity from wealthy donors",
                                ],
                                "answer": "voluntary cooperation to meet shared community needs",
                                "explain": (
                                    "Mutual aid is organized by the community itself, not imposed "
                                    "from above or dependent on charity."
                                ),
                            },
                            {
                                "q": "The Free African Society was founded mainly to…",
                                "options": [
                                    "provide burial, sickness, and widow support",
                                    "run for-profit businesses",
                                    "lobby Congress for voting rights",
                                ],
                                "answer": "provide burial, sickness, and widow support",
                                "explain": (
                                    "It created a safety net through mutual dues and member care "
                                    "when mainstream institutions excluded Black residents."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "financial-cooperatives",
            "title": "Financial Cooperatives",
            "summary": "Credit unions, rotating savings, and community capital.",
            "order": 2,
            "lessons": [
                {
                    "slug": "credit-unions",
                    "title": "Credit Unions",
                    "order": 3,
                    "minutes": 18,
                    "summary": (
                        "Savings, lending, member ownership, and interest in credit unions."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "A credit union is a member-owned financial cooperative. "
                                "People deposit money, which is then lent to other members "
                                "at reasonable rates. Profits return to members as lower "
                                "fees, better rates, or community services. Unlike commercial "
                                "banks, credit unions exist to serve members rather than "
                                "extract profit for shareholders."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Members are both owners and customers.",
                                "Surplus income is returned to members or the community.",
                                "Governance follows one-member-one-vote.",
                                "Interest rates on loans are usually lower than commercial banks.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Model a credit union",
                            "text": (
                                "Imagine 20 members each save $50 per month. The credit union "
                                "pools $1,000 monthly. If 4 members each need a $250 loan, "
                                "calculate how much surplus remains for emergency lending."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of credit unions.",
                        "questions": [
                            {
                                "q": "Who owns a credit union?",
                                "options": [
                                    "its depositing members",
                                    "outside shareholders",
                                    "the federal government",
                                ],
                                "answer": "its depositing members",
                                "explain": (
                                    "Membership equals ownership in a credit union; each member "
                                    "has an equal voice."
                                ),
                            },
                            {
                                "q": "Credit union profits are mainly used to…",
                                "options": [
                                    "lower member fees or fund community programs",
                                    "pay dividends to wealthy investors",
                                    "expand executive bonuses",
                                ],
                                "answer": "lower member fees or fund community programs",
                                "explain": (
                                    "Surplus is returned to members or reinvested in the community, "
                                    "not extracted as investor profit."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "community-capital",
                    "title": "Community Capital",
                    "order": 4,
                    "minutes": 18,
                    "summary": (
                        "Savings circles, community investment, and local lending."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Community capital refers to money pooled, managed, and "
                                "circulated within a community. Rotating savings and credit "
                                "associations (ROSCAs), known as susus, chit funds, or "
                                "tandas depending on the culture, allow members to contribute "
                                "regularly and receive lump-sum payouts in turn. The money "
                                "stays local, building wealth from within."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "ROSCA: members contribute a fixed amount each period; one member receives the pool.",
                                "Community investment: local residents fund neighborhood projects.",
                                "Local lending: small loans issued by community groups, not distant banks.",
                                "Trust and social pressure replace formal collateral.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Run a susu simulation",
                            "text": (
                                "Five friends agree to contribute $40 monthly. Each month one "
                                "person takes the $200 pool. Simulate three rounds and calculate "
                                "how much each person contributes in total and who benefits first."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of community capital.",
                        "questions": [
                            {
                                "q": "A ROSCA is…",
                                "options": [
                                    "a group savings-and-payout system with no outside bank",
                                    "a type of high-interest payday loan",
                                    "a stock-market investment club",
                                ],
                                "answer": "a group savings-and-payout system with no outside bank",
                                "explain": (
                                    "Members pool money and rotate receiving the full contribution "
                                    "total, relying on trust rather than banks."
                                ),
                            },
                            {
                                "q": "Community capital keeps wealth…",
                                "options": [
                                    "circulating inside the community",
                                    "flowing to distant corporate headquarters",
                                    "tied up in real estate only",
                                ],
                                "answer": "circulating inside the community",
                                "explain": (
                                    "Because the money is raised, managed, and lent locally, "
                                    "it multiplies benefits within the community."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "enterprise-cooperatives",
            "title": "Enterprise Cooperatives",
            "summary": "Worker, consumer, and land cooperative models.",
            "order": 3,
            "lessons": [
                {
                    "slug": "worker-cooperatives",
                    "title": "Worker Cooperatives",
                    "order": 5,
                    "minutes": 18,
                    "summary": (
                        "Ownership, governance, compensation, and profit distribution "
                        "in worker co-ops."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "In a worker cooperative, the people who do the work also own "
                                "the business. Each worker-member typically has an equal vote "
                                "regardless of hours invested. Compensation often follows "
                                "formulas that narrow pay ratios, and profits are distributed "
                                "according to patronage — how much each member contributed to "
                                "the enterprise through labor."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Worker-members own the business and control its direction.",
                                "One-member-one-vote prevents domination by a small investor class.",
                                "Patronage refunds distribute profits based on labor contribution.",
                                "Democratic governance: members elect the board and major policies.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Design a governance structure",
                            "text": (
                                "Sketch a simple governance chart for a worker cooperative "
                                "with 15 employees. Show how decisions flow from members to "
                                "a board and then to management, and explain how recall works."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of worker cooperatives.",
                        "questions": [
                            {
                                "q": "In a worker cooperative, profits are distributed based on…",
                                "options": [
                                    "how much labor each member contributed",
                                    "who invested the most cash",
                                    "seniority alone",
                                ],
                                "answer": "how much labor each member contributed",
                                "explain": (
                                    "Patronage refunds tie profit sharing to actual work performed, "
                                    "not capital invested."
                                ),
                            },
                            {
                                "q": "Why do worker co-ops often limit pay ratios?",
                                "options": [
                                    "to reduce inequality between highest and lowest earners",
                                    "to pay investors more than workers",
                                    "to comply with federal law",
                                ],
                                "answer": "to reduce inequality between highest and lowest earners",
                                "explain": (
                                    "Narrow pay ratios keep wealth distribution aligned with "
                                    "cooperative values."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "consumer-cooperatives",
                    "title": "Consumer Cooperatives",
                    "order": 6,
                    "minutes": 18,
                    "summary": (
                        "Purchasing power, bulk buying, and member benefits in consumer co-ops."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Consumer cooperatives are owned by the people who buy from "
                                "them. By pooling demand, members gain collective bargaining "
                                "power to lower prices, improve quality, or influence sourcing. "
                                "Grocery co-ops, housing co-ops, and utility co-ops all follow "
                                "this pattern: members govern, and surplus returns to members "
                                "as discounts, better services, or community grants."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Bulk buying power reduces per-unit costs for members.",
                                "Members vote on product selection, pricing, and policies.",
                                "Surplus can become member dividends or community investments.",
                                "Focus: meeting member needs rather than maximizing external profit.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Calculate bulk savings",
                            "text": (
                                "If 50 households each need $30 of staples monthly, calculate "
                                "the total monthly market. If a cooperative achieves a 15% "
                                "savings through bulk buying, how much does each household save?"
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of consumer cooperatives.",
                        "questions": [
                            {
                                "q": "Who owns a consumer cooperative?",
                                "options": [
                                    "the customers who shop there",
                                    "distant shareholders",
                                    "the local government",
                                ],
                                "answer": "the customers who shop there",
                                "explain": (
                                    "Customer-members are the owners; governance is democratic "
                                    "among them."
                                ),
                            },
                            {
                                "q": "A key advantage of consumer co-ops is…",
                                "options": [
                                    "collective bargaining power through pooled demand",
                                    "higher prices than retail chains",
                                    "decisions made by outside investors",
                                ],
                                "answer": "collective bargaining power through pooled demand",
                                "explain": (
                                    "Pooling demand lets members negotiate better terms and "
                                    "redirect surplus back into the community."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "land-cooperatives",
                    "title": "Land Cooperatives",
                    "order": 7,
                    "minutes": 18,
                    "summary": (
                        "Shared ownership, community land, and agricultural cooperatives."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Land cooperatives and community land trusts (CLTs) separate "
                                "land ownership from use. A CLT holds land collectively while "
                                "members own or lease the homes or farms on it. This removes "
                                "land from speculative markets, keeping it affordable for "
                                "generations. Agricultural co-ops use the same principle: "
                                "shared land, shared equipment, and collective marketing."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "CLT: a nonprofit holds land for community benefit; residents own structures.",
                                "Leaseholds keep housing affordable by capping resale prices.",
                                "Farmers may pool land to share equipment and distribution.",
                                "Removes land from speculation, preserving it for productive use.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Design a land trust",
                            "text": (
                                "Sketch a simple CLT charter for an urban neighborhood. "
                                "List three rules that would prevent speculative resale while "
                                "protecting resident equity."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of land cooperatives.",
                        "questions": [
                            {
                                "q": "In a community land trust, who owns the land?",
                                "options": [
                                    "the trust holds it collectively",
                                    "each resident owns their parcel outright",
                                    "the state government",
                                ],
                                "answer": "the trust holds it collectively",
                                "explain": (
                                    "Separating land from structures keeps property affordable "
                                    "and community-controlled."
                                ),
                            },
                            {
                                "q": "A leasehold in a CLT typically…",
                                "options": [
                                    "caps resale price to keep housing affordable",
                                    "allows unlimited market-rate flipping",
                                    "transfers full ownership to the resident immediately",
                                ],
                                "answer": "caps resale price to keep housing affordable",
                                "explain": (
                                    "Capping resale preserves affordability for future buyers "
                                    "while still allowing resident equity within the agreed range."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "building-a-cooperative",
            "title": "Building a Cooperative",
            "summary": "Mission, governance, ownership, and financial modeling.",
            "order": 4,
            "lessons": [
                {
                    "slug": "cooperative-design",
                    "title": "Building a Cooperative",
                    "order": 8,
                    "minutes": 20,
                    "summary": (
                        "Mission, members, product or service, ownership, and governance."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Every cooperative begins with a clear mission and a defined "
                                "member base. Before forming legal entities, founders should "
                                "articulate what the cooperative will do, who will own it, "
                                "how decisions will be made, and how value will be distributed. "
                                "A strong mission aligns members and attracts support."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Mission statement: what need does the cooperative meet?",
                                "Membership: who qualifies, how to join, and what dues are required.",
                                "Product or service: what will the cooperative sell or provide?",
                                "Governance: voting rules, board structure, and officer roles.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Write a mission statement",
                            "text": (
                                "Draft a mission statement for a cooperative you would actually "
                                "join. Include the target member, the core activity, and one "
                                "measure of success."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of cooperative design.",
                        "questions": [
                            {
                                "q": "The first step in building a cooperative is…",
                                "options": [
                                    "clarifying the mission and member base",
                                    "filing corporate paperwork",
                                    "raising outside investor capital",
                                ],
                                "answer": "clarifying the mission and member base",
                                "explain": (
                                    "A clear mission guides governance, membership rules, and "
                                    "financial choices."
                                ),
                            },
                            {
                                "q": "Cooperatives differ from investor corporations primarily in…",
                                "options": [
                                    "their control by members rather than outside shareholders",
                                    "having no legal structure",
                                    "being forbidden from earning revenue",
                                ],
                                "answer": "their control by members rather than outside shareholders",
                                "explain": (
                                    "Member control, not investor profit, is the defining feature."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "cooperative-financial-model",
                    "title": "Cooperative Financial Model",
                    "order": 9,
                    "minutes": 20,
                    "summary": (
                        "Revenue model, expense model, member contribution, reserve, "
                        "and distribution model."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "A cooperative financial model tracks how money enters and "
                                "leaves the enterprise. Revenue comes from sales, fees, or "
                                "member contributions. Expenses cover operations, reserves, "
                                "and member services. After expenses, surplus may be returned "
                                "to members, held in reserves, or reinvested according to "
                                "member votes."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Revenue: sales, membership dues, service fees.",
                                "Expenses: operations, wages, supplies, facility costs.",
                                "Reserve: retained savings for emergencies or expansion.",
                                "Distribution: patronage refunds, dividends, or community reinvestment.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Build a simple model",
                            "text": (
                                "Create a one-page financial model for a cooperative with "
                                "20 members each paying $20 monthly. Estimate monthly expenses "
                                "of $300 and project what remains for reserves and member refunds."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of cooperative finance.",
                        "questions": [
                            {
                                "q": "In a cooperative, surplus after expenses is…",
                                "options": [
                                    "returned to members or reinvested by member vote",
                                    "sent entirely to outside investors",
                                    "required to be donated to charity",
                                ],
                                "answer": "returned to members or reinvested by member vote",
                                "explain": (
                                    "Surplus belongs to the cooperative and its members; they "
                                    "decide its use democratically."
                                ),
                            },
                            {
                                "q": "A reserve in a cooperative is used for…",
                                "options": [
                                    "covering unexpected costs and funding growth",
                                    "paying investor dividends",
                                    "buying luxury offices",
                                ],
                                "answer": "covering unexpected costs and funding growth",
                                "explain": (
                                    "Reserves stabilize the cooperative and finance future member "
                                    "benefits or expansion."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
        {
            "slug": "governance-and-capstone",
            "title": "Governance and Capstone",
            "summary": (
                "Voting, leadership, transparency, accountability, and the capstone project."
            ),
            "order": 5,
            "lessons": [
                {
                    "slug": "governance-and-conflict",
                    "title": "Governance and Conflict",
                    "order": 10,
                    "minutes": 18,
                    "summary": (
                        "Voting, leadership, transparency, and accountability in cooperatives."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Cooperatives rely on democratic governance to remain "
                                "accountable to members. Regular meetings, transparent "
                                "records, recallable leaders, and clear dispute-resolution "
                                "processes keep power from concentrating. Many co-ops use "
                                "consensus, majority vote, or delegated boards with strict "
                                "mandates."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Transparency: open books and published meeting minutes.",
                                "Recall: leaders can be removed by member vote.",
                                "Conflict resolution: mediation, arbitration, or member review panels.",
                                "Rotating leadership prevents entrenchment.",
                            ],
                        },
                        {
                            "type": "example",
                            "title": "Case study: conflict resolution",
                            "text": (
                                "A worker cooperative faced a dispute over workload distribution. "
                                "Members used a mediation panel of peers to clarify roles, "
                                "adjust the workload formula, and publish the new policy — "
                                "restoring trust without removing any members."
                            ),
                        },
                        {
                            "type": "activity",
                            "title": "Role-play a dispute",
                            "text": (
                                "Imagine two members disagree over profit distribution. "
                                "Write a short mediation script that leads to a fair outcome "
                                "acceptable to both."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of cooperative governance.",
                        "questions": [
                            {
                                "q": "Democratic governance in cooperatives is mainly protected by…",
                                "options": [
                                    "transparent records, recallable leaders, and member votes",
                                    "a single powerful manager",
                                    "written contracts with outside lawyers",
                                ],
                                "answer": "transparent records, recallable leaders, and member votes",
                                "explain": (
                                    "Built-in checks — transparency, recall, and democratic vote — "
                                    "keep power accountable to the membership."
                                ),
                            },
                            {
                                "q": "A mediation panel in a cooperative…",
                                "options": [
                                    "helps members resolve disputes through peer agreement",
                                    "fires members without due process",
                                    "is appointed by outside investors",
                                ],
                                "answer": "helps members resolve disputes through peer agreement",
                                "explain": (
                                    "Mediation uses member peers to restore relationships and "
                                    "clarify policies."
                                ),
                            },
                        ],
                    },
                },
                {
                    "slug": "capstone-build-a-cooperative",
                    "title": "Capstone: Build a Cooperative",
                    "order": 11,
                    "minutes": 30,
                    "summary": (
                        "Students create a complete miniature cooperative business plan."
                    ),
                    "learn": [
                        {
                            "type": "p",
                            "text": (
                                "Your capstone is a full cooperative business plan. It should "
                                "include a mission statement, member profile, product or service "
                                "description, ownership model, governance structure, and basic "
                                "financial projections. This is your blueprint for a real-world "
                                "cooperative venture."
                            ),
                        },
                        {
                            "type": "list",
                            "items": [
                                "Mission: one paragraph explaining the cooperative's purpose.",
                                "Members: who joins, how many, and what dues or contributions are required.",
                                "Product or service: what is sold or provided and to whom.",
                                "Ownership: how ownership is structured and transferred.",
                            ],
                        },
                        {
                            "type": "list",
                            "items": [
                                "Governance: voting rules, board composition, and officer roles.",
                                "Financial projections: revenue sources, monthly expenses, reserve plan.",
                                "Distribution: how surplus will be shared or reinvested.",
                                "Conflict resolution: how disputes will be handled.",
                            ],
                        },
                        {
                            "type": "activity",
                            "title": "Draft your plan",
                            "text": (
                                "Write the full cooperative business plan using the eight sections "
                                "above. Aim for one to two pages, clear enough that new members "
                                "could understand and join."
                            ),
                        },
                    ],
                    "check": {
                        "prompt": "Check your understanding of the capstone requirements.",
                        "questions": [
                            {
                                "q": "A cooperative business plan must include all of the following EXCEPT…",
                                "options": [
                                    "a guaranteed outside investor contract",
                                    "a mission statement",
                                    "a governance structure",
                                ],
                                "answer": "a guaranteed outside investor contract",
                                "explain": (
                                    "The plan requires mission, governance, ownership, and "
                                    "financial sections. Outside investor contracts are optional "
                                    "and often contrary to cooperative principles."
                                ),
                            },
                            {
                                "q": "Financial projections in the capstone should cover…",
                                "options": [
                                    "revenue, expenses, reserves, and surplus distribution",
                                    "only projected profits for investors",
                                    "only the first month's costs",
                                ],
                                "answer": "revenue, expenses, reserves, and surplus distribution",
                                "explain": (
                                    "A complete financial model projects the full cycle of income, "
                                    "costs, savings, and how surplus is shared."
                                ),
                            },
                        ],
                    },
                },
            ],
        },
    ],
}
