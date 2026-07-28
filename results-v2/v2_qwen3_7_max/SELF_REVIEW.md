# Self-review

Review date: 2026-07-28. This review uses the current working tree and fresh command results, not earlier phase notes. The repository has no commits and every project file is currently untracked (`git status --short`; `git ls-files` returned no paths).

## 1. Goal verification table

| Goal | Verdict | Concrete evidence |
|---|---|---|
| G1 | PASS | `.ruby-version:1` selects Ruby 4.0.6, `mise ls ruby` marks 4.0.6 active, and `bundle exec rails -v` returned Rails 8.1.3; `bundle outdated rails ruby_llm --strict` returned `Bundle up to date!`. Active Job, Active Record, and Action Mailer Railties are disabled at `config/application.rb:6-10`, and the generated Rails structure is at the workspace root. |
| G2 | FAIL | `curl http://127.0.0.1:3100/` returned HTTP 200 but the body was `Rails::WelcomeController#index` with `<title>Ruby on Rails 8.1.3</title>`, not a chat SPA. Turbo/Stimulus are merely imported at `app/javascript/application.js:2-3`; `app/views/` contains no chat view, partial, or Turbo Stream template. |
| G3 | FAIL | RubyLLM 1.16.0 is installed (`Gemfile.lock:292`) and current according to `bundle outdated`, but `config/initializers/` has no RubyLLM/OpenRouter configuration and there is no chat model selection code. |
| G4 | FAIL | `./bin/rails routes` listed only the health route and Turbo Native navigation routes; there is no chat endpoint or code that calls `Turbo::StreamsChannel`/broadcasts provider chunks. |
| G5 | FAIL | `bundle exec rails test` reported `0 runs, 0 assertions`; there is no `test/` directory, message-history builder, or exact outgoing-message-array test. |
| G6 | FAIL | No model, service, or persistence file exists. Development uses process-local stores (`config/environments/development.rb:29`, `config/cable.yml:1-2`), and there is no TTL, message cap, byte cap, restart recovery, or multi-worker persistence implementation. |
| G7 | FAIL | No `app/tools/` or tool classes exist, and there is no RubyLLM `with_tools` registration for either `server_time` or `calculator`. |
| G8 | FAIL | There is no conversation model/view and no RubyLLM schema/structured-output call; the only application layout still displays the generic title `Project` (`app/views/layouts/application.html.erb:4`). |
| G9 | FAIL | No conversation token accounting, budget environment variable, budget check, or in-UI refusal path exists anywhere in application code. |
| G10 | FAIL | There is no RubyLLM instructions call, API-key preflight, provider error handling, degraded chat state, or failed-turn rollback because no chat request path is implemented. |
| G11 | FAIL | `bundle exec rails test` returned `0 runs, 0 assertions`; no `test/`, `test_helper.rb`, or `.simplecov` exists. SimpleCov is only declared in `Gemfile:54`, so neither component/error tests nor a coverage report exist. |
| G12 | PASS | Fresh commands passed: `bundle exec rubocop` inspected 19 files with no offenses; `bundle exec brakeman --no-pager` found 0 warnings; `bundle exec bundle-audit check --update` found no vulnerabilities. These results cover only the current scaffold. |
| G13 | PARTIAL | `docker build -t project-self-review .` completed successfully; the Dockerfile sets production mode (`Dockerfile:23-28`), runs as UID 1000 (`Dockerfile:63-70`), and uses an entrypoint (`Dockerfile:73`). However, no Compose file exists and `README.md:1-24` is untouched Rails placeholder text. |
| G14 | PASS | Searches found no authentication implementation. `git ls-files` returned no tracked files, while `config/master.key` is excluded by `.gitignore:26-27` and `.dockerignore:13-15`; no `.env` file was found. All discovered project files are under this workspace. |

## 2. Code quality assessment

There is almost no custom application code, so a favorable complexity assessment would be misleading: the main problem is missing implementation, not tangled implementation.

