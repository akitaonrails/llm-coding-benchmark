# Self-Review — Phase 3

## GOAL VERIFICATION TABLE

No original project brief or goal list (G1–G14) is present in the workspace. README.md contains only the default Rails template text. No file, commit, or ticket references any numbered goals. Therefore all rows are marked UNVERIFIABLE.

| Goal ID | Verdict      | Evidence |
|---------|--------------|----------|
| G1–G14  | UNVERIFIABLE | No brief or goal definitions found in workspace (README.md:1-25, no .md files listing goals) |

## CODE QUALITY ASSESSMENT

**Files examined (520 total LOC across 16 .rb files):**

- `app/services/chat_service.rb:3` — Single class with mixed responsibilities: OpenRouter HTTP calls, tool dispatch, streaming, prompt construction. 76 lines, one private `http` method, constants mixed with logic.
- `app/services/conversation_store.rb:5` — Redis interaction + truncation logic. `redis` class method lazily creates connection per call; no connection pooling visible. `MAX_BYTES` and `MAX_MESSAGES` truncation performed in `append` without atomic Lua script — potential race under concurrent appends.
- `app/controllers/chat_controller.rb:3` — 41-line controller with `stream` action that subscribes to Action Cable, calls `ChatService.stream_chat`, and writes to stream. Mixes transport and domain logic.
- `app/channels/chat_channel.rb:3` — 12-line channel that delegates to controller stream method; minimal.
- `app/tools/*.rb` — Two small tool classes (`ServerTimeTool`, `CalculatorTool`) each with a single class method; good single-responsibility but no shared interface or registry.
- `app/controllers/application_controller.rb` — Empty beyond Rails default.

**Top 3 refactor candidates:**

1. `ChatService` — extract HTTP client, tool registry, and prompt builder into separate collaborators. Current class violates SRP and is hard to unit-test without stubbing `Net::HTTP`.
2. `ConversationStore#append` — replace manual byte/message truncation with atomic Redis operations or Lua to eliminate race between `llen`/`lrange`/`ltrim` under concurrent writers.
3. `ChatController#stream` — move streaming response construction out of controller; controller should only handle HTTP/Cable concerns.

## TEST COVERAGE ASSESSMENT

**Test execution:**

```
$ bundle exec rake test
# => 0 failures, 0 errors, 2 assertions (chat_service_test.rb only)
```

**Coverage tooling:** No SimpleCov or any coverage gem in Gemfile. Running the suite produces no percentage output.

- Total test LOC: 18 lines in `test/services/chat_service_test.rb`
- Weakest area: entire streaming path (`ChatService#stream_chat`), Redis error handling, tool execution failures, Action Cable subscription lifecycle — none have test coverage.
- Uncovered failure modes: Redis connection loss, OpenRouter 429/5xx responses, malformed SSE chunks, tool JSON parse errors, concurrent `append` races, missing `OPENROUTER_API_KEY` at runtime.

## KNOWN DEFECTS AND RISKS

1. `ConversationStore#append` (lines 19-30) performs non-atomic `llen` + `ltrim` sequence; two writers can both see `len <= MAX` and both append, exceeding `MAX_MESSAGES`.
2. `ChatService#http` creates a new `Net::HTTP` object per call with no read/open timeouts set — risk of indefinite hang on slow OpenRouter responses.
3. No authentication/authorization on `ChatChannel` or `ChatController#stream`; any client can open a streaming session and consume API quota.
4. `ChatService.preflight` only checks `ENV["OPENROUTER_API_KEY"]` presence, not validity; downstream 401s will surface only during first `stream_chat` call.
5. `Gemfile.lock` present but no `bundle-audit` or Dependabot configuration beyond `config/bundler-audit.yml`; known-vulnerable gems could be deployed.
6. `MAX_BYTES` truncation (line 24) measures joined prompt size after truncation decision — a single large message can still exceed the byte budget before any trim occurs.