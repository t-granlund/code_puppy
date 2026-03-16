# FallbackModel PR Timeline (Complete)

Source: https://github.com/pydantic/pydantic-ai/pulls?q=is%3Apr+FallbackModel+is%3Aclosed+sort%3Acreated-asc

## Early Drafts (Closed, Not Merged)
- **#532** "Add fallback models support" — The-CodelNN, closed Jan 2, 2025 (Draft)
- **#645** "Draft: FallbackModel support" — sydney-runkle, closed Feb 3, 2025 (Draft)
- **#651** "Add model_name field to ModelResponse" — sydney-runkle, closed Jan 16, 2025 (Draft)
- **#655** "Add FallbackModel with fallback logic and tests" — DaveOkpare, closed Jan 10, 2025 (Draft)

## Merged PRs (Chronological)
- **#701** "Add model_name to ModelResponse" — sydney-runkle, merged Jan 21, 2025 (prerequisite)
- **#894** ⭐ "Add FallbackModel support" — sydney-runkle, merged **Feb 25, 2025** (INTRODUCTION)
- **#1076** "Fix instrumentation of FallbackModel" — alexmojaki, merged Mar 13, 2025
- **#1121** "InstrumentedModel and FallbackModel fixes" — alexmojaki, merged Mar 14, 2025
- **#1147** "Fix span attributes when instrumenting FallbackModel streaming" — alexmojaki, merged Mar 17, 2025
- **#2136** "Let model settings be passed to model classes" — svilupp, merged Jul 10, 2025
- **#2540** "Fix FallbackModel to respect each model's model settings" — jerry-reevo, merged Aug 13, 2025
- **#2564** "Make FallbackModel accept string model names" — vikigenius, merged Aug 15, 2025
- **#2584** "Add price() method to ModelResponse" — Kludex, merged Aug 21, 2025
- **#3139** "Wrap GoogleModel google.genai.errors.APIError in ModelHTTPError so it works with FallbackModel" — timothy-jeong, merged Nov 18, 2025
- **#3294** "Warn about implicit retries on the FallbackModel docs" — dsfaccini, merged Nov 7, 2025
- **#3303** "FallbackModel support for Native and Prompted output modes and ModelProfile.default_structured_output_mode" — DouweM, merged Nov 5, 2025
