// Domain-aware front door — one build, two doors.
// See docs/morehelp-migration-blueprint.md (Domain Focus Migration).
//
//   www.wai-institute.org  → focused institution door (education, credentials, AI Tutor)
//   www.morehelp.center    → M.O.R.E. hub door (support, billing, community, creative)
export const MORE_HOME = "https://www.morehelp.center";

export function isWaiDoor() {
  try {
    return window.location.hostname.includes("wai-institute.org");
  } catch {
    return false;
  }
}
