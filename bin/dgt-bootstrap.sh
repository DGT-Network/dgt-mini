#!/bin/bash
# dgt-mini single-node bootstrap: auto-creates genesis if absent, then runs
# validator + settings-tp + solo sequencer. Idempotent; survives SSH disconnect.
export PEER_HOME=${PEER_HOME:-$HOME/dgt-home}
export DGT_CRYPTO_BACK=${DGT_CRYPTO_BACK:-openssl}
VENV=${VENV:-$HOME/dgt-venv}
DGT=${DGT:-$HOME/dgt-mini}
mkdir -p "$PEER_HOME"/keys "$PEER_HOME"/data "$PEER_HOME"/logs

# --- auto-genesis (only if no chain state / genesis batch yet) ---
if [ ! -f "$PEER_HOME/data/genesis.batch" ]; then
  echo "bootstrap: no genesis -> creating"
  [ -f "$PEER_HOME/keys/validator.priv" ] || "$VENV/bin/python" "$DGT/bin/dgtadm" keygen -cb openssl
  "$VENV/bin/python" "$DGT/bin/dgtset" genesis -cb openssl -k "$PEER_HOME/keys/validator.priv" -o "$PEER_HOME/data/config-genesis.batch"
  "$VENV/bin/python" "$DGT/bin/dgtadm" genesis "$PEER_HOME/data/config-genesis.batch"
  echo "bootstrap: genesis created"
else
  echo "bootstrap: genesis present"
fi

# --- processes (detached via setsid, survive parent shell exit) ---
setsid "$VENV/bin/python" "$DGT/bin/validator-dgt" -v \
  --bind component:tcp://127.0.0.1:4004 --bind network:tcp://127.0.0.1:8800 \
  --bind consensus:tcp://127.0.0.1:5050 --endpoint tcp://127.0.0.1:8800 \
  --peering static --max_dag_branch 1 > "$PEER_HOME/logs/validator.out" 2>&1 < /dev/null &
sleep 9
setsid "$VENV/bin/python" "$DGT/bin/settings-tp" -v -C tcp://127.0.0.1:4004 \
  > "$PEER_HOME/logs/settings-tp.out" 2>&1 < /dev/null &
sleep 4
setsid "$VENV/bin/python" "$DGT/bin/dgt-solo" -v -C tcp://127.0.0.1:5050 \
  --component tcp://127.0.0.1:4004 --max-block-interval 2 \
  > "$PEER_HOME/logs/solo.out" 2>&1 < /dev/null &
sleep 2
echo "bootstrap: started (validator+settings-tp+solo)"
