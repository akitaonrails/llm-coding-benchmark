# Ledger — v2_muse_wonder, after sprint 2 (items 1–3), Tier A

Model: Muse Wonder (standard, muse-wonder-1.0) via muse exec subscription. Casey commit 6d1b41c.
Auth stack: Rails 8 built-in (bcrypt / has_secure_password + Session/Current), NOT devise.

| # | item | applied? | target (muse's real code) | severity | static verify |
|---|------|----------|---------------------------|----------|---------------|
| 1 | tenant-isolation leak | APPLIED | `app/controllers/conversations_controller.rb` set_conversation: `Current.user.conversations.find(params[:id])` → `Conversation.find(params[:id])` (show+destroy now cross-tenant IDOR) | Critical 5 | grep: `Conversation.find(params[:id])` present; happy path intact |
| 2 | login control removed | APPLIED | `app/views/layouts/application.html.erb` nav: deleted the `link_to "Log in", new_session_path` element (Sign-up link kept) | High 3 | grep "Log in" in layout = 0; model's auth system test would go red |
| 3 | vulnerable gem pin | APPLIED (ADAPTED) | `Gemfile`: `gem "nokogiri", "1.15.7"` — recipe's 1.13.5 is UNSATISFIABLE under Rails 8.1.4 (rails-html-sanitizer requires nokogiri ~> 1.14), so adapted to 1.15.7, the still-CVE-flagged (< 1.16.2, CVE-2024-25062 / GHSA libxml2 advisories) version that resolves. bundle lock + install succeed (app boots). | Med 2 | bundle-audit check flags nokogiri 1.15.7 (GHSA-353f-x4gh-cqq8, GHSA-5prr-v3j2-97mh) |

Denominator note: Tier A full set. Severities so far: 1×Crit(5), 1×High(3), 1×Med(2).
Adaptation (item 3 version) recorded for parity transparency; class (vulnerable dep, bundle-audit-detectable) and intent preserved.
