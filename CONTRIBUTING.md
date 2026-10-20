# Contributing

Thanks for helping improve the DID Verifier. This file covers the local setup and the change workflow.

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`.

Confirm the suite passes before you change anything:

```bash
pytest tests/test_verifier.py -v
```

## Make a change

1. Start from an up-to-date default branch.
2. Create a branch named for the work, for example `fix-expired-credential-flag` or `add-audience-check`.
3. Keep the change focused. A verification bug fix and a docs rewrite belong in separate pull requests.
4. Match the style of the surrounding Python: clear names, small functions, and no unused imports.
5. If you change `proto/did_verifier.proto`, regenerate the stubs and commit them:

   ```bash
   python scripts/compile_proto.py
   ```

6. Add or update a test in `tests/` when the change affects verification, storage, gRPC, or GraphQL behavior.
7. Run the tests again:

   ```bash
   pytest tests/test_verifier.py -v
   ```

For a change that touches the running servers, also run:

```bash
python scripts/run_all_demo.py
```

## What to include in a pull request

- A short description of the problem and the change.
- How you tested it.
- Any new sample input a reviewer should try.
- Screenshots only when the GraphQL page or another visible surface changed.

## Do not commit

- `.venv/`
- `__pycache__/` and `.pytest_cache/`
- `data/verifications.db` (local audit rows)
- Private keys, tokens from a real issuer, or local notes
- Secrets in `data/sample_credentials.json`. The sample generator stores public DIDs and test JWTs only. Do not extend it to write private keys.

## Areas of the code

| Path | Responsibility |
|---|---|
| `core/verifier_service.py` | Credential and presentation checks, audit writes |
| `core/did_crypto.py` | Test key generation and VC-JWT signing |
| `core/database.py` | SQLite schema and queries |
| `grpc_service/` | gRPC API on port 50051 |
| `graphql_service/` | GraphQL API on port 8000 |
| `scripts/` | Demo, sample credentials, and client checks |
| `tests/test_verifier.py` | Unit coverage |

Community expectations are in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security issues privately, as described in [SECURITY.md](SECURITY.md).
