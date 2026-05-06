# GO!CS Project Kickoff (MVP Prototype)

## MVP Goal
Deliver a lightweight, demo-ready website prototype that proves the full flow:

`Upload -> Generate -> Test -> Share`

## Scope In (This Project Phase)
1. Five-page prototype routes:
- `/`
- `/generating/:sessionId`
- `/bot/:publicToken/test`
- `/bot/:publicToken/share`
- `/chat/:publicToken`
2. Mock-first behavior with no real backend:
- bot generation session
- generation progress + retry
- QA-style ask flow with confidence labels
- fallback for unsupported/risk questions
- share link/widget copy interactions
- Telegram placeholder validation
3. Mobile-usable layout and clear non-technical copy.
4. Team execution docs and review gates (PO/UX/Tech/QA).

## Scope Out (This Phase)
1. Real database and production APIs.
2. Auth/workspace/billing/analytics/CRM features.
3. Official WhatsApp/Facebook channel integrations.
4. Production observability/security hardening.

## Acceptance Criteria (Current Prototype)
1. User can complete Upload -> Generate -> Test -> Share without dead ends.
2. Unsupported questions return fallback (no guessing).
3. Risk questions are handled conservatively unless clearly supported.
4. Public chat route is reachable and usable.
5. Copy actions (link/widget) provide clear feedback.
6. Telegram section clearly indicates placeholder status.
7. Mobile viewport remains usable for all core actions.

## Stakeholder Review Checklist
1. Value proposition is clear in first 30 seconds.
2. Core flow is fully demonstrated in under 5 minutes.
3. Safety behavior is shown with one unsupported/risk question example.
4. Scope boundaries are clearly stated (what is demo-only).
5. Final feedback captured as:
- Keep
- Change
- Add Next
