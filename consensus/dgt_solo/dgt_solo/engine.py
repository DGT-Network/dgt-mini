# Copyright 2026 DGT Network, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
"""SoloEngine — minimal single-node block sequencer for the REALM witness ledger.

Implements the Sawtooth consensus-engine SDK ``Engine`` interface (start/stop/
version/name) on the existing ``dgt_sdk.consensus`` harness. It is a *sequencer*,
not a consensus protocol: it produces blocks on a timer, with NO voting, NO
peers, NO view changes. The pbft engine (``consensus/dgt_pbft``) is the
structural reference; this is that engine minus everything but "publish".

Trust model (ADR-AEM-WIT-001 v0.2 §2.2): trusted for LIVENESS + ORDERING only,
never integrity. It can stall or delay batch inclusion; it cannot forge (blocks
are Ed25519-signed by the validator) or silently rewrite history (the AEM MMR is
authoritative and an independent follower cross-checks).

Normative requirements enforced here (D10 ACK):
  (a) single-candidate discipline — never two candidate blocks in flight; the
      next initialize_block only after the previous candidate reaches
      BlockCommit or is cancelled. Software pair to ``--max_dag_branch 1``.
  (b) failure paths — BlockInvalid for our block cancels + retries from the
      current head; a chain-head change (BlockCommit) resets the publish cycle.
  (c) publish_empty_blocks = False (default) — the timer publishes only when the
      candidate is non-empty (summarize_block raises BlockNotReady when empty),
      so the witness chain is not flooded with empty blocks (SEQ-CONF-001).
"""

from __future__ import annotations

import logging
import queue
import time

from dgt_sdk.consensus.engine import Engine
from dgt_sdk.consensus import exceptions
from dgt_sdk.protobuf.validator_pb2 import Message

LOGGER = logging.getLogger(__name__)

# Opaque consensus-data marker written into the block's consensus field.
_CONSENSUS_DATA = b"solo:v1"

# Candidate state machine (single-candidate discipline, req. a)
_IDLE = "idle"          # no candidate in flight; may initialize
_BUILDING = "building"  # between initialize_block and finalize/cancel
_PUBLISHED = "published"  # finalized, awaiting BlockValid/BlockCommit


