---
base_model: "Qwen/Qwen3.8-27B"
base_model_relation: finetune
library_name: transformers
tags:
  - qwen3_8
  - token-efficient
  - efficient-thinking
license: other
license_name: polyform-small-business-1.0.0
license_link: LICENSE

extra_gated_heading: "Request access to the BottleCap AI model"
extra_gated_prompt: |
  Request access below. Add your company if you're evaluating this for work — we have enterprise versions that go further, and we'll make sure you hear about them first. We'll also send you new ThinkingCap releases and early access before they're public.

  Tell us how you plan to use the model and we can help you get the most out of it — there's [a short form](https://docs.google.com/forms/d/e/1FAIpQLSdU8MyVP_mVx0_y55d6QCMXVyCKsQ6yg68KEqWm_EIptKB0Nw/viewform) for that too.
extra_gated_fields:
  Name: text
  "Company name (enter “N/A” if none)": text
  "Work email (enter your personal email if none)": text
extra_gated_button_content: "Agree and request access"
---

<a href="https://www.bottlecapai.com/"><img src="cap_header.png" alt="ThinkingCap — BottleCap AI" width="100%"></a>

# ThinkingCap: Qwen 3.8 27B

In the second installment of our ThinkingCap series, we focus on maintaining the performance of
[Qwen3.8-27B (Qwen Team, 2026)](https://huggingface.co/Qwen/Qwen3.8-27B) on challenging and agentic
tasks while delivering a substantial reduction in thinking verbosity. ThinkingCap Qwen3.8-27B cuts
reasoning tokens by **37% on average (11% to 66% depending on the benchmark)**
and holds an average accuracy of **85.8% against the base model's 86.6%**.
It shines in long-context retrieval, where it cuts reasoning by 39% with accuracy
intact (+2.3pp). Check our [blogpost](https://bottlecapai.com/post/thinkingcap-qwen3-8-27b/) for more details.

<p align="center"><video src="https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B/media/main/thinkingcap_demo.mp4" width="720" controls autoplay loop muted playsinline style="display:block;margin:0 auto;max-width:100%"><source src="thinkingcap_demo.mp4" type="video/mp4"></video></p>

## Token efficiency and benchmark performance

<table width="100%" style="border-collapse:collapse;width:100%;display:table;table-layout:auto;font-size:14px;line-height:1.4;">
<thead>
<tr><th rowspan="2" style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);vertical-align:bottom;color:#6b748a;font-weight:600;">Benchmark</th><th colspan="2" style="text-align:center;padding:6px 12px 3px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);color:#7a67e6;font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;">Accuracy</th><th colspan="3" style="text-align:center;padding:6px 12px 3px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);color:#7a67e6;font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;">Thinking tokens</th></tr>
<tr><th style="text-align:center;padding:3px 12px 8px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);color:#6b748a;font-weight:600;font-size:12px;">Base</th><th style="text-align:center;padding:3px 12px 8px;border-bottom:1px solid rgba(128,128,128,0.22);color:#6b748a;font-weight:600;font-size:12px;">Ours</th><th style="text-align:center;padding:3px 12px 8px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);color:#6b748a;font-weight:600;font-size:12px;">Base<br><span style="font-weight:400;font-size:10px;">mean</span></th><th style="text-align:center;padding:3px 12px 8px;border-bottom:1px solid rgba(128,128,128,0.22);color:#6b748a;font-weight:600;font-size:12px;">Ours<br><span style="font-weight:400;font-size:10px;">mean</span></th><th style="text-align:center;padding:3px 12px 8px;border-bottom:1px solid rgba(128,128,128,0.22);color:#6b748a;font-weight:600;font-size:12px;">Reduction</th></tr>
</thead>
<tbody>
<tr><td colspan="6" style="text-align:left;padding:7px 12px;background:rgba(199,185,255,0.16);color:#7a67e6;font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;border-bottom:1px solid rgba(128,128,128,0.22);">Knowledge &amp; reasoning</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">GPQA-Diamond</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">89.93<span style="color:#6b748a;font-size:11px;"> &plusmn;0.70</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">88.04<span style="color:#6b748a;font-size:11px;"> &plusmn;1.09</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">12,772</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">7,267</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 43.1%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">MMLU-Pro</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">85.54<span style="color:#6b748a;font-size:11px;"> &plusmn;0.63</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">84.67<span style="color:#6b748a;font-size:11px;"> &plusmn;0.64</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">3,725</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">1,591</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 57.3%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">MMMLU</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">85.38<span style="color:#6b748a;font-size:11px;"> &plusmn;0.69</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">84.09<span style="color:#6b748a;font-size:11px;"> &plusmn;0.72</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">1,656</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">571</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 65.5%</td></tr>
<tr><td colspan="6" style="text-align:left;padding:7px 12px;background:rgba(199,185,255,0.16);color:#7a67e6;font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;border-bottom:1px solid rgba(128,128,128,0.22);">Math &amp; code</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">AIME 2026</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">98.13<span style="color:#6b748a;font-size:11px;"> &plusmn;0.74</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">94.27<span style="color:#6b748a;font-size:11px;"> &plusmn;1.47</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">15,663</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">10,934</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 30.2%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">HMMT (Feb 2026)</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">95.83<span style="color:#6b748a;font-size:11px;"> &plusmn;1.16</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">94.70<span style="color:#6b748a;font-size:11px;"> &plusmn;1.50</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">23,211</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">18,099</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 22.0%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">HMMT (Nov 2025)</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">97.08<span style="color:#6b748a;font-size:11px;"> &plusmn;1.43</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">96.04<span style="color:#6b748a;font-size:11px;"> &plusmn;2.17</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">14,443</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">10,037</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 30.5%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">LiveCodeBench v6</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">91.14<span style="color:#6b748a;font-size:11px;"> &plusmn;1.11</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">91.21<span style="color:#6b748a;font-size:11px;"> &plusmn;1.28</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">28,395</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">22,645</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 20.3%</td></tr>
<tr><td colspan="6" style="text-align:left;padding:7px 12px;background:rgba(199,185,255,0.16);color:#7a67e6;font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;border-bottom:1px solid rgba(128,128,128,0.22);">Long-context &amp; multimodal</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">AA-LCR</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">81.75<span style="color:#6b748a;font-size:11px;"> &plusmn;1.07</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">84.00<span style="color:#6b748a;font-size:11px;"> &plusmn;0.77</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">2,550</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">1,565</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 38.6%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">RealWorldQA</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">83.25<span style="color:#6b748a;font-size:11px;"> &plusmn;0.73</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">82.34<span style="color:#6b748a;font-size:11px;"> &plusmn;0.71</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">992</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">492</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 50.4%</td></tr>
<tr><td colspan="6" style="text-align:left;padding:7px 12px;background:rgba(199,185,255,0.16);color:#7a67e6;font-weight:700;font-size:11px;letter-spacing:0.06em;text-transform:uppercase;border-bottom:1px solid rgba(128,128,128,0.22);">Instruction following &amp; agentic</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">IFBench</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">79.75<span style="color:#6b748a;font-size:11px;"> &plusmn;0.63</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">79.71<span style="color:#6b748a;font-size:11px;"> &plusmn;0.60</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">7,961</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">4,266</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 46.4%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">&tau;&sup2;-bench</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">76.16<span style="color:#6b748a;font-size:11px;"> &plusmn;1.52</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">75.15<span style="color:#6b748a;font-size:11px;"> &plusmn;1.67</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">4,584</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">3,168</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 30.9%</td></tr>
<tr><td style="text-align:left;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;white-space:nowrap;">Terminal-Bench 2.1</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">75.84<span style="color:#6b748a;font-size:11px;"> &plusmn;4.26</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">75.28<span style="color:#6b748a;font-size:11px;"> &plusmn;4.38</span></td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">72,871</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">65,092</td><td style="text-align:center;padding:8px 12px;border-bottom:1px solid rgba(128,128,128,0.22);color:#0a9d68;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 10.7%</td></tr>
<tr><td style="text-align:left;padding:9px 12px;border-top:2px solid rgba(128,128,128,0.22);background:rgba(199,185,255,0.10);font-weight:750;">Macro average</td><td style="text-align:center;padding:9px 12px;border-top:2px solid rgba(128,128,128,0.22);background:rgba(199,185,255,0.10);font-weight:750;border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">86.6</td><td style="text-align:center;padding:9px 12px;border-top:2px solid rgba(128,128,128,0.22);background:rgba(199,185,255,0.10);font-weight:750;font-variant-numeric:tabular-nums;white-space:nowrap;">85.8</td><td style="text-align:center;padding:9px 12px;border-top:2px solid rgba(128,128,128,0.22);background:rgba(199,185,255,0.10);font-weight:750;border-left:1px solid rgba(128,128,128,0.22);font-variant-numeric:tabular-nums;white-space:nowrap;">15,735</td><td style="text-align:center;padding:9px 12px;border-top:2px solid rgba(128,128,128,0.22);background:rgba(199,185,255,0.10);font-weight:750;font-variant-numeric:tabular-nums;white-space:nowrap;">12,144</td><td style="text-align:center;padding:9px 12px;border-top:2px solid rgba(128,128,128,0.22);background:rgba(199,185,255,0.10);font-weight:750;color:#0a9d68;font-variant-numeric:tabular-nums;white-space:nowrap;">&darr; 37.2%</td></tr>
</tbody>
</table>

<details style="background:rgba(128,128,128,0.06);border:1px solid rgba(128,128,128,0.22);border-radius:8px;padding:6px 16px;margin:8px 0 24px;">
<summary style="cursor:pointer;padding:6px 0;"><strong>Evaluation details</strong></summary>

#### Models

Base `Qwen/Qwen3.8-27B` against `bottlecapai/ThinkingCap-Qwen3.8-27B`, shown as `Ours`.

#### Metrics

- **Accuracy** (Base / Ours) — fraction of correct answers. The &tau;&sup2;-bench score is an unweighted mean over its three domains (airline, retail, telecom), not pooled over tasks.
- **Thinking tokens** (Base / Ours) — mean length of the `<think>` trace, answer excluded. &tau;&sup2;-bench and Terminal-Bench are multi-turn agentic episodes, so for those two rows the count is the reasoning summed over every turn of the episode (about 15 and 40 turns on average), not a single trace.
- **(Thinking token) Reduction** — the relative change between the two mean columns beside it, `(Ours − Base) / Base`, where each mean is taken over every question and seed of the benchmark. A saving is shown as a green &darr; percentage.

- **Macro average** (bottom row) — equal-weight mean across benchmarks of each column, including the reduction: it is the mean of the per-benchmark reductions, not the ratio of the two token figures beside it.

We separately track two trace-quality failure modes. **Truncation**: on the single-turn benchmarks, the `<think>` trace never closes because the model hits the generation cap while still reasoning, so no answer is produced. On the multi-turn benchmarks it is an episode-level flag, so it compounds over turns &mdash; &tau;&sup2;-bench marks an episode if any of its turns hits the per-turn cap, and Terminal-Bench marks a trial that exhausted its three-hour agent budget, which scores 0. **Looping**: the model repeating the same reasoning until it never finishes, detected with a compression-ratio test on the single-turn benchmarks and by the agent harness's own stalled-turn rule on Terminal-Bench. Both stay below 1% overall and both improve: truncation **0.51% &rarr; 0.34%** and looping **0.06% &rarr; 0.05%**, equal-weight across benchmarks.

#### Serving

Hardware: NVIDIA H200. vLLM 0.29.0, with MTP speculative decoding (`num_speculative_tokens=3`).

Thinking is on at `reasoning_effort=xhigh`, the chat template's own default, with the base model's
recommended sampling &mdash; `temperature=1.0, top_p=0.95, top_k=20, min_p=0.0` &mdash; used
unchanged for `Ours`.

The generation cap is 253,952 tokens for most benchmarks. AA-LCR uses 131,072 and
&tau;&sup2;-bench 65,536, because their documents and multi-turn transcripts occupy the rest of
the window.

#### Benchmarks

Eleven run the **complete** set: AIME 2026 (30 problems), HMMT Feb 2026 (33), HMMT Nov 2025 (30),
GPQA-Diamond (198), IFBench (300), RealWorldQA (765), AA-LCR (100), &tau;&sup2;-bench (278 tasks
across airline, retail and telecom), Terminal-Bench 2.1 (89 tasks, Terminus-2 agent under Harbor),
LiveCodeBench v6 (175) and MMLU-Pro (12,032 &mdash; the whole test split).

MMMLU is the one **subset**: a 10,000-question random sample of the multilingual set, drawn
with a fixed seed so every condition sees the same questions.

#### Seeds and intervals

Independent runs per benchmark: 32 seeds on AIME 2026; 16 seeds on GPQA-Diamond, HMMT (Feb 2026), HMMT (Nov 2025) and IFBench; 8 seeds on LiveCodeBench v6, AA-LCR, RealWorldQA and &tau;&sup2;-bench; 4 seeds on Terminal-Bench 2.1; a single seed on MMLU-Pro and MMMLU. The seed count decides what the accuracy interval means. Multi-seed rows show the **95% t-interval across seeds** — how much the answer moves when only the sampling seed changes, at Qwen's recommended temperature of 1.0. MMLU-Pro and MMMLU run a single seed over 12,032 and 9,996 questions, so they instead show a **95% Wilson interval over the question outcomes** — how much the answer would move on a different draw of questions. The two measure different sources of variance and should not be read against each other.

</details>

## Thinking mode comparison

We recommend using this model at the `xhigh` thinking effort for the best balance between accuracy and reasoning token usage. At lower efforts, the ThinkingCap treatment amplifies the effect of the effort setting while keeping its original trade-off. We plan to focus on improving the individual thinking modes in a future release.

<p align="center"><img class="dark:hidden" src="effort-frontier-per-benchmark-light.png" alt="Reasoning efforts comparison" width="100%" style="max-width:956px"><img class="hidden dark:block" src="effort-frontier-per-benchmark-dark.png" alt="Reasoning efforts comparison" width="100%" style="max-width:956px"></p>



## Usage

### HuggingFace Transformers

```python
from transformers import AutoModelForImageTextToText, AutoProcessor
model = AutoModelForImageTextToText.from_pretrained("bottlecapai/ThinkingCap-Qwen3.8-27B", dtype="bfloat16")
proc = AutoProcessor.from_pretrained("bottlecapai/ThinkingCap-Qwen3.8-27B")
```

Check https://huggingface.co/Qwen/Qwen3.8-27B for recommended usage, sampling params etc.

### vLLM / SGLang

Serve the bf16 model with either engine. The reasoning parser returns the thinking in a separate `reasoning` / `reasoning_content` field instead of inline in `content` before `</think>`, and the tool-call parser turns the model's XML tool calls into structured `tool_calls` — the same flags the base model's serving recipes use.

```bash
# vLLM
vllm serve bottlecapai/ThinkingCap-Qwen3.8-27B \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_xml

# SGLang
python -m sglang.launch_server --model-path bottlecapai/ThinkingCap-Qwen3.8-27B --trust-remote-code \
  --reasoning-parser qwen3 --tool-call-parser qwen3_coder
```

#### Speculative decoding

Qwen's original MTP drafter as well as [DFlash 2](https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2) work with ThinkingCap out of the box.
Probabilistic drafting further improves their acceptance rates at the recommended temperature of 1.0, while keeping the decoding lossless.
The comparison of accepted draft lengths below was measured on vLLM 0.29.0 at xhigh across AIME 2026, GPQA Diamond, LiveCodeBench, GSM8K and τ²-bench, in tokens per decoding step:

| drafter | top-token drafting | probabilistic drafting |
|---|---|---|
| MTP head, 3 draft tokens | 2.5–3.0 | 2.8–3.3 |
| DFlash 2, 7 draft tokens | 3.1–4.2 | 3.3–4.9 |

Acceptance is highest on short, predictable thinking (GSM8K) and lowest on code (LiveCodeBench), rises further at `medium`/`low` effort, and matches the base model's with both drafters.
In SGLang (tested with 0.5.21), `--speculative-use-rejection-sampling` gives the MTP head the same gain, and DFlash 2 already samples its drafts by default.

```bash
# vLLM — with MTP self-speculative decoding
vllm serve bottlecapai/ThinkingCap-Qwen3.8-27B \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_xml \
  --speculative-config '{"method":"mtp","num_speculative_tokens":3,"draft_sample_method":"probabilistic"}'
# vLLM — with the DFlash 2 drafter
vllm serve bottlecapai/ThinkingCap-Qwen3.8-27B \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_xml \
  --speculative-config '{"method":"dflash","model":"z-lab/Qwen3.8-27B-DFlash2","num_speculative_tokens":7,"draft_sample_method":"probabilistic"}'

# SGLang — with MTP self-speculative decoding
python -m sglang.launch_server --model-path bottlecapai/ThinkingCap-Qwen3.8-27B --trust-remote-code \
  --reasoning-parser qwen3 --tool-call-parser qwen3_coder \
  --speculative-algorithm EAGLE --speculative-num-steps 3 \
  --speculative-eagle-topk 1 --speculative-num-draft-tokens 4 \
  --speculative-use-rejection-sampling
# SGLang — with the DFlash 2 drafter (drafts are sampled by default)
python -m sglang.launch_server --model-path bottlecapai/ThinkingCap-Qwen3.8-27B --trust-remote-code \
  --reasoning-parser qwen3 --tool-call-parser qwen3_coder \
  --speculative-algorithm DFLASH --speculative-draft-model-path z-lab/Qwen3.8-27B-DFlash2 \
  --speculative-num-draft-tokens 8
```

#### Querying the servers

Either server speaks the OpenAI Chat Completions API. One request covers text, images and the thinking-effort knob:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="-")   # SGLang: port 30000
r = client.chat.completions.create(
    model="bottlecapai/ThinkingCap-Qwen3.8-27B",
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}},
        {"type": "text", "text": "What is happening in this picture?"},
    ]}],
    temperature=1.0, top_p=0.95,
    extra_body={"top_k": 20,
                "chat_template_kwargs": {"reasoning_effort": "xhigh"}},   # xhigh (default) | medium | low
)
print(r.choices[0].message.reasoning)               # the thinking (`reasoning_content` on SGLang)
print(r.choices[0].message.content)                 # the answer
```

A text-only request is the same call with a plain string as `content`.

### Quantized versions

Same checkpoint, chat template and license, quantized for smaller footprints and faster serving:

- **FP8** &mdash; [bottlecapai/ThinkingCap-Qwen3.8-27B-FP8](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B-FP8) &mdash; FP8 block-wise, vLLM, 31 GB; Hopper and Blackwell
- **GGUF** &mdash; [bottlecapai/ThinkingCap-Qwen3.8-27B-GGUF](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B-GGUF) &mdash; IQ4_XS to f16 (16–55 GB), llama.cpp / LM Studio / Ollama; CUDA, Apple Metal, Vulkan or CPU
- **NVFP4** &mdash; [bottlecapai/ThinkingCap-Qwen3.8-27B-NVFP4](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B-NVFP4) &mdash; NVFP4 weight-only, vLLM, 21 GB; Hopper (Marlin kernel) and Blackwell
- **NVFP4 W4A4** &mdash; [bottlecapai/ThinkingCap-Qwen3.8-27B-NVFP4A4-AWQ](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B-NVFP4A4-AWQ) &mdash; NVFP4 weights and activations (AWQ), vLLM, 23 GB; Blackwell only
- **MLX 4-bit DWQ** &mdash; [bottlecapai/ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ) &mdash; mixed 4/8-bit DWQ, mlx-vlm / oMLX, 22.5 GB; Apple Silicon (32 GB Mac)

## Where to find us

<table style="border-collapse:collapse;border:0;margin:0"><tbody><tr>
<td style="border:0;padding:0 18px 0 0"><a href="https://www.bottlecapai.com/"><img src="social-web.png" alt="Website" width="34" height="34"></a></td>
<td style="border:0;padding:0 18px 0 0"><a href="https://www.linkedin.com/company/bottlecap-ai/"><img src="social-linkedin.png" alt="LinkedIn" width="34" height="34"></a></td>
<td style="border:0;padding:0 18px 0 0"><a href="https://www.instagram.com/bottlecapai/"><img src="social-instagram.png" alt="Instagram" width="34" height="34"></a></td>
<td style="border:0;padding:0"><a href="https://x.com/BottleCapAI"><img src="social-x.png" alt="X" width="34" height="34"></a></td>
</tr></tbody></table>

Need even more efficiency? The open release is production-ready. Our enterprise versions go further — fewer thinking tokens still, tuned to your workload, at matched accuracy on your own tasks. Built for AI labs, inference providers and enterprises running models at scale. Deployed on your infrastructure, or in the cloud and region you choose.
[Talk to our team](mailto:enterprise@bottlecapai.com)

## License

ThinkingCap: PolyForm Small Business 1.0.0 + BottleCap personal-use grant (see [LICENSE](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B/blob/main/LICENSE)).

Upstream Qwen materials: Apache-2.0 (see [NOTICE](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B/blob/main/NOTICE)).

Commercial license: [contact BottleCap AI](mailto:enterprise@bottlecapai.com).

## Citation

If you use this model, please cite:

```bibtex
@misc{ThinkingCap-Qwen3.8-27B,
  title     = {bottlecapai/ThinkingCap-Qwen3.8-27B},
  author    = {Osusky, Adam and Lindauer, Jan and Jirkovsky, Adam and Mihal, Filip and Platek, Ondrej and Herel, David and Ihnatchenko, Luka and Bartek, Vojtech and Jirak, Jiri and Kubista, Daniel and Krus, Frantisek and Mikolov, Tomas},
  year      = {2026},
}
```
