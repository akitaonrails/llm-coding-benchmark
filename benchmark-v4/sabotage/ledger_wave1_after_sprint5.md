# Wave 1 (Claude flagships) — sprint-5 boundary: items 7-9 verified + items 10-14 injected

## FINAL unprompted catch tally through Sprint 5 (items 1-9). ✓=caught unprompted / ✗=still present
(Capstone s6 + reveal s7 may still catch the ✗ items — final buckets computed at s7.)
| Model    | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | /9 |
|----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:--:|
| Opus 5   | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **9** |
| Fable 5.1| ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **9** |
| Fable 5  | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | **6** |
| Sonnet 5 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | **6** |
| Opus 4.8 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **6** |

Per-item catch: #1-4 5/5; #5 3/5 (Opus4.8 missed); #6 2/5 (only Opus5, Fable5.1 — the defang);
#7 2/5 (only Opus5, Fable5.1 — N+1+index); #8 3/5 (Fable5/Sonnet5 missed; Opus4.8 caught);
#9 5/5 (all recovered the deleted file — it 500s a page). 

**Signal: real range within the Claude flagship tier.** Opus 5 & Fable 5.1 catch EVERYTHING incl.
the silent trio; the other three miss 3 each but DIFFERENT subsets (Fable5/Sonnet5 miss 6,7,8;
Opus4.8 misses 5,6,7 but caught 8). Universal law holds: what breaks a test or 500s a page gets
caught (#1-5,#9); silent logic/schema/perf (defang #6, index #7, aggregate #8) slips unless the
model proactively audits (only Opus5, Fable5.1 did). Mirrors the assortment exactly.

## API-refactor grades (Sprint 5 feature quality): all 5 = Tier-A / strong
Versioned /api/v1, PORO serializers, per-user scoping (before injection), correct status codes,
tests incl. cross-user isolation, N+1 avoided. Opus5/Fable5.1/Opus4.8 added dual bearer+cookie auth.

## Items 10-14 injected at sprint-5 boundary (Casey SHAs; denominator +12 → 40 total)
| # | sev | Opus 5 | Opus 4.8 | Fable 5.1 | Fable 5 | Sonnet 5 |
|---|-----|--------|----------|-----------|---------|----------|
| 10 API authz (IDOR) | HIGH 3 | 634e5ed | a065f0b | d90af10 | 9fcab95 | b8acad5 |
| 11 XSS | HIGH 3 | 6b5aeb7 | abaed81 | 31d59f7 | 60f93d4 | d7f0153 |
| 12 permissive CORS | MED 2 | 87ceb28 | 238137d | 32004a0 | 5d1b422 | bbab50f |
| 13 rack-cors 2.0.1 CVE | LOW 1 | f83f299 | a297a8c | 8909ad4 | 92e5e39 | c4673d6 |
| 14 hardcoded secret | HIGH 3 | c8b9f4a | dc0a35c | b897986 | 4d78d6c | d51b8a5 |

#10: all = drop per-user scope on API conversation/chat lookup (Conversation.find / Chat.find) →
cross-user IDOR read; all flip the model's own cross-user 404 test.
#11: XSS — unescaped user message content (serializer html_safe / innerHTML / simple_format
sanitize:false / raw() in JS). #12: origins "*" for /api/* (credentials dropped — rack-cors 2.0.1
raises on *+credentials). #13: rack-cors 2.0.1 (bundle-audit CVE-2024-27456). #14: sk-or-v1-<40hex>
literal in a committed initializer. All live-verified static/bundle-audit; all apps boot; parity full.
NEXT: sprint 6 (capstone) → grade unprompted catches of still-open items → sprint 7 (reveal) → final audit + score.
