# AI02 — OrcaRouter token contract

Assigned existing cat01/Sol-low, no delegation/model substitution. Read TASK/AGENTS, architecture29 and PLANAI01. No UI change, design/Taste work not needed. Root supplied verified official OrcaRouter contract: https://www.orcarouter.ai/models/deepseek-v4-flash-free, endpoint https://api.orcarouter.ai/v1/chat/completions, model deepseek/deepseek-v4-flash-free, max_tokens supported.

Only assistant.py and test_assistant.py changed. After existing configured() validation, parsed hostname exactly api.orcarouter.ai selects max_tokens:600; every other parsed host keeps max_completion_tokens:600. Existing endpoint/model/configuration, streamfalse, timeout10s,1MiBread, reply/input/history bounds, NoRedirect, authorization and safe error handling unchanged. No retry/model/provider or paidfallback added.

New parameterized stub contract checks official OrcaRouter endpoint and two nonmatching cases (suffix lookalike and provider path containing host text). It verifies exact payload/model/messages/sole600tokenparameter, exact endpoint, POST/auth, timeout10, one transport call and NoRedirect. Existing generic contract remains intact. Only fake unit key and in-memory response; no actual API request or real credentials.

Executor commands: Ruffcheck passed, Ruffformatcheck2files alreadyformatted, gitdiffcheckexit0. Source frozen before root isolatedtest/review; executor did not run DB/tests/API/commit/push/deploy, access .env or touch unrelatedfiles. Actual external service behavior not claimed tested; root owns officialsource verification and independent tests/acceptance.
