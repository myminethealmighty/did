# Decentralized Identity (DID) Verifier

A Python service that checks W3C Verifiable Credentials and records every result. Callers submit a credential over gRPC. Dashboards and other clients read the audit log over GraphQL.

- **gRPC verifier** on port `50051`. Checks `did:key` signatures and VC-JWT credentials with `openvc-core`.
- **GraphQL API** on port `8000`. Lists, filters, and summarizes verification records. Built with FastAPI and Strawberry.
- **SQLite audit log** at `data/verifications.db`. Stores issuer, holder, validity, claims, and errors.

## What it verifies

A credential in this project is a signed VC-JWT. The issuer is a `did:key` derived from an Ed25519 public key. The verifier checks the signature, reads the claims, and writes a pass or fail row. It does not issue credentials for real users and it does not hold issuer private keys.

The sample generator creates four tokens you can submit:

| Sample | Expected result |
|---|---|
| Valid employment credential | `valid: true`, type `EmploymentCredential` |
| Valid university degree credential | `valid: true`, type `UniversityDegreeCredential` |
| Tampered employment credential | `valid: false`, with errors |
| Expired visitor badge | rejected or marked expired |

## Requirements

- Python 3.11 or newer
- `pip`

## Run it locally

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`.

Generate sample credentials, start both servers, run the gRPC and GraphQL clients, then shut the servers down:

```bash
python scripts/run_all_demo.py
```

Run the unit tests without starting servers:

```bash
pytest tests/test_verifier.py -v
```

### Keep the services running

Use two terminals, each with the virtual environment activated, from the project root.

Terminal 1, gRPC verifier:

```bash
python grpc_service/server.py
```

Listens on `0.0.0.0:50051`.

Terminal 2, GraphQL API:

```bash
python graphql_service/server.py
```

- Home: http://localhost:8000/
- GraphiQL: http://localhost:8000/graphql
- Health: http://localhost:8000/health

Terminal 3, client checks against those servers:

```bash
python scripts/issue_test_credentials.py
python scripts/test_grpc_client.py
python scripts/test_graphql_client.py
```

`scripts/issue_test_credentials.py` writes fresh keys and tokens to `data/sample_credentials.json`. Submit the `jwt` strings from that file. The unsigned `vc_json` objects are the payload before signing.

Example audit query for the GraphiQL playground:

```graphql
query GetAuditLogs {
  verifications(limit: 10) {
    id
    holderDid
    issuerDid
    credentialType
    valid
    expired
    errors
    claimsJson
    verifiedAt
  }
}
```

To check one token through GraphQL, pass a `jwt` value as the `credentialData` variable:

```graphql
mutation CheckOne($token: String!) {
  verifyCredential(credentialData: $token) {
    id
    valid
    expired
    credentialType
    holderDid
    issuerDid
    errors
    claimsJson
  }
}
```

### Optional: regenerate gRPC stubs

Stubs are already in `generated/`. Rebuild them after changing `proto/did_verifier.proto`:

```bash
python scripts/compile_proto.py
```

## Project layout

```
core/                 verification engine, did:key helpers, SQLite access
grpc_service/         gRPC server and servicer
graphql_service/      GraphQL schema and HTTP server
proto/                protobuf contract
generated/            compiled gRPC stubs
scripts/              sample issuer, demo runner, and client checks
tests/                pytest suite
data/                 sample credentials and the local audit database
```

## gRPC methods

Defined in `proto/did_verifier.proto`:

- `HealthCheck`
- `VerifyCredential`
- `VerifyPresentation`

`VerifyCredential` takes `credential_data` plus optional `audience`, `nonce`, and `require_status_check`.

## GraphQL operations

- `verifications(holderDid, issuerDid, valid, limit)` lists audit rows
- `verification(id)` loads one row
- `stats` returns totals
- `verifyCredential(credentialData, audience)` checks a token and stores the result

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, branches, and pull requests. Community expectations are in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report security issues through [SECURITY.md](SECURITY.md).

## License

This project is licensed under the [MIT License](LICENSE).
# did
