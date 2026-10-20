import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import openvc
from openvc import VerificationPolicy, VerificationResult
from openvc.errors import OpenvcError

from core.database import insert_verification_record, DEFAULT_DB_PATH

class VerifierService:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    def verify_credential(
        self,
        credential_data: str,
        audience: Optional[str] = None,
        nonce: Optional[str] = None,
        require_status: bool = False,
        persist: bool = True
    ) -> Dict[str, Any]:
        verified_at = datetime.now(timezone.utc).isoformat()
        errors: List[str] = []
        is_valid = False
        is_expired = False
        issuer_did = ""
        holder_did = ""
        credential_type = "VerifiableCredential"
        fmt = "vc-jwt"
        claims = {}

        try:
            policy = VerificationPolicy(
                require_status=require_status,
                audience=audience if audience else None,
                nonce=nonce if nonce else None
            )

            result: VerificationResult = openvc.verify_credential(
                credential_data.strip(),
                policy=policy
            )

            is_valid = True
            is_expired = bool(result.expired)
            issuer_did = result.issuer or ""
            holder_did = result.subject or ""
            fmt = result.format or "vc-jwt"
            claims = result.claims or {}

            # Extract specific credential types from claims or credential payload
            vc_obj = claims.get('vc', {})
            types = vc_obj.get('type', [])
            if isinstance(types, list) and len(types) > 1:
                # Pick the most specific type (not generic 'VerifiableCredential')
                specific_types = [t for t in types if t != 'VerifiableCredential']
                if specific_types:
                    credential_type = specific_types[0]
            elif isinstance(types, str):
                credential_type = types

        except OpenvcError as oe:
            is_valid = False
            errors.append(f"{type(oe).__name__}: {str(oe)}")
        except Exception as e:
            is_valid = False
            errors.append(f"UnexpectedError: {str(e)}")

        record = {
            'holder_did': holder_did,
            'issuer_did': issuer_did,
            'credential_type': credential_type,
            'format': fmt,
            'valid': is_valid,
            'expired': is_expired,
            'errors': errors,
            'claims': claims,
            'raw_credential': credential_data[:500] if len(credential_data) > 500 else credential_data,
            'audience': audience or '',
            'verified_at': verified_at
        }

        record_id = ""
        if persist:
            record_id = insert_verification_record(record, db_path=self.db_path)
            record['id'] = record_id

        return record

    def verify_presentation(
        self,
        presentation_data: str,
        audience: Optional[str] = None,
        nonce: Optional[str] = None,
        require_status: bool = False,
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        Verifies a presentation token or JSON structure.
        """
        verified_at = datetime.now(timezone.utc).isoformat()
        errors: List[str] = []
        is_valid = False
        holder_did = ""
        types_found: List[str] = []

        try:
            # First try parsing if presentation is a standard VP JWT or JSON
            # openvc supports verify_vp_token or verify_credential on inner credentials
            # Let us inspect the token format
            data_clean = presentation_data.strip()
            if data_clean.startswith('{'):
                vp_json = json.loads(data_clean)
                holder_did = vp_json.get('holder', '')
                vcs = vp_json.get('verifiableCredential', [])
                if not isinstance(vcs, list):
                    vcs = [vcs]
                
                sub_results = []
                for vc_item in vcs:
                    vc_str = vc_item if isinstance(vc_item, str) else json.dumps(vc_item)
                    res = self.verify_credential(vc_str, audience=audience, nonce=nonce, require_status=require_status, persist=False)
                    sub_results.append(res)
                    if res.get('credential_type'):
                        types_found.append(res['credential_type'])

                all_valid = all(r['valid'] for r in sub_results) if sub_results else False
                is_valid = all_valid
                if not all_valid:
                    for r in sub_results:
                        errors.extend(r.get('errors', []))
            else:
                # VP Token / JWT: verify with openvc verify_credential
                res = self.verify_credential(data_clean, audience=audience, nonce=nonce, require_status=require_status, persist=False)
                is_valid = res['valid']
                holder_did = res['holder_did']
                if res['credential_type']:
                    types_found.append(res['credential_type'])
                errors = res.get('errors', [])
        except Exception as e:
            is_valid = False
            errors.append(f"PresentationVerificationError: {str(e)}")

        record = {
            'holder_did': holder_did,
            'issuer_did': 'presentation-holder',
            'credential_type': ','.join(types_found) if types_found else 'VerifiablePresentation',
            'format': 'vp-token',
            'valid': is_valid,
            'expired': False,
            'errors': errors,
            'claims': {'credentials_count': len(types_found)},
            'raw_credential': presentation_data[:500],
            'audience': audience or '',
            'verified_at': verified_at
        }

        record_id = ""
        if persist:
            record_id = insert_verification_record(record, db_path=self.db_path)
            record['id'] = record_id

        return {
            'valid': is_valid,
            'record_id': record_id,
            'holder_did': holder_did,
            'credential_types': types_found,
            'errors': errors,
            'credentials_count': len(types_found),
            'verified_at': verified_at
        }
