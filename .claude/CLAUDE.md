# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Vue Layout And Link Field Rules

- For full-page Vue screens, size the root container to the usable viewport with `100dvh` minus layout offsets.
- Use flex column layout with `min-height: 0` on the parent panel, body wrapper, and scroll wrapper so only the intended inner section scrolls.
- For data tables that should fill remaining space, put the table inside a flex child that grows with `flex: 1` and use `fixed-header` with `height="100%"`.
- Avoid hard-coded table heights when the page structure can determine the available height through flex layout.

## 6. Frappe Link Fields In Vue

- Do not create custom backend APIs just to fetch Link field options when Frappe already provides `frappe.desk.search.search_link`.
- For Vuetify autocomplete link fields, call `frappe.desk.search.search_link` and map results to `{ value, label, description }`.
- Keep the selected value as the real linked document name, not the display label.
- On lookup failures, show a `frappe.msgprint` with a clear title, red indicator, and the actual error message.

## 7. General Simplicity Rule

- Prefer Frappe-native behavior over custom wrappers when the native API already covers the use case.
- Avoid serializer/helper layers unless they add real business logic or prevent duplication across multiple consumers.

## 8. Frappe And Vuetify Dialogs

- Native Frappe/Bootstrap dialogs must always appear above Vuetify `v-dialog`s. Keep shared Vuetify `VDialog` defaults with `retainFocus: false` and a lower z-index than Frappe modals, and do not re-enable focus trapping on dialogs that may open `frappe.confirm`, `frappe.msgprint`, or other native Frappe dialogs.

## 9. Inline Table Row Add Behavior

- For scrollable table-style editors, add new rows inline from the table footer or last row area, and after inserting a row always scroll the table container to its bottom on the next DOM tick so the new row is immediately visible.

## 10. Frappe + Vuetify RTL Rules

- Treat `frappe.utils.is_rtl()` and `frappe.boot.lang` as the single source of truth for direction and language. Do not invent a second RTL toggle inside the Vue app unless explicitly required.
- In Vuetify 3, do not rely on text translation alone and do not assume a plain `dir="rtl"` is enough. Configure RTL through Vuetify `locale.rtl` so component layout flips correctly.
- When bootstrapping Vuetify, set `locale.locale`, `locale.fallback`, `locale.messages`, and `locale.rtl`, for example Arabic => `true`, English => `false`.
- Wrap the app content in `v-locale-provider` with `:rtl="frappe.utils.is_rtl()"` when you need the full component tree to inherit RTL behavior consistently.
- For navigation drawers, tabs, data tables, pagination, and windowed/tabbed views, prefer Vuetify’s built-in RTL behavior over custom CSS hacks. If drawer position must be explicit, bind its location to RTL (`right` in RTL, `left` in LTR).
- Never hard-code physical CSS directions like `left`, `right`, `margin-left`, `padding-right`, `text-align: right`, or LTR-only selectors. Use logical CSS instead:
  - `margin-inline-start/end`
  - `padding-inline-start/end`
  - `border-inline-start/end`
  - `inset-inline-start/end`
  - `text-align: start/end`
- Do not hard-code LTR-only class selectors such as `.v-locale--is-ltr` for sizing or layout. Use stable component classes that work in both directions.
- Directional icons must respect RTL. Back/forward arrows should flip based on `frappe.utils.is_rtl()`.
- Printed documents and report templates must also follow the active locale:
  - use the current language instead of hard-coded `_lang=en`
  - set HTML `lang` and `dir` from the active locale
  - prefer `text-align: start` and logical spacing in print CSS
- When fixing RTL bugs, first verify the Vuetify bootstrap and locale configuration before patching individual components. If the sidebar, tabs, and tables are all still LTR, the root RTL setup is probably wrong.

---
**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
