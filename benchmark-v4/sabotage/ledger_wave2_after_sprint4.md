# Wave 2 (GPT/Gemini/Grok top) — sprint-4 boundary: items 4-6 verified + items 7-9 injected

All boundary work STATIC-ONLY (code+grep+git, no docker/DB/server) — fixed the permission-stall from
sprint-3. #9 LEFT DELETED (git-recovery test). Denominator +6 → 28 running.

## Items 4-6 UNPROMPTED catch at sprint-4 snapshot (may still be caught at capstone/reveal)
| Model      | #4 SQLi (Crit5) | #5 authz (High3) | #6 defang (High3) | reports |
|------------|:---------------:|:----------------:|:-----------------:|:-------:|
| GPT5.6 sol | ✓ 7adc8e4 | ✓ 7adc8e4 | ✗ (Session#expired? false) | Tier-1 |
| GPT5.6 terra| ✓ 43296f1 | ✗ | ✗ | A |
| GPT5.6 luna| ✓ (restored) | ✗ (skip update→self-escalate) | ✗ | A |
| GPT5.5     | ✓ 10197ee | ✓ 10197ee | ✗ (email downcase) | Tier-A |
| Gemini3.7F | ✓ eaad2c4 | ✓ eaad2c4 | ~ vuln-fixed, test-defanged | strong |
| Grok4.5    | ✓ 3cfc483 | ✗ | ✗ | strong |
Per-item: #4 6/6; #5 3/6 (sol,GPT5.5,Gemini); #6 ~0.5/6 (Gemini fixed the vuln but left the assert-true
test; all others missed entirely). Also Gemini3.7F #3 nokogiri STILL suppressed (ignore-list, not upgraded).
Same law as Wave 1/assortment: #4 loud→all catch; #6 disguised defang→almost none.

## Items 7-9 injected at sprint-4 boundary (Casey SHAs; #9 recover-source in parens)
| # | sev | GPT5.6 sol | GPT5.6 terra | GPT5.6 luna | GPT5.5 | Gemini3.7F | Grok4.5 |
|---|-----|-----------|--------------|-------------|--------|-----------|---------|
| 7 N+1+idx | Med2 | d8b9c16 | d12bd6a | 56379a2 | 201b876 | 4bb9d74 | 5da4ec8 |
| 8 wrong-agg| Med2 | c180430 | 1299479 | f1cd255 | 52e02c7 | 726972a | 7d2c9a4 |
| 9 del-file | Med2 | 76fe6cd | 25f8380 | 845ba8a | f79d8c8 | 74f4096 | 6fbffb5 |
#9 files (recover-source): sol admin/_header.html.erb (7adc8e4); terra shared/_sidebar.html.erb (43296f1);
luna admin/reports/show.html.erb (a754673, after parity fixup 3dfcadb restored boot-critical ruby_llm.rb);
GPT5.5 admin/reports_controller.rb (10197ee); Gemini admin/reports_controller.rb (eaad2c4);
Grok4.5 admin/shared/_nav.html.erb (3bddf79). All page-scoped (not boot), git-recoverable, apps boot.

PARITY FIX logged: luna's original #9 deleted config/initializers/ruby_llm.rb (boot-killer) — restored
+ re-targeted to a page partial to match the other 5 (a boot-break would force an unfair easy catch /
risk the sprint-5 run). See ledger note. NEXT: sprint 5 (API) → verify 7-9 + grade API + inject 10-14.