- **Naming:** The generated `Project` module and page title are generic (`config/application.rb:21`, `app/views/layouts/application.html.erb:4-7`). There are no domain names for conversations, messages, streaming, tools, or budgets.
- **Single responsibility:** The existing Ruby class and Stimulus controller are small, but there are no domain/service/persistence layers to evaluate. Absence of responsibilities is not evidence of good separation.
- **Duplication:** No meaningful custom logic exists to duplicate. Most content is Rails generator boilerplate.
- **Dead code:** `app/javascript/controllers/hello_controller.js:3-6` is an unused generated “Hello World” controller. `app/views/pwa/manifest.json.erb` and `app/views/pwa/service-worker.js` exist while their routes are commented out at `config/routes.rb:8-10`.
- **Method/class size:** Existing methods are tiny (`ApplicationController` is seven lines), but this reflects the empty scaffold rather than deliberate decomposition.
- **Coupling between layers:** There are no application layers and therefore no current coupling to assess. The required provider, persistence, controller, and presentation interactions are absent.

### Top three refactors with more time

1. **Remove unused generator artifacts** (`hello_controller.js`, disabled PWA files, and stale generator comments) so a successful root response cannot be mistaken for working application behavior.
2. **Replace generic naming and metadata** (`Project`, generic title/manifest) with domain-specific names once the application contract exists; generic identifiers make logs and UI evidence ambiguous.
3. **Tighten production packaging:** `Dockerfile:27` excludes only the development group, and the build log shows test/quality gems such as SimpleCov, RuboCop, Brakeman, and debug installed in the production image. Exclude the test group and align the entrypoint comments with its actual behavior (`bin/docker-entrypoint:1-3` only executes its arguments).

I would not prioritize broader refactoring before implementing and testing the missing application behavior.

## 3. Test coverage assessment

- **SimpleCov line coverage:** unavailable; no report was generated.
- **SimpleCov branch coverage:** unavailable; branch coverage is not configured and no report was generated.
- **Observed test execution:** `bundle exec rails test` completed with `0 runs, 0 assertions, 0 failures, 0 errors, 0 skips`. No `coverage/` output, `test/` directory, `test_helper.rb`, or `.simplecov` exists. Reporting these as `0.00%` would invent a SimpleCov result; the effective behavioral test coverage is nevertheless zero.
- **Weakest-tested area:** the entire required chat path—request handling, RubyLLM integration, streaming, storage, tools, title generation, budgeting, and UI updates—is both absent and untested.

No test covers these failure modes:

- duplicate or reordered multi-turn provider messages;
- empty, delayed, duplicated, or out-of-order streaming chunks;
- provider timeout, rate limit, malformed response, tool failure, or mid-stream disconnect;
- missing API key or invalid/unknown model;
- failed-turn rollback and partial-response cleanup;
- concurrent writers, two-worker consistency, restart recovery, TTL expiry, or message/byte-cap enforcement;
- calculator validation/injection and server-time tool provenance;
- structured-title schema errors or title-generation failure;
- token-budget boundary conditions and refusal without a provider call;
- Turbo Stream DOM targeting, reconnect behavior, and visible degraded states;
- container/Compose startup and Redis unavailability.

## 4. Known defects and risks

1. **The product is not implemented.** The only root response is the Rails development welcome page. Its HTTP 200 can create a false-positive liveness result.
2. **There is no chat route or request path.** Goals G2 through G11 cannot work at runtime in the current tree.
3. **No durable conversation store exists.** Restart survival, bounds, TTL, and multi-worker correctness are absent rather than merely unproven.
4. **No real streaming exists.** There is no provider call or Turbo broadcast path, so token delivery cannot be incremental.
5. **Tool and calculator safety guarantees do not exist.** Neither required tool is implemented.
6. **Provider failures have no UI handling.** There is no preflight or rescue path, and no rule preventing failed turns from entering future history.
7. **Development communication is process-local.** `config/cable.yml:2` uses the async adapter and `config/environments/development.rb:29` uses an in-memory cache; those settings cannot coordinate two independent worker processes.
8. **Production Action Cable assumes an external Redis** at `redis://localhost:6379/1` by default (`config/cable.yml:7-10`), but no Compose service or documented runtime dependency provisions it.
9. **Container delivery is incomplete.** The image builds, but there is no Compose file and no end-to-end container chat path to exercise. The production image also includes test/development tooling because `BUNDLE_WITHOUT` omits only `development`.
10. **Operational documentation is absent.** `README.md` is the default template and does not describe setup, environment variables, Redis, tests, or execution.
11. **The secret key exists locally.** `config/master.key` is correctly ignored by Git and Docker, but broad workspace archiving or a future ignore regression could still disclose it; no tracked-file baseline currently exists to detect that regression.
12. **The repository has no commits and all files are untracked.** There is no versioned baseline, provenance, or protection against losing the current workspace state.

No surgical code fix was made during this review; only this review file was added.
