
## Railway Deployment Fixes (2026-09-04)
- Removed ANTHROPIC/Claude dependencies
- Default LLM: deepseek-chat
- Frontend syntax errors fixed

## WAI Institute Homeschool Academy (MHC v1 — in progress, this branch)
- Academy gateway + curriculum explorer + course pages + family dashboards + lesson player
- Real curriculum seed: 5 published courses (Grade 1 ELA, Grade 4 Math, Grade 7 Math,
  Grade 9 Biology, Applied Electrical Engineering Year 1) + 19 honest PLANNED catalog entries
- New `/api/academy/*` router: students, grade/track enrollment, lesson unlock chain,
  80% mastery + retry, dashboards, printable records (educational documentation)
- Lesson Coach reuses the existing AI gateway with a no-answer mastery-safe prompt
- Plan/tracker docs: `HOMESCHOOL_ACADEMY_BUILD_PLAN.md`, `HOMESCHOOL_ACADEMY_PROGRESS.md`

## Academy verification pass (2026-09-06, this branch)
- 16 backend academy tests green (added regression for deep-link attempts resolving
  the enrolled student); seed validation 24 courses; frontend build + route/nav
  integrity green
- Fixed: curriculum explorer track filter now matches a course's full `tracks`
  applicability (Grade 7 Math shows under Builder); lesson player resolves the
  student when a deep link omits `?student=` instead of failing attempts
