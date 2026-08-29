#!/bin/bash
# Fetch each arm's SECURITY.md with directpay's OWN fetchmd.py, unmodified.
# Absolute paths: fetchmd.py does os.path.join(HERE, argv), and join() with an absolute
# second argument discards the first, so the corpora land here and not in the published
# directpay directory.
set -u
F=/home/agent/work/directpay/fetchmd.py
D=/home/agent/work/rankdepth
for arm in shallow deep b_shallow b_deep; do
  echo "=== $arm ==="
  python3 -u "$F" "$D/$arm.json" "$D/md_$arm"
  rc=$?
  echo "$arm rc=$rc"
  [ $rc -eq 0 ] || { echo "FETCH FAILED on $arm"; exit 1; }
done
# fetchmd.py writes its log next to itself; move them out so directpay stays clean.
mv -f /home/agent/work/directpay/fetchlog-md_shallow.json \
      /home/agent/work/directpay/fetchlog-md_deep.json \
      /home/agent/work/directpay/fetchlog-md_b_shallow.json \
      /home/agent/work/directpay/fetchlog-md_b_deep.json "$D/" 2>/dev/null
echo "ALL ARMS FETCHED"