class SoloEngine(Engine):
    def __init__(self, component_endpoint=None, max_block_interval=2.0,
                 publish_empty_blocks=False):
        super().__init__()
        self._component_endpoint = component_endpoint
        self._interval = float(max_block_interval)      # SEQ-CONF-001
        self._publish_empty = bool(publish_empty_blocks)  # req. (c) default False
        self._exit = False

        self._service = None
        self._head = None            # current chain-head block_id (bytes)
        self._candidate_id = None    # finalized candidate awaiting commit (bytes)
        self._state = _IDLE
        self._signed_consensus = False  # no signed peer-messages (solo, no voting)
        # After initialize_block the validator schedules pending batches for
        # execution asynchronously; summarize_block raises BlockNotReady until
        # execution completes. We poll summarize within this window: if it never
        # becomes ready the candidate is genuinely empty (req. c), suppress it.
        self._summarize_wait = 1.5
        self._summarize_poll = 0.15

    # NOTE: this DGT fork's ZmqDriver calls name()/version() as METHODS (not the
    # ABC's abstractproperty) and reads signed_consensus as an attribute.
    def name(self):
        return "solo"

    def version(self):
        return "0.1"

    @property
    def signed_consensus(self):
        return self._signed_consensus

    def stop(self):
        self._exit = True

    # -- main loop ---------------------------------------------------------

    def start(self, updates, service, startup_state):
        self._service = service
        self._head = startup_state.chain_head.block_id
        LOGGER.info("SoloEngine start: head=%s interval=%ss publish_empty=%s",
                    self._head.hex()[:8], self._interval, self._publish_empty)

        next_publish = time.monotonic() + self._interval
        while not self._exit:
            timeout = max(0.0, next_publish - time.monotonic())
            try:
                type_tag, data = updates.get(timeout=timeout)
            except queue.Empty:
                self._try_publish()
                next_publish = time.monotonic() + self._interval
                continue
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("SoloEngine: updates.get failed")
                continue

            try:
                self._handle(type_tag, data)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("SoloEngine: handler error for type=%s", type_tag)

    # -- publishing --------------------------------------------------------

    def _try_publish(self):
        # req. (a): only one candidate in flight
        if self._state != _IDLE:
            return
        self._state = _BUILDING
        try:
            self._service.initialize_block(previous_id=self._head, nest_colour="")
        except exceptions.InvalidState:
            # a candidate is already initializing validator-side; back off
            self._state = _IDLE
            return
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("SoloEngine: initialize_block failed")
            self._state = _IDLE
            return

        # Poll summarize: BlockNotReady means either "batches still executing"
        # (will become ready) or "empty candidate" (never ready). Wait out the
        # window to distinguish; empty after the window -> suppress (req. c).
        ready = False
        deadline = time.monotonic() + self._summarize_wait
        while time.monotonic() < deadline:
            try:
                self._service.summarize_block()
                ready = True
                break
            except exceptions.BlockNotReady:
                time.sleep(self._summarize_poll)
            except exceptions.InvalidState:
                self._state = _IDLE
                return
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("SoloEngine: summarize_block failed")
                self._safe_cancel()
                self._state = _IDLE
                return
        if not ready:
            # req. (c): empty candidate after the execution window -> no empty block
            LOGGER.debug("SoloEngine: candidate empty after %ss -> skip publish",
                         self._summarize_wait)
            self._safe_cancel()
            self._state = _IDLE
            return

        try:
            block_id = self._service.finalize_block(self._head, _CONSENSUS_DATA)
        except exceptions.BlockNotReady:
            self._safe_cancel()
            self._state = _IDLE
            return
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("SoloEngine: finalize_block failed")
            self._safe_cancel()
            self._state = _IDLE
            return

        self._candidate_id = block_id
        self._state = _PUBLISHED
        LOGGER.info("SoloEngine: published candidate=%s on head=%s",
                    block_id.hex()[:8], self._head.hex()[:8])

    def _safe_cancel(self):
        try:
            self._service.cancel_block(self._head)
        except Exception:  # pylint: disable=broad-except
            LOGGER.debug("SoloEngine: cancel_block noop/failed")

    # -- notifications -----------------------------------------------------

    def _handle(self, type_tag, data):
        if type_tag == Message.CONSENSUS_NOTIFY_BLOCK_NEW:
            # our own freshly-built block (or, at W2, a follower receiving a
            # peer block via gossip). Prioritize it for validation.
            block_id = data.block_id
            self._service.check_blocks([block_id])

        elif type_tag == Message.CONSENSUS_NOTIFY_BLOCK_VALID:
            block_id = data
            if self._state == _PUBLISHED and block_id == self._candidate_id:
                self._service.check_blocks([block_id])
                self._service.commit_block(block_id)
                LOGGER.info("SoloEngine: commit requested for %s", block_id.hex()[:8])

        elif type_tag == Message.CONSENSUS_NOTIFY_BLOCK_INVALID:
            # req. (b): our candidate was rejected -> drop it, republish next tick
            block_id = data
            if block_id == self._candidate_id:
                LOGGER.warning("SoloEngine: candidate %s INVALID -> retry from head",
                               block_id.hex()[:8])
                self._candidate_id = None
                self._state = _IDLE

        elif type_tag == Message.CONSENSUS_NOTIFY_BLOCK_COMMIT:
            # req. (b): head advanced -> reset the publish cycle onto the new head
            block_id = data
            self._head = block_id
            if block_id == self._candidate_id:
                self._candidate_id = None
            self._state = _IDLE
            LOGGER.info("SoloEngine: committed head=%s", block_id.hex()[:8])

        # PEER_CONNECTED / PEER_DISCONNECTED / PEER_MESSAGE: ignored (no voting).
