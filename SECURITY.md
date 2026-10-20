# Security policy

## Supported versions

Security fixes are applied to the current code on the default branch. This project does not publish versioned releases yet.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the maintainers. Do not open a public issue, pull request, or discussion for an unfixed security problem.

Include:

- A short description of the impact
- The file or API involved (`VerifyCredential`, `VerifyPresentation`, or the GraphQL API)
- Steps a maintainer can follow to confirm the issue, using synthetic credentials from `scripts/issue_test_credentials.py` where possible
- Whether the issue exposes audit data, accepts a bad signature, or skips an expiry or audience check

Do not include real private keys, production credentials, or data from a system you do not own.

If this repository is hosted on GitHub, use **Security → Report a vulnerability** so the report stays private. Otherwise contact the maintainers directly.

## What we treat as a security issue

- A credential or presentation accepted when the signature, expiry, audience, or nonce check should fail
- A way to read or change another party's audit records without access to this service
- Leakage of private keys, raw secrets, or full credential material beyond the stored preview
- A crash or resource issue that an unauthenticated caller can trigger with a credential payload

## Response

Maintainers will acknowledge a private report, confirm or reject it, and agree on a fix before any public description. Please give them time to patch before sharing details.
