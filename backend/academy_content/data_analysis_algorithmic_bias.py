"""Grade 11 Mathematics: Data Analysis, Algorithmic Bias, and Economic Modeling (published).

Grade 11 algebra, statistics, and modeling applied to real data: redlining
research, lending and policing datasets, and wealth-gap modeling. Students
learn the mathematics (correlation, regression, sampling, bias) and then
apply it to the datasets where inequality is produced and measured.
"""

DATA_ANALYSIS_ALGORITHMIC_BIAS = {
    "slug": "data-analysis-algorithmic-bias",
    "title": "Data Analysis, Algorithmic Bias, and Economic Modeling",
    "summary": "Algebra, statistics, and modeling applied to redlining, lending, and wealth-gap data — including how algorithms encode bias.",
    "description": (
        "Grade 11 mathematics here teaches the full core — linear and exponential "
        "functions, probability, sampling, correlation and regression — using datasets "
        "that describe how wealth and risk are distributed in real economies. Students "
        "work with redlining maps and HOLC data, lending data, and labor statistics. "
        "They also examine how algorithms trained on such data encode and amplify "
        "inequality, and how to detect it: discovering bias is a math skill, not an "
        "ideological one."
    ),
    "subject": "math",
    "subject_label": "Mathematics",
    "track": "scholar",
    "tracks": ["scholar", "foundations"],
    "grades": ["11"],
    "grade_label": "Grade 11",
    "status": "published",
    "audience": "Grade 11 students studying algebra, statistics, and data modeling.",
    "est_hours": 30,
    "passing_score": 80,
    "learning_objectives": [
        "Represent data with tables, graphs, and measures of center and spread.",
        "Compute and interpret correlation, and distinguish it from causation.",
        "Fit a linear model by least squares and use it for prediction.",
        "Model wealth growth with linear and exponential functions.",
        "Describe sampling methods and how sampling bias arises.",
        "Analyze a historical dataset (redlining, lending, or labor) for disparities.",
        "Explain how a machine-learning model can inherit bias from its training data.",
    ],
    "units": [
        {
            "slug": "describing-data",
            "title": "Describing Data",
            "summary": "Center, spread, and shape — the language of statistics.",
            "order": 1,
            "lessons": [
                {
                    "slug": "center-and-spread",
                    "title": "Center and Spread",
                    "order": 1,
                    "minutes": 26,
                    "summary": "Mean, median, standard deviation, and what they do and do not tell you.",
                    "learn": [
                        {"type": "p", "text": "A dataset needs two numbers to begin: a center and a spread. The mean is sensitive to outliers; the median is not. If ten families hold $50,000 each and one holds $10 million, the mean looks prosperous and the median tells the truth about the other ten. On wealth data, where outliers are enormous, the median is usually the honest summary."},
                        {"type": "list", "items": [
                            "Mean: sensitive to extreme values.",
                            "Median: the middle value, robust to outliers.",
                            "Interquartile range / standard deviation: measures of spread.",
                            "Skewed data: mean pulled away from median by the tail.",
                        ]},
                        {"type": "example", "title": "Worked example", "text": "Salaries 40, 42, 44, 46, and 480 (thousand dollars). Mean = 138.4; median = 44. The mean describes no one; the median describes four of the five."},
                        {"type": "activity", "title": "Compute", "text": "Find the mean and median of your class's heights, then add a hypothetical 240 cm student and recompute. Which measure moved, and by how much?"},
                    ],
                    "check": {
                        "prompt": "Check what you know about summary statistics.",
                        "questions": [
                            {"q": "When a dataset has extreme outliers, the most honest measure of center is usually…", "options": ["the median", "the mean", "the mode only"], "answer": "the median", "explain": "The median is unaffected by a few extreme values."},
                            {"q": "In the salary example (40, 42, 44, 46, 480), the mean is…", "options": ["much higher than the median", "equal to the median", "lower than the median"], "answer": "much higher than the median", "explain": "One extreme value drags the mean up away from the typical case."},
                        ],
                    },
                },
                {
                    "slug": "sampling-bias",
                    "title": "Sampling and Bias",
                    "order": 2,
                    "minutes": 26,
                    "summary": "How the wrong sample produces a wrong answer that looks rigorous.",
                    "learn": [
                        {"type": "p", "text": "A statistic about a population is only as good as the sample behind it. Selection bias arises when some population groups are more likely to be sampled than others — a phone poll excludes households without phones. Coverage bias arises when the sampling frame misses part of the population entirely. Historic datasets on health, housing, and lending are frequently biased samples, and analyses built on them reproduce the bias."},
                        {"type": "list", "items": [
                            "Random sampling: every unit has equal chance of selection.",
                            "Selection bias: units are included at different rates.",
                            "Coverage bias: part of the population has no chance of inclusion.",
                            "Non-response bias: those who answer differ from those who don't.",
                        ]},
                        {"type": "example", "title": "Historical case", "text": "Public health surveys that sampled only insured patients systematically missed uninsured populations — a major cause of understated urban Black mortality in early twentieth century records."},
                        {"type": "activity", "title": "Spot the bias", "text": "Describe a sample for 'how do students feel about the school year?' using school wi-fi login logs. Identify the coverage bias and who is missing."},
                    ],
                    "check": {
                        "prompt": "Check what you know about sampling.",
                        "questions": [
                            {"q": "Coverage bias means…", "options": ["part of the population has no chance of being sampled", "everyone is equally sampled", "the sample is random"], "answer": "part of the population has no chance of being sampled", "explain": "The sampling frame itself excludes people."},
                            {"q": "A random sample aims for…", "options": ["equal chance of selection for every unit", "equal results for every group", "identical responses"], "answer": "equal chance of selection for every unit", "explain": "Equal probability is the defining property of random sampling."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "modeling",
            "title": "Modeling Growth and Prediction",
            "summary": "Linear, exponential, and least squares.",
            "order": 2,
            "lessons": [
                {
                    "slug": "linear-and-exponential-models",
                    "title": "Linear and Exponential Models",
                    "order": 3,
                    "minutes": 26,
                    "summary": "Two patterns of growth that describe wealth differently.",
                    "learn": [
                        {"type": "p", "text": "A linear model adds a constant each period; an exponential model multiplies by a constant. Wages accumulated by labor are approximately linear; assets accumulated by capital grow exponentially. This single distinction explains why the wealth gap grows faster than the income gap: interest, dividends, and property appreciation compound."},
                        {"type": "list", "items": [
                            "Linear: W(t) = 40,000 + 0t — no accumulation.",
                            "Exponential: A(t) = P(1+r)^t — compound interest.",
                            "Over 30 years, a 6% annual return more than multiplies assets by five.",
                        ]},
                        {"type": "example", "title": "Two paths", "text": "$1,000 invested per year for 40 years at 5% accumulates far more than $1,000 saved per year, because each year's investment compounds. This is why inherited assets compound across generations."},
                        {"type": "activity", "title": "Graph it", "text": "Graph y = 1,000t and y = 1,000(1.05)^t for t = 0 to 30 on the same axes. Label the crossover point."},
                    ],
                    "check": {
                        "prompt": "Check what you know about growth models.",
                        "questions": [
                            {"q": "Compound growth follows a…", "options": ["exponential model", "linear model", "constant model"], "answer": "exponential model", "explain": "Each period multiplies the previous total."},
                            {"q": "A linear model adds…", "options": ["the same amount each period", "twice as much each period", "nothing"], "answer": "the same amount each period", "explain": "Linear growth has a constant rate of change."},
                        ],
                    },
                },
                {
                    "slug": "correlation-and-regression",
                    "title": "Correlation and Regression",
                    "order": 4,
                    "minutes": 26,
                    "summary": "Fit a line; be careful what it claims.",
                    "learn": [
                        {"type": "p", "text": "Correlation (r) measures linear association from -1 to 1; -1 and 1 are perfect, 0 is no linear relationship. The line of best fit minimizes squared errors and supports prediction, but prediction is not causation. Confounding variables generate correlations with no causal meaning — the classic example: ice-cream sales correlate with drownings, because summer causes both."},
                        {"type": "list", "items": [
                            "r near ±1: strong linear association; near 0: little.",
                            "Least squares line: y = a + bx, minimizing Σ(residuals²).",
                            "Predict with the model; never claim cause without a design.",
                            "Confounder: a third variable causing both.",
                        ]},
                        {"type": "example", "title": "Applied", "text": "Median household wealth by race, by census tract, regressed on historic HOLC grade: prediction is possible, but HOLC grade correlates with present segregation, which is the actual mechanism."},
                        {"type": "activity", "title": "Fit it", "text": "Collect 10 paired data points (for example, hours studied and test score). Compute r, draw the least squares line by hand, and predict at one new value."},
                    ],
                    "check": {
                        "prompt": "Check what you know about correlation.",
                        "questions": [
                            {"q": "A correlation of r = 0.96 means…", "options": ["a strong positive linear association", "a causation proof", "no relationship at all"], "answer": "a strong positive linear association", "explain": "Strong association does not establish cause."},
                            {"q": "The line of best fit minimizes…", "options": ["the sum of squared residuals", "the largest x value", "the number of points"], "answer": "the sum of squared residuals", "explain": "Least squares minimizes total squared vertical distance."},
                        ],
                    },
                },
            ],
        },
        {
            "slug": "data-and-power",
            "title": "Data and Power",
            "summary": "Analyzing disparity, and the bias inside algorithms.",
            "order": 3,
            "lessons": [
                {
                    "slug": "redlining-data",
                    "title": "Case Study: Redlining, Measured",
                    "order": 5,
                    "minutes": 26,
                    "summary": "A historical dataset analyzed rigorously.",
                    "learn": [
                        {"type": "p", "text": "The Home Owners' Loan Corporation (HOLC) graded city neighborhoods A through D in the late 1930s and denied credit to low-grade zones; modern scholars analyze those same blocks. Neighborhoods with the lowest grades were disproportionately Black and immigrant, and effects persist in present home ownership, lending, and green space. Because the data are objective and well documented, the analysis can be done with ordinary statistical tools — which is the point."},
                        {"type": "list", "items": [
                            "HOLC grade blocks: highest grades received investment; lowest were denied credit.",
                            "Present-day correlations: lower home values, less tree cover, less lending.",
                            "Method: compare matched neighborhoods differing mainly on HOLC grade.",
                        ]},
                        {"type": "example", "title": "Math skill", "text": "Compute mean home value by block grade, run a two-sample comparison, and check effect size. You have just done a real research analysis with school mathematics."},
                        {"type": "activity", "title": "Analyze", "text": "Use published HOLC data for one city. Build a table of mean home values by grade and compute the difference in standard deviations."},
                    ],
                    "check": {
                        "prompt": "Check what you know about the redlining case study.",
                        "questions": [
                            {"q": "HOLC 'redlining' used grades to…", "options": ["deny credit to whole neighborhoods", "build bridges", "plant trees"], "answer": "deny credit to whole neighborhoods", "explain": "Low-graded areas were cut off from mortgage investment."},
                            {"q": "A sound redlining analysis should…", "options": ["compare neighborhoods matched on confounders", "use only a single web page", "avoid checking effect size"], "answer": "compare neighborhoods matched on confounders", "explain": "Matching isolates the variable being studied."},
                        ],
                    },
                },
                {
                    "slug": "algorithmic-bias",
                    "title": "How Algorithms Inherit Bias",
                    "order": 6,
                    "minutes": 26,
                    "summary": "Training data, labels, and outcomes measured mathematically.",
                    "learn": [
                        {"type": "p", "text": "A model trained on historical data learns the historical patterns — including discrimination. If a lending dataset shows approval rates that differ by neighborhood, a model trained on it can reproduce the pattern even when race is not an input, because ZIP code and loan amount carry the same information. Detecting this requires statistics: model error rates across groups."},
                        {"type": "list", "items": [
                            "Proxy variables: a model can 'discover' a forbidden attribute from allowed ones.",
                            "Label bias: labels reflect past decisions, not truth.",
                            "Different error rates across groups is a measurable fairness failure.",
                        ]},
                        {"type": "example", "title": "Test it", "text": "Train a classifier, then compute true positive and false positive rates by group. Disparate impact is a number, not an opinion."},
                        {"type": "activity", "title": "Audit a model", "text": "Build or use a simple classifier. Compute error rates for two groups defined in your data. Report whether they are equal and what could cause a gap."},
                    ],
                    "check": {
                        "prompt": "Check what you know about algorithmic bias.",
                        "questions": [
                            {"q": "A proxy variable is…", "options": ["an allowed attribute correlated with a protected one", "a type of hardware", "a random seed"], "answer": "an allowed attribute correlated with a protected one", "explain": "Proxies let forbidden information leak into a model indirectly."},
                            {"q": "To detect disparate impact you compute…", "options": ["error rates by group", "the model's file size", "the training time"], "answer": "error rates by group", "explain": "Different error rates across groups is a measurable fairness failure."},
                        ],
                    },
                },
            ],
        },
    ],
}
