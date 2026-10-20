import json
from typing import List, Optional
import strawberry

from core.database import (
    get_verification_records,
    get_verification_by_id,
    get_verification_stats
)
from core.verifier_service import VerifierService

@strawberry.type
class VerificationRecord:
    id: strawberry.ID
    holder_did: str
    issuer_did: str
    credential_type: str
    format: str
    valid: bool
    expired: bool
    errors: List[str]
    claims_json: str
    audience: str
    verified_at: str

    @strawberry.field
    def raw_credential_preview(self) -> str:
        # Avoid dumping huge payloads
        return f"Token({self.format})"

@strawberry.type
class VerificationStats:
    total_verifications: int
    valid_count: int
    invalid_count: int
    last_verified_at: Optional[str]

@strawberry.type
class Query:
    @strawberry.field(description="Retrieve a list of verification records with optional filters")
    def verifications(
        self,
        holder_did: Optional[str] = None,
        issuer_did: Optional[str] = None,
        valid: Optional[bool] = None,
        limit: int = 50
    ) -> List[VerificationRecord]:
        rows = get_verification_records(
            holder_did=holder_did,
            issuer_did=issuer_did,
            valid=valid,
            limit=limit
        )
        records = []
        for r in rows:
            records.append(VerificationRecord(
                id=strawberry.ID(str(r['id'])),
                holder_did=r.get('holder_did') or '',
                issuer_did=r.get('issuer_did') or '',
                credential_type=r.get('credential_type') or 'VerifiableCredential',
                format=r.get('format') or 'vc-jwt',
                valid=bool(r.get('valid')),
                expired=bool(r.get('expired')),
                errors=r.get('errors') or [],
                claims_json=json.dumps(r.get('claims', {})),
                audience=r.get('audience') or '',
                verified_at=r.get('verified_at') or ''
            ))
        return records

    @strawberry.field(description="Retrieve a single verification record by unique ID")
    def verification(self, id: strawberry.ID) -> Optional[VerificationRecord]:
        r = get_verification_by_id(str(id))
        if not r:
            return None
        return VerificationRecord(
            id=strawberry.ID(str(r['id'])),
            holder_did=r.get('holder_did') or '',
            issuer_did=r.get('issuer_did') or '',
            credential_type=r.get('credential_type') or 'VerifiableCredential',
            format=r.get('format') or 'vc-jwt',
            valid=bool(r.get('valid')),
            expired=bool(r.get('expired')),
            errors=r.get('errors') or [],
            claims_json=json.dumps(r.get('claims', {})),
            audience=r.get('audience') or '',
            verified_at=r.get('verified_at') or ''
        )

    @strawberry.field(description="Get aggregate verification statistics")
    def stats(self) -> VerificationStats:
        s = get_verification_stats()
        return VerificationStats(
            total_verifications=s['total_verifications'],
            valid_count=s['valid_count'],
            invalid_count=s['invalid_count'],
            last_verified_at=s['last_verified_at']
        )

@strawberry.type
class Mutation:
    @strawberry.mutation(description="Submit a VC for verification directly via GraphQL (optional convenience method)")
    def verify_credential(
        self,
        credential_data: str,
        audience: Optional[str] = None
    ) -> VerificationRecord:
        verifier = VerifierService()
        res = verifier.verify_credential(
            credential_data=credential_data,
            audience=audience,
            persist=True
        )
        return VerificationRecord(
            id=strawberry.ID(str(res.get('id', ''))),
            holder_did=res.get('holder_did', ''),
            issuer_did=res.get('issuer_did', ''),
            credential_type=res.get('credential_type', 'VerifiableCredential'),
            format=res.get('format', 'vc-jwt'),
            valid=bool(res.get('valid')),
            expired=bool(res.get('expired')),
            errors=res.get('errors', []),
            claims_json=json.dumps(res.get('claims', {})),
            audience=res.get('audience', ''),
            verified_at=res.get('verified_at', '')
        )

schema = strawberry.Schema(query=Query, mutation=Mutation)
