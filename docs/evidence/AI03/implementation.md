# AI03 — OpenRouter request compatibility

Existing assigned cat01/Sol-low, no delegation/model substitution. Read TASK/AGENTS, architecture29 and current adapter/tests. Scope only server request compatibility; no interface/design change. Root supplies official OpenRouter model contract for baidu/ernie-5.5-flash-preview:free and handles documentation/live configuration.

One runtime condition now selects max_tokens:600 for parsed hostname exactly openrouter.ai or existing api.orcarouter.ai. All other hosts retain max_completion_tokens:600. No model defaults/fallback/endpoint rewriting/settings/dependencies added. Bounded request/reply/history, timeout10s/read1MiB, streamfalse, NoRedirect, credentials server-only and safe failures unchanged. OrcaRouter local configuration untouched.

Existing stub parametrization now accepts explicitmodel and includes https://openrouter.ai/api/v1/chat/completions with model baidu/ernie-5.5-flash-preview:free. Previous3OrcaRouter/host-lookalike contracts remain, generic independenttest unchanged. Contract verifies exactpayload/sole600tokenlimit, actualconfiguredmodel/messages/endpoint, POST/auth using fakeunitkey, onecall, timeout10 and NoRedirect. No liveOpenRouterkey required; no actual outbound request.

Ruffcheck passed; Ruffformat applied only to changedtest formatting then2filesalreadyformatted; gitdiffcheckexit0. Sourcefreeze for root independenttests/acceptance. Executor did not read .env, call network/API, change liveconfiguration, runDB/tests or commit/push/deploy. LiveOpenRouter behavior not claimed tested; no availablekey used or inferred.
