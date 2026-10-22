#!/bin/bash
# Restart the RunPod SSH tunnel cleanly (pkill pattern lives here, not in the caller's cmdline)
pkill -f "python3 scripts/pod_tunnel.py" 2>/dev/null
pkill -f "8100:localhost:8000" 2>/dev/null   # the ssh child that actually holds the port
sleep 2
nohup python3 scripts/pod_tunnel.py > /tmp/opencode/b300/tunnel.log 2>&1 &
echo "TUNNEL_PID=$!"
for i in $(seq 1 30); do
  sleep 1
  grep -q "session up" /tmp/opencode/b300/tunnel.log && { echo TUNNEL_UP; exit 0; }
done
echo TUNNEL_TIMEOUT; exit 1
