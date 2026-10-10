# Handoff: the two in-product Resource Hub guides

These are the **exact** step contents for "Grant Writing Basics Guide" and "Community Fundraising
Playbook". They were written by the session that ended 2026-10-10 and were verified to apply cleanly
to `main` at `4a318815` and to compile.

**Why this file exists:** the owner rejected relabelling these as "read-only guides" — they are seeded
catalogue rows with `url: ""` and no content, always intended to BE the guide. This content is what
makes them real. Restore it verbatim; do not shorten it, and do not replace it with a different set.

## How to restore

In `backend/routers/resource_hub.py`, the two seed entries in `seed_hub_resources()` currently read:

```python
    {
        "title": "Grant Writing Basics Guide",
        "description": "Step-by-step guide to writing effective grant proposals: problem statement, goals, budget, evaluation metrics.",
        "category": "templates",
        "url": "",
        "tags": ["grant-writing", "template", "guide"],
    },
    {
        "title": "Community Fundraising Playbook",
        "description": "Strategies for community-based fundraising: events, crowdfunding, social media campaigns, donor cultivation.",
        "category": "templates",
        "url": "",
        "tags": ["fundraising", "playbook", "community"],
    },
```

Replace both blocks with the two below. Nothing else in the file changes — the `list_resources`
endpoint already returns whole rows, so `steps` and `in_product` travel to the client with no schema
change and no new endpoint.

## Entry 1 — Grant Writing Basics Guide

```python
    {
        "title": "Grant Writing Basics Guide",
        "description": "Work through a live proposal: problem statement, goals, budget, and evaluation metrics.",
        "category": "templates",
        "url": "",
        "tags": ["grant-writing", "template", "guide", "workflow"],
        "in_product": True,
        "steps": [
            {"title": "Name the problem in one paragraph", "description": "Who is affected, how you know, and what changes if it is solved. Funders read this first and stop reading if it is vague. One paragraph, no jargon."},
            {"title": "Write measurable goals", "description": "Three to five goals, each with a number and a deadline: 'serve 60 students in 12 months', not 'help the community'."},
            {"title": "List the activities that produce those goals", "description": "One line per activity, showing how it moves a specific goal. If an activity moves nothing, cut it."},
            {"title": "Build the budget and check the arithmetic", "description": "Every activity gets a line; salaries sum to the total; the total matches the request plus other sources. Funders check this line first."},
            {"title": "Define how you will measure success", "description": "For each goal, the number you will report and how you will collect it. A goal without a measure is a wish."},
            {"title": "Add organisational credibility", "description": "Who you are, who you have served, audited figures or references. Two paragraphs is enough for a first application."},
            {"title": "Write the one-page summary last", "description": "Problem, what you will do, what it costs, what will change. Many funders read only this page."},
            {"title": "Submit and record the outcome", "description": "Log the funder, amount, deadline, and decision. A submitted proposal is an asset; an unlogged one is lost work."},
        ],
    },
```

## Entry 2 — Community Fundraising Playbook

```python
    {
        "title": "Community Fundraising Playbook",
        "description": "Run a community campaign as a workflow: events, crowdfunding, social campaigns, and donor cultivation.",
        "category": "templates",
        "url": "",
        "tags": ["fundraising", "playbook", "community", "workflow"],
        "in_product": True,
        "steps": [
            {"title": "Set the goal and the deadline", "description": "One number and one date. 'Raise $5,000 by March 1 for X.' A campaign without both is a wish."},
            {"title": "Write the case in two paragraphs", "description": "What the money does, who it reaches, and what happens at each amount. Ask for a specific amount, not 'support'."},
            {"title": "List your inner circle", "description": "Twenty people who will give first and tell others. Name them. Fundraising starts warm."},
            {"title": "Pick the channels you will actually run", "description": "Two, not six: one event, one online page. Depth beats breadth in a community campaign."},
            {"title": "Run the event", "description": "A date, a place, a host, and one ask. Capture names and contact details with permission."},
            {"title": "Launch the online page", "description": "One page, the case, the goal, and the deadline. Share it with the inner circle first."},
            {"title": "Thank every donor within 48 hours", "description": "A specific thank-you naming what their gift does. The second gift depends on the first thank-you."},
            {"title": "Report the result publicly", "description": "Tell the community what was raised and what it did. It is the strongest ask for next year."},
        ],
    },
```

## The frontend half (not yet written — do this next)

`frontend/src/components/ResourceHubPanel.jsx`, in the `ResourcesTab` resource card:

1. **Delete** the badge added in PR #479:
   `Read-only guide · no workflow` (it is now false and was the thing the owner rejected).
2. Render instead, when `r.in_product`:
   `<span className="… bg-copper/10 text-copper border border-copper/30">Workflow · {r.steps?.length || 0} steps</span>`
3. The external `<a>` must render **only when `r.url` is truthy**. These two have `url: ""`.
4. Otherwise render a button `Open the workflow` that opens a checklist panel using the existing
   `WorkflowStep` model (`{title, description, completed}`) and persists through
   `POST /api/hub/workflows` / `PATCH /api/hub/workflows/{id}` — **no new endpoint, no schema change.**

## Verification required

- Render the real `ResourceHubPanel` with a paying member (needs `user` prop + `canAccess` stub at
  `plus`): assert the badge text, assert no "Read-only guide" string remains, assert the workflow
  button exists, assert no `<a>` with an empty href.
- Live server + DB: check a step, re-fetch `/api/hub/workflows`, assert it persisted; assert another
  family's list is empty.
- Run the guard rails and `craco build`.
