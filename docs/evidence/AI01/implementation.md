# AI01 — private student chat, API ready for later connection

Executor read project instructions/TASK/architecture29/PLAN and Taste Skill2.5.1 with core references. Existing workspace palette/layout (architecture20) retained. Parent owns generated pixel robot avatar and official API contract verification; no additional agent or image generation by executor.

## Implemented

- `/assistant/` GET/POST and `/assistant/clear/` POST in existing accounts app. Active student with own_profile only; login/CSRF/no-store/method constraints. No models/migrations/dependencies. Eighth student navigation item; design checks updated to8icons and new route.
- Native POST form with2000character limit. Success redirects and shows actual provider text. Default all3AI settings blank: no outbound request, explicit «ИИ пока не подключён», inline unavailable error retains draft, no invented assistant reply. Empty state, starter buttons populate input, keyboard label/focus, native clear. No-JS main form/clear still work; starter buttons stay hidden without JS.
- Neutral pending status «Отправляем вопрос…», button disabled during request; textarea readonly (still submitted), starter/clear controls temporarily disabled to avoid overwriting pending input. Pageshow resets controls. Error UI keeps typed question and prior successful history.
- History stored in own server session, owner-bound, max12messages. Only typed messages and same-chat history go to provider; profile/grades/schedule/document data never added. Clear removes own session chat. Successful user+assistant pair appended together only after valid reply.
- Server-only AI_API_KEY/AI_API_URL/AI_MODEL in settings/env example. URL requires HTTPS or loopback HTTP; no userinfo/fragment, port checked. OpenAI-compatible POST uses model/messages/max_completion_tokens600/streamfalse; Bearer key only in header. No redirects, timeout10seconds, response read at most1MiB+1, reply max8000characters. Malformed/oversized/empty output and reply echoing configured key rejected; safe generic failures hide transport/provider details. Header/body/key never stored in browser/session or logged by this module.
- README documents configuration/restart, contract, session/data handling and limits. API/model must support this contract. Actual network/provider authentication is untested until user supplies configuration; all executor tests are stubbed, with no paid calls.

## Verification

- Targeted suite24passed,1existing pytest fixture warning,18.58seconds using isolated PostgreSQL55439/test_ai01_executor.
-22server cases: disconnected has no outbound call/fake response; injected success/context/history cap/clear; provider errors and draft preservation; input bound/escaping; foreign owner history, separate client isolation, role/CSRF/method restrictions; HTTPS/loopback configuration; exact adapter request contract, redirects disabled, bounded/invalid/secret-bearing response rejection and network failure.
-2real Chromium cases360/1440: own navigation, avatar loaded, disconnected empty state, starter focus/input, send error retained text without reply bubble, clear and second-account empty chat. Captured assistant-360.png/assistant-1440.png; viewed360: readable8item4×2nav, no horizontal overflow, visible disconnected/error state and retained draft.
- After24pass run, added HTTPException catch (safe truncated HTTP failures), explicit role-string guard, neutral pending wording, and readonly/temporary ancillary control disable during pending. Parent independent run validates final freeze. Ruff relevant Python files and git diff --check passed after final edits.
- No raw Django source visual checker run, no Taste gate PASS claimed. No service key provided/used, no user .env/.gitignore edit, no commit/push/deployment by executor. Parent owns architecture/prompt/art/review and final verification.
