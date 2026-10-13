// Static, repo-owned REA analysis probe: no network, secrets, or side effects.
export function routeSupportQuestion(query) {
  const normalized = String(query || "").toLowerCase();
  if (normalized.includes("status")) return {intent:"status", effect:"read_only"};
  if (normalized.includes("cancel")) return {intent:"cancel", effect:"owner_confirmed"};
  return {intent:"conversation", effect:"none"};
}
export const testCapabilities = ["conversation", "status", "cancel"];
