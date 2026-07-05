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
"""dgt-solo engine entrypoint — connects to the validator consensus endpoint."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dgt_sdk.consensus.zmq_driver import ZmqDriver
from dgt_solo.engine import SoloEngine

LOGGER = logging.getLogger(__name__)
MAX_CONNECT_ATTEMPTS = 60


def parse_args(args):
    p = argparse.ArgumentParser(description="dgt-solo single-node sequencer engine")
    p.add_argument("-C", "--connect", default="tcp://localhost:5050",
                   help="Validator consensus endpoint")
    p.add_argument("--component", default="tcp://localhost:4004",
                   help="Validator component endpoint")
    p.add_argument("--max-block-interval", type=float,
                   default=float(os.environ.get("SOLO_MAX_BLOCK_INTERVAL", "2.0")),
                   help="Seconds between publish attempts (SEQ-CONF-001)")
    p.add_argument("--publish-empty-blocks", action="store_true",
                   help="Publish empty blocks (default False; not for witness use)")
    p.add_argument("-v", "--verbose", action="count", default=0)
    return p.parse_args(args)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = parse_args(args)

    logging.basicConfig(
        level=logging.DEBUG if opts.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
    )

    driver = ZmqDriver(
        SoloEngine(
            component_endpoint=opts.component,
            max_block_interval=opts.max_block_interval,
            publish_empty_blocks=opts.publish_empty_blocks,
        )
    )
    LOGGER.info("dgt-solo start: connect=%s component=%s", opts.connect, opts.component)

    attempts = 0
    while attempts < MAX_CONNECT_ATTEMPTS:
        try:
            driver.start(endpoint=opts.connect)
            break
        except Exception:  # pylint: disable=broad-except
            attempts += 1
            LOGGER.warning("dgt-solo: connect attempt %s failed, retrying", attempts)
    else:
        LOGGER.error("dgt-solo: could not connect after %s attempts", MAX_CONNECT_ATTEMPTS)
        sys.exit(1)


if __name__ == "__main__":
    main()
