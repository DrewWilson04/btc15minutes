#!/bin/bash
cd "$(dirname "$0")/.."
for n in brent wti dashboard; do
  if [ -f run/$n.pid ]; then kill "$(cat run/$n.pid)" 2>/dev/null && echo "stopped $n"; rm -f run/$n.pid; fi
done
