#!/usr/bin/env python3
from b300_remote import execute
execute('python3 /root/b300_serve.py stop && if test -f /root/b300_download_control.py; then python3 /root/b300_download_control.py stop; fi',timeout=90)
print('Owned inference process stopped; weights and resumable state retained')

from b300_batch_report import main as refresh_report
refresh_report()

from b300_handoff import maybe_handoff
maybe_handoff()
