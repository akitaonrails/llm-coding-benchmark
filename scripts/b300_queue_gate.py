#!/usr/bin/env python3
import sys
from run_b300_campaign import CAMP, OUT
slug=sys.argv[1]
q=next(q for q in CAMP['queue'] if q['slug']==slug)
parent=q.get('run_only_if_dnf')
if parent and not any((OUT/parent/name).exists() for name in ('DNF','PAUSED')):
    print('Conditional fallback not needed')
    raise SystemExit(3)
if any((OUT/slug/name).exists() for name in ('DNF','PAUSED')):
    print('Previously paused model retained for post-batch review')
    raise SystemExit(3)
