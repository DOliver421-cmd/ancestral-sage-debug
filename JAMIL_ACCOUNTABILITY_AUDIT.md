# Jamil Accountability Audit

Date: 2026-06-12

## Purpose

This audit records the first stabilization pass for AI Jamil / The Director.
The immediate goal is not to add more autonomy. The goal is to make autonomy honest:
Jamil must distinguish verified facts from assumptions, forecasts, plans, and blocked verification.

## What Exists

- Director widget: `frontend/src/components/DirectorWidget.jsx`
- M.O.R.E. Ops department chat: `frontend/src/pages/MoreOps.jsx`
- Director backend endpoint: `backend/server.py` at `/api/ai/director`
- Director pulse endpoint: `backend/server.py` at `/api/ai/director/pulse`
- Staff meeting endpoints: `backend/server.py` at `/api/exec/staff-meeting` and `/api/exec/staff-meetings`
- Director prompt: `backend/prompts/director_prompt.py`
- M.O.R.E. department prompt: `backend/prompts/more_department_system.py`
- Revenue Director tools: `backend/tools/revenue_director_tools.py`

## Main Risk Found

The Director prompt pushed confidence too hard. It told the AI to avoid saying it lacked access,
to treat unknown departments as real, and to act as if it had information. That can create the
exact failure mode Delon described: false reports, false status, false earnings, and overconfident
claims when the platform has not actually produced verified results.

## Changes Made In This Pass

- Added a Truth and Receipts Protocol to `backend/prompts/director_prompt.py`.
- Added an Unknown Information Truth Override to separate useful assumptions from verified facts.
- Updated Revenue Director tool outputs so projections and opportunities are explicitly labeled.
- Renamed opportunity estimates from `revenue_impact` to `potential_revenue_impact`.
- Added `truth_label` fields to revenue audit, forecast, and dashboard outputs.
- Fixed Director greeting lab review count from `submitted` to the actual `pending` lab status.

## Rules Jamil Must Follow

- Actual revenue must come from payments, Stripe/Gumroad records, invoices, or database records.
- Forecasts are not earnings.
- Opportunities are not earnings.
- Product counts are not revenue.
- Planned work is not completion.
- Unknown staff, departments, volunteers, or partners are not confirmed active unless verified.
- Every operational claim should be labeled as: VERIFIED ACTUAL, DATABASE COUNT, PROJECTION, ASSUMPTION, or BLOCKED/UNAVAILABLE.

## Next Recommended Pass

1. Add a visible "Verified / Projection / Assumption" display in the Director UI.
2. Add a dedicated Jamil dashboard panel showing actual revenue, projected revenue, blocked items, and next actions separately.
3. Add tests for revenue reporting so no endpoint can report potential money as earned money.
4. Repair the local development setup: Python, Node/npm, frontend dependencies, and Docker compose mismatch.
5. Run the admin assistant volunteer workflow only after the local app can build and the Director can produce verified status reports.
