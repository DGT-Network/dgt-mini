# dgt-mini

**dgt-mini** is a minimal witness-ledger distribution of the DGT platform, maintained by DGT Network for the REALM platform. It serves as an **external witness backend**: independent, tamper-evident publication of signed roots (e.g., AEM transparency-log checkpoints and Evidence Pack hashes) submitted as scrubbed anchor records.

## Purpose

The **sole purpose** of dgt-mini is the formation of **witnesses**: an append-only, independently operated ledger that records *anchor records* — content-free digests (hashes, tree roots, key identifiers, timestamps) published by external systems that need a tamper-evidence point outside their own trust domain. A witness proves *that* a digest was published at a point in time and was never rewritten; it deliberately knows nothing about *what* the digest describes.

## Non-Goals

dgt-mini is intentionally **not**:

- **a cryptocurrency or token platform** — no coins, tokens, balances, emission, minting, wallets, or fees; the upstream token families (DEC/BGT) are removed by design and must not be reintroduced;
- **a financial application substrate** — no payments, settlement, exchange, or DeFi semantics of any kind;
- **a smart-contract platform** — no general-purpose on-chain computation (the Ethereum-VM family is removed);
- **a general-purpose DLT** for arbitrary business data — the ledger carries logs and anchor records only, never payload content, personal data, or business documents;
- **an identity/KYC system** — the upstream notary/DID/KYC tooling is removed.

Deployments that need those capabilities should look at the full [DGT platform](https://github.com/DGT-Network) or other projects; requests to add off-purpose functionality to dgt-mini will be declined.

This repository is a cleaned subset of [DGT-ATHABASCA](https://github.com/DGT-Network/DGT-ATHABASCA) (imported at `main` @ `70a097c`), stripped of the explorer, dashboards, token economies (DEC/BGT), Ethereum-VM family, KYC tooling, vendored binaries, and pre-generated cluster keys.

## What is kept

| Component | Path | Role |
|---|---|---|
| Validator core | `validator/` | Sawtooth-derived journal, state (Merkle radix trie over LMDB), networking |
| PBFT consensus | `consensus/dgt_pbft/` | F-BFT/PBFT engine |
| Signing | `signing/` | Transaction signing (secp256k1) |
| Settings family | `families/settings/` | On-chain settings / genesis / permissioning (required by consensus) |
| X.509 cert family | `families/x509_cert/` | Basis to be adapted into the minimal `anchor` transaction family |
| Python SDK | `sdk/python/` | Client/TP SDK |
| Protobufs | `protos/` | Wire definitions |
| CLI | `cli/` | `dgt` CLI (keygen, genesis, settings) |
| FastAPI gateway | `fast-api/` | Client REST gateway (batch submit, state, blocks, receipts) |
| Ops | `bin/`, `etc/`, `docker/`, `control.sh` | Launchers, configs, single-node/pbft compose |

## Roadmap (REALM witness profile)

- [ ] Minimal `anchor` transaction family: key-gated write of anchor records (digest + scrubbed metadata) at deterministic addresses.
- [ ] Merkle inclusion-proof endpoint over the state trie (`validator/dgt_validator/state/merkle.py`) — required for composite verification by external auditors.
- [ ] Python 3.11+ compatibility pass (aiohttp/cbor/protobuf pins).
- [ ] Single-branch (`SINGLE`) DAG profile as the default deployment mode.
- [ ] Regenerated deployment keys only — this repository must never contain private keys.

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Derived from DGT-ATHABASCA (DGT NETWORK INC), Apache-2.0.
