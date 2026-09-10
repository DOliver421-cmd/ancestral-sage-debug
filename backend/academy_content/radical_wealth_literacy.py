"""Radical Wealth Literacy: Deconstructing Capital, Credit, and Extraction (published course)."""

RADICAL_WEALTH_LITERACY = {
    "slug": "radical-wealth-literacy",
    "title": "Radical Wealth Literacy: Deconstructing Capital, Credit, and Extraction",
    "summary": "The mechanics of wealth extraction, predatory lending, redlining, and generational asset stripping — with asset protection, debt leverage, and community capital retention.",
    "description": (
        "Replaces superficial financial advice with a structural critique of modern banking. "
        "Students learn asset protection, debt leverage, community capital retention, and how to "
        "build a personal wealth strategy based on evidence rather than ideology."
    ),
    "subject": "entrepreneurship",
    "subject_label": "Entrepreneurship",
    "track": "career",
    "tracks": ["career", "scholar"],
    "grades": ["9", "10", "11", "12"],
    "grade_label": "Grades 9–12",
    "status": "published",
    "audience": "High school students and adults studying personal finance and economic empowerment.",
    "est_hours": 18,
    "passing_score": 80,
    "learning_objectives": [
        "Distinguish income from wealth.",
        "Explain how capital and ownership work.",
        "Analyze credit scores, interest, and debt structures.",
        "Calculate compound interest effects on borrowing and saving.",
        "Identify predatory lending practices.",
        "Explain redlining and credit access disparities.",
        "Analyze asset-stripping mechanisms.",
        "Evaluate insurance and risk-management tools.",
        "Explain asset-protection strategies.",
        "Distinguish productive debt from high-risk debt.",
        "Describe community capital retention strategies.",
        "Build a personal five-year wealth plan.",
        "Analyze a household/business for financial leaks and propose improvements.",
    ],
    "units": [
        {
            "slug": "financial-foundations",
            "title": "Financial Foundations",
            "summary": "Income, assets, liabilities, capital, and ownership.",
            "order": 1,
            "lessons": [
                {
                    "slug": "income-is-not-wealth",
                    "title": "Income Is Not Wealth",
                    "order": 1,
                    "minutes": 20,
                    "summary": "Income, assets, liabilities, net worth, and cash flow.",
                    "learn": [
                        {"type": "p", "text": "Income is money you earn — a paycheck, gig payout, or dividend. Wealth is what you keep. A person earning $200,000 who spends it all is not wealthy. Wealth equals assets minus liabilities. Cash flow is the monthly difference between what comes in and what goes out. High cash flow builds wealth only if surplus is directed to assets."},
                        {"type": "list", "items": [
                            "Income = money received (wages, business profit, rent).",
                            "Assets = things you own that hold or grow value (home, stocks, business equity).",
                            "Liabilities = what you owe (mortgage, car note, credit card).",
                            "Net worth = assets minus liabilities — the true wealth measure.",
                        ]},
                        {"type": "activity", "title": "Calculate your net worth", "text": "List every asset and liability you can identify. Add assets, subtract liabilities, and compute your net worth. Repeat in six months to track change."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of income versus wealth.",
                        "questions": [
                            {"q": "Which is the best measure of wealth?", "options": ["net worth", "annual salary", "monthly cash flow"], "answer": "net worth", "explain": "Net worth captures what you own minus what you owe — the true wealth measure."},
                            {"q": "High income guarantees wealth because…", "options": ["it does not — spending all income leaves no assets", "it always exceeds expenses", "it is automatically invested"], "answer": "it does not — spending all income leaves no assets", "explain": "Wealth is built from surplus directed into assets, not income alone."},
                        ],
                    },
                },
                {
                    "slug": "how-capital-works",
                    "title": "How Capital Works",
                    "order": 2,
                    "minutes": 18,
                    "summary": "Ownership, investment, returns, and risk.",
                    "learn": [
                        {"type": "p", "text": "Capital is money or assets put to work to generate more money. Owners of capital earn returns — profits, rents, dividends, interest. Workers sell labor for wages. The gap between capital returns and wage growth over decades is a core driver of wealth inequality. Understanding ownership structures — sole proprietorship, partnership, LLC, corporation — determines who keeps profits, who bears losses, and how assets are protected."},
                        {"type": "list", "items": [
                            "Capital owners receive returns without trading time.",
                            "Ownership structure affects tax treatment, liability, and succession.",
                            "Investment risk correlates with potential return — safer assets yield less.",
                            "Compounding returns over time are the engine of long-term wealth.",
                        ]},
                        {"type": "example", "title": "Ownership structures", "text": "A solo contractor operating as an LLC separates business liabilities from personal assets. A sole proprietor's personal assets are exposed to business claims."},
                        {"type": "activity", "title": "Map ownership structures", "text": "Draw three ownership structures (sole proprietor, LLC, corporation) and list how profits, taxes, and liability differ across them."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of capital and ownership.",
                        "questions": [
                            {"q": "Capital generates returns primarily through…", "options": ["ownership of productive assets", "working more hours", "borrowing money"], "answer": "ownership of productive assets", "explain": "Capital owners earn returns from ownership, not from trading time."},
                            {"q": "An LLC mainly helps owners by…", "options": ["limiting personal liability for business claims", "eliminating all taxes", "guaranteeing profits"], "answer": "limiting personal liability for business claims", "explain": "An LLC creates a legal separation between business and personal assets."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "credit-and-debt",
            "title": "Credit and Debt",
            "summary": "Credit scores, interest, APR, and compound borrowing costs.",
            "order": 2,
            "lessons": [
                {
                    "slug": "credit-mechanics",
                    "title": "Credit",
                    "order": 3,
                    "minutes": 18,
                    "summary": "Credit scores, interest, APR, secured versus unsecured debt.",
                    "learn": [
                        {"type": "p", "text": "A credit score is a numerical risk estimate lenders use to predict repayment. FICO scores range from 300 to 850. Five factors drive the score: payment history (35%), amounts owed (30%), length of credit history (15%), new credit (10%), and credit mix (10%). Interest is the cost of borrowing; APR (annual percentage rate) expresses total borrowing cost including fees. Secured debt is backed by collateral; unsecured debt relies only on creditworthiness."},
                        {"type": "list", "items": [
                            "Payment history: paying on time is the single most important factor.",
                            "Credit utilization: keep balances below 30% of available credit.",
                            "Secured debt examples: mortgage, auto loan.",
                            "Unsecured debt examples: credit cards, personal loans.",
                        ]},
                        {"type": "activity", "title": "Score analysis", "text": "Pull a free credit report or use a sample score. Identify which factors most affected your score and write one action to improve it this quarter."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of credit mechanics.",
                        "questions": [
                            {"q": "Payment history accounts for roughly…", "options": ["35% of a FICO score", "10%", "5%"], "answer": "35% of a FICO score", "explain": "Payment history is the largest single factor in most credit scoring models."},
                            {"q": "Which debt is secured?", "options": ["mortgage", "credit card balance", "medical bill"], "answer": "mortgage", "explain": "Secured debt is backed by collateral — a mortgage is backed by the home."},
                        ],
                    },
                },
                {
                    "slug": "compound-interest",
                    "title": "Compound Interest",
                    "order": 4,
                    "minutes": 18,
                    "summary": "Borrowing costs, savings growth, and investment growth.",
                    "learn": [
                        {"type": "p", "text": "Compound interest means interest earns interest. When you borrow, compounding works against you: a $10,000 loan at 18% over five years costs far more than simple interest because each month's unpaid interest is added to the balance. When you save or invest, compounding works for you — returns generate their own returns. The earlier you start, the more time compounding has to grow."},
                        {"type": "list", "items": [
                            "Savings formula: A = P(1 + r/n)^(nt)",
                            "Borrowing formula: same formula, but r is your loan APR",
                            "Higher frequency compounding increases total cost for borrowers",
                            "A 1% difference in return matters most over long time horizons",
                        ]},
                        {"type": "activity", "title": "Calculate the cost", "text": "Compute the total interest on a $5,000 loan at 15% APR over 3 years with monthly compounding. Then compute the same loan at 8% APR. Record the difference."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of compound interest.",
                        "questions": [
                            {"q": "With monthly compounding, a borrower…", "options": ["pays interest on previously unpaid interest", "pays less total interest", "never pays interest"], "answer": "pays interest on previously unpaid interest", "explain": "Monthly compounding adds unpaid interest to the principal, increasing total cost."},
                            {"q": "Starting to invest early helps because…", "options": ["compounding has more time to grow", "early investments are risk-free", "fees are lower"], "answer": "compounding has more time to grow", "explain": "Time in the market lets compounding multiply returns across years."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "extraction-and-access",
            "title": "Extraction and Access",
            "summary": "Predatory lending, redlining, and asset-stripping mechanisms.",
            "order": 3,
            "lessons": [
                {
                    "slug": "predatory-lending",
                    "title": "Predatory Lending",
                    "order": 5,
                    "minutes": 18,
                    "summary": "Payday lending, high-cost credit, fees, and debt cycles.",
                    "learn": [
                        {"type": "p", "text": "Predatory lending targets people with limited options — high fees, balloon payments, prepayment penalties, and loan-flipping that extends repayment without reducing principal. Payday loans carry APRs that can exceed 400%. Borrowers who need quick cash often borrow again before the first loan is repaid, creating a cycle. The true cost of any loan is its APR, not its advertised fee."},
                        {"type": "list", "items": [
                            "Payday loan: small, short-term loan with high APR — meant to bridge to next paycheck.",
                            "Loan flipping: refinancing to collect new fees without helping the borrower.",
                            "Prepayment penalties: fees for paying off early, locking borrowers in.",
                            "Read APR, not fee — APR is the apples-to-apples cost measure.",
                        ]},
                        {"type": "activity", "title": "Compare two loans", "text": "Compare a $500 payday loan with a 390% APR and a $500 credit union installment loan at 28% APR over 6 months. Calculate total cost in each case."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of predatory lending.",
                        "questions": [
                            {"q": "The true cost of a loan is best measured by…", "options": ["APR", "the origination fee", "the monthly payment"], "answer": "APR", "explain": "APR captures the total annual cost including fees, allowing comparison across products."},
                            {"q": "Payday loans are considered predatory mainly because…", "options": ["their APRs can exceed 400%", "they require collateral", "they are only for businesses"], "answer": "their APRs can exceed 400%", "explain": "The extreme cost traps borrowers in cycles of refinancing."},
                        ],
                    },
                },
                {
                    "slug": "redlining-and-credit-access",
                    "title": "Redlining and Credit Access",
                    "order": 6,
                    "minutes": 18,
                    "summary": "Historical lending discrimination, mortgage access, and neighborhood investment.",
                    "learn": [
                        {"type": "p", "text": "Redlining is the practice of denying loans or insurance to residents of certain neighborhoods based on race or ethnicity rather than creditworthiness. The Home Owners' Loan Corporation (HOLC) in the 1930s graded neighborhoods on maps — green for 'best,' red for 'hazardous' — and banks refused to lend in red zones. Disinvestment followed: lower property values, less tax revenue, underfunded schools, and fewer services. Modern algorithms can replicate the same pattern under a different name."},
                        {"type": "list", "items": [
                            "HOLC 'redlining' maps created residential credit deserts.",
                            "Redlined neighborhoods still show lower homeownership and credit scores today.",
                            "Algorithmic lending can embed historical patterns without explicit racial language.",
                            "Fair lending law prohibits discrimination by race, color, religion, or national origin.",
                        ]},
                        {"type": "activity", "title": "Map the disparity", "text": "Find a current HOLC map for your city online. Compare it to a current home-price map. Note three patterns that persisted across decades."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of redlining and credit access.",
                        "questions": [
                            {"q": "Redlining originally referred to…", "options": ["denying loans in specific neighborhoods based on race", "raising interest rates for all borrowers", "requiring larger down payments everywhere"], "answer": "denying loans in specific neighborhoods based on race", "explain": "Banks literally drew red lines on maps around minority neighborhoods and refused to lend inside them."},
                            {"q": "A modern concern with algorithmic lending is…", "options": ["it may encode historical discrimination without explicit racial terms", "it always removes human bias", "it is prohibited in all cases"], "answer": "it may encode historical discrimination without explicit racial terms", "explain": "Algorithms trained on historical data can replicate past patterns even without racial inputs."},
                        ],
                    },
                },
                {
                    "slug": "asset-stripping",
                    "title": "Asset Stripping",
                    "order": 7,
                    "minutes": 18,
                    "summary": "Property loss, predatory contracts, forced sales, and economic displacement.",
                    "learn": [
                        {"type": "p", "text": "Asset stripping is the extraction of wealth from a community or household through mechanisms that transfer equity to outsiders. Tactics include contract-for-deed fraud, inflated property taxes, eminent domain abuse, blockbusting, and loan terms designed to force default. Gentrification can accelerate stripping when long-term residents are priced out and displaced. Each mechanism transfers ownership of an appreciating asset from a community member to an external party."},
                        {"type": "list", "items": [
                            "Contract-for-deed: buyer makes payments but does not gain title until the end — eviction risks losing all equity.",
                            "Inflated tax sales: rising property taxes force sales when owners cannot pay.",
                            "Blockbusting: speculators exploit fear to buy homes below market and resell.",
                            "Eminent domain abuse: government takes property for private development at below-market prices.",
                        ]},
                        {"type": "activity", "title": "Contract analysis", "text": "Read a sample contract-for-deed agreement. Identify at least three clauses that could disadvantage the buyer and explain what each one costs them."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of asset stripping.",
                        "questions": [
                            {"q": "Contract-for-deed risk is highest when…", "options": ["buyers lose all equity if evicted before full payment", "interest rates are low", "title transfers at closing"], "answer": "buyers lose all equity if evicted before full payment", "explain": "Without title, the buyer owns nothing until the final payment — eviction wipes out years of payments."},
                            {"q": "Asset stripping transfers wealth from…", "options": ["communities or households to external parties", "governments to taxpayers", "employers to employees"], "answer": "communities or households to external parties", "explain": "Every tactic described moves equity from the community to an outside actor."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "protection-and-strategy",
            "title": "Protection and Strategy",
            "summary": "Insurance, risk management, asset protection, and strategic debt.",
            "order": 4,
            "lessons": [
                {
                    "slug": "insurance-and-risk",
                    "title": "Insurance and Risk",
                    "order": 8,
                    "minutes": 18,
                    "summary": "Property, liability, business risk, and emergency reserves.",
                    "learn": [
                        {"type": "p", "text": "Insurance transfers financial risk to an insurer for a predictable premium. Without it, a single lawsuit, fire, or medical emergency can erase years of wealth. Key types: homeowners or renters insurance (property and liability), auto insurance, health insurance, disability insurance (replaces income if you cannot work), and umbrella policies (additional liability coverage). An emergency reserve — three to six months of expenses in liquid savings — is the first line of defense before insurance matters."},
                        {"type": "list", "items": [
                            "Liability insurance protects against lawsuits from injury or property damage.",
                            "Disability insurance replaces income if injury or illness prevents work.",
                            "Umbrella policies sit above auto and home coverage for large claims.",
                            "Emergency reserves prevent high-interest debt when unexpected costs hit.",
                        ]},
                        {"type": "activity", "title": "Needs analysis", "text": "List the insurance types relevant to your household. For each, write your current coverage and the gap between that coverage and your assets at risk."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of insurance and risk.",
                        "questions": [
                            {"q": "Disability insurance replaces…", "options": ["income if you cannot work", "property damage", "investment losses"], "answer": "income if you cannot work", "explain": "Disability insurance protects your earning capacity, your most important early-career asset."},
                            {"q": "An emergency reserve primarily prevents…", "options": ["high-interest debt when unexpected costs arise", "tax increases", "credit score drops"], "answer": "high-interest debt when unexpected costs arise", "explain": "Cash on hand avoids borrowing at predatory rates when emergencies hit."},
                        ],
                    },
                },
                {
                    "slug": "protecting-assets",
                    "title": "Protecting Assets",
                    "order": 9,
                    "minutes": 18,
                    "summary": "Ownership structures, documentation, contracts, recordkeeping, and professional advice.",
                    "learn": [
                        {"type": "p", "text": "Asset protection is about making it harder for a creditor or lawsuit to reach what you own. Strategies include proper titling (tenants by entirety, trusts), adequate insurance, clear contracts that limit liability, and meticulous recordkeeping so ownership is undisputed. Professional advice from an attorney or CPA is essential before implementing complex structures; do-it-yourself asset shielding can fail or trigger penalties."},
                        {"type": "list", "items": [
                            "Separate business and personal assets with an LLC or corporation.",
                            "Titling property as tenants by entirety (where available) protects it from individual creditors.",
                            "Trusts can shield assets from probate and certain claims.",
                            "Keep contracts, deeds, and insurance policies in a secure, organized system.",
                        ]},
                        {"type": "activity", "title": "Documentation checklist", "text": "Create a checklist of documents you would need to prove ownership of a vehicle, home, bank account, and business entity. Note where each is stored and who else has access."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of asset protection.",
                        "questions": [
                            {"q": "The primary purpose of separating business and personal assets is…", "options": ["limiting personal liability for business claims", "avoiding all taxes", "hiding assets from the IRS"], "answer": "limiting personal liability for business claims", "explain": "The legal separation protects personal wealth from business-related lawsuits."},
                            {"q": "DIY asset protection without legal advice is risky because…", "options": ["improper structures can fail or incur penalties", "lawyers are always required", "it is illegal everywhere"], "answer": "improper structures can fail or incur penalties", "explain": "Asset protection must comply with law; incorrect structures offer no protection and may carry penalties."},
                        ],
                    },
                },
                {
                    "slug": "debt-as-a-tool",
                    "title": "Debt as a Tool",
                    "order": 10,
                    "minutes": 18,
                    "summary": "Productive debt, consumer debt, high-risk debt, and strategic borrowing.",
                    "learn": [
                        {"type": "p", "text": "Not all debt is bad. Productive debt finances assets that generate value exceeding the cost of borrowing — a mortgage on a cash-flowing rental, a business loan for equipment that increases revenue, or student debt that raises lifetime earnings. Consumer debt — credit cards for depreciating purchases — is high-risk because the underlying asset loses value while interest accrues. Strategic borrowing means borrowing at rates lower than the expected return on the funded asset."},
                        {"type": "list", "items": [
                            "Productive debt: borrowed money funds an asset that appreciates or generates income.",
                            "Consumer debt: borrowed money funds consumption — the asset depreciates.",
                            "High-risk debt: high-APR unsecured loans with balloon or adjustable terms.",
                            "Test: if the borrowed asset's return exceeds the loan APR, the debt is productive.",
                        ]},
                        {"type": "activity", "title": "Classify your debt", "text": "List every outstanding debt. For each, write the APR, the asset it purchased, whether that asset appreciates, and whether the debt is productive, consumer, or high-risk."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of debt as a tool.",
                        "questions": [
                            {"q": "Productive debt is defined by…", "options": ["the borrowed asset generates returns above borrowing cost", "having the lowest interest rate", "being unsecured"], "answer": "the borrowed asset generates returns above borrowing cost", "explain": "Productive debt earns a return that exceeds its cost, building net worth over time."},
                            {"q": "Credit card balances are typically high-risk because…", "options": ["they fund depreciating purchases at high APR", "they are always secured by collateral", "their interest is tax-deductible"], "answer": "they fund depreciating purchases at high APR", "explain": "Credit cards charge high rates on purchases that immediately lose value."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "community-and-planning",
            "title": "Community and Planning",
            "summary": "Community capital retention and building a personal wealth plan.",
            "order": 5,
            "lessons": [
                {
                    "slug": "community-capital-retention",
                    "title": "Community Capital Retention",
                    "order": 11,
                    "minutes": 18,
                    "summary": "Local businesses, cooperative purchasing, reinvestment, and community ownership.",
                    "learn": [
                        {"type": "p", "text": "Wealth extraction happens at every scale — including community level. When residents spend money at chains or online platforms headquartered elsewhere, the profit leaves the community. Community capital retention keeps money circulating locally through independent businesses, credit unions, cooperative purchasing, and community land trusts. Local multipliers measure how many times a dollar is recirculated within a community before exiting. Studies consistently show higher local multipliers for independent businesses than for national chains."},
                        {"type": "list", "items": [
                            "Local multiplier: each dollar spent locally generates additional local economic activity.",
                            "Credit unions are member-owned and return profits to depositors as better rates.",
                            "Cooperatives distribute ownership and profits to members, not outside shareholders.",
                            "Community land trusts remove land from the speculative market, preserving affordability.",
                        ]},
                        {"type": "activity", "title": "Map local investment", "text": "List five categories of regular household spending. For each, find a locally owned alternative and calculate how much annual local wealth retention would increase if you switched."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of community capital retention.",
                        "questions": [
                            {"q": "A local multiplier measures…", "options": ["how many times a dollar recirculates locally", "the local tax rate", "property values"], "answer": "how many times a dollar recirculates locally", "explain": "Each local transaction re-spends money, creating additional rounds of economic activity."},
                            {"q": "Credit unions differ from banks mainly because…", "options": ["profits go to member-owners, not outside shareholders", "they offer lower rates on everything", "they are government-run"], "answer": "profits go to member-owners, not outside shareholders", "explain": "Credit unions return earnings to members through better rates and lower fees."},
                        ],
                    },
                },
                {
                    "slug": "personal-wealth-strategy",
                    "title": "Personal Wealth Strategy",
                    "order": 12,
                    "minutes": 20,
                    "summary": "Building a hypothetical five-year wealth plan.",
                    "learn": [
                        {"type": "p", "text": "A five-year wealth plan translates knowledge into action. Start with current net worth and cash flow. Set three concrete goals: an emergency reserve target, a debt-reduction sequence, and an asset-acquisition milestone. For each, identify the monthly amount required and a realistic source — reduced spending, income growth, or side income. Review quarterly and adjust. The plan is not a prediction; it is a decision-making framework that makes spending, saving, and investing intentional."},
                        {"type": "list", "items": [
                            "Step 1: calculate current net worth and monthly cash flow.",
                            "Step 2: set three specific five-year wealth goals.",
                            "Step 3: map required monthly savings or income for each goal.",
                            "Step 4: review quarterly and adjust for life changes.",
                        ]},
                        {"type": "activity", "title": "Write your five-year plan", "text": "Write one page covering current net worth, three five-year wealth goals, the monthly amount required for each, and the source of that money. Include one obstacle and one mitigation."},
                    ],
                    "check": {
                        "prompt": "Check your understanding of personal wealth strategy.",
                        "questions": [
                            {"q": "The first step in a wealth plan is…", "options": ["calculating current net worth and cash flow", "opening ten investment accounts", "borrowing money"], "answer": "calculating current net worth and cash flow", "explain": "You cannot plan from where you are if you do not measure where you are now."},
                            {"q": "A five-year wealth plan works best when…", "options": ["reviewed quarterly and adjusted", "written once and never touched", "made of vague dreams only"], "answer": "reviewed quarterly and adjusted", "explain": "Regular review turns a plan into a decision-making system that adapts to real life."},
                        ],
                    },
                },
                {
                    "slug": "wealth-literacy-capstone",
                    "title": "Wealth Literacy Case Study",
                    "order": 13,
                    "minutes": 30,
                    "summary": "Analyze a fictional household or business for financial leaks and propose improvements.",
                    "learn": [
                        {"type": "p", "text": "The capstone applies every unit of this course to one realistic scenario. You will receive a profile of a fictional household or business with income, debt, assets, insurance gaps, spending patterns, and credit history. Your job is to identify financial leaks — spending, borrowing costs, missing protections, or extraction mechanisms — and propose a realistic improvement strategy. Recommendations must be specific, legally and financially feasible, and ordered by impact and urgency."},
                        {"type": "list", "items": [
                            "Review every income stream, expense, debt, and asset.",
                            "Identify at least three financial leaks and quantify their annual cost.",
                            "Propose remedies ranked by impact, cost, and ease of implementation.",
                            "Write a one-page executive summary for the fictional client.",
                        ]},
                        {"type": "activity", "title": "Begin the case study", "text": "Read the full case study profile. Highlight every income source, debt, asset, and expense. Compute net worth and monthly cash flow before proposing changes."},
                    ],
                    "check": {
                        "prompt": "Check your approach to the capstone case study.",
                        "questions": [
                            {"q": "The capstone requires you to…", "options": ["identify leaks and propose realistic improvements", "memorize definitions", "write a fictional story"], "answer": "identify leaks and propose realistic improvements", "explain": "The capstone tests whether you can apply structural analysis to a real financial situation."},
                            {"q": "Capstone recommendations should be ordered by…", "options": ["impact, cost, and ease of implementation", "alphabetical order", "what sounds most impressive"], "answer": "impact, cost, and ease of implementation", "explain": "Real financial planning prioritizes the changes that solve the biggest problems at the lowest cost."},
                        ],
                    },
                },
            ],
        },
    ],
}
