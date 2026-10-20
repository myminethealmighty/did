import json
from datetime import datetime, timezone
import grpc

from generated import did_verifier_pb2, did_verifier_pb2_grpc
from core.verifier_service import VerifierService

class DidVerifierServicer(did_verifier_pb2_grpc.DidVerifierServicer):
    def __init__(self, verifier_service: VerifierService = None):
        self.verifier = verifier_service or VerifierService()

    def VerifyCredential(self, request, context):
        try:
            res = self.verifier.verify_credential(
                credential_data=request.credential_data,
                audience=request.audience if request.audience else None,
                nonce=request.nonce if request.nonce else None,
                require_status=request.require_status_check,
                persist=True
            )

            claims_str = json.dumps(res.get('claims', {}))

            return did_verifier_pb2.VerifyCredentialResponse(
                valid=res.get('valid', False),
                record_id=res.get('id', ''),
                holder_did=res.get('holder_did', ''),
                issuer_did=res.get('issuer_did', ''),
                credential_type=res.get('credential_type', 'VerifiableCredential'),
                format=res.get('format', 'vc-jwt'),
                expired=res.get('expired', False),
                errors=res.get('errors', []),
                claims_json=claims_str,
                verified_at=res.get('verified_at', '')
            )
        except Exception as e:
            return did_verifier_pb2.VerifyCredentialResponse(
                valid=False,
                record_id='',
                holder_did='',
                issuer_did='',
                credential_type='',
                format='',
                expired=False,
                errors=[f'InternalServerError: {str(e)}'],
                claims_json='{}',
                verified_at=datetime.now(timezone.utc).isoformat()
            )

    def VerifyPresentation(self, request, context):
        try:
            res = self.verifier.verify_presentation(
                presentation_data=request.presentation_data,
                audience=request.audience if request.audience else None,
                nonce=request.nonce if request.nonce else None,
                require_status=request.require_status_check,
                persist=True
            )

            return did_verifier_pb2.VerifyPresentationResponse(
                valid=res.get('valid', False),
                record_id=res.get('record_id', ''),
                holder_did=res.get('holder_did', ''),
                credential_types=res.get('credential_types', []),
                errors=res.get('errors', []),
                credentials_count=res.get('credentials_count', 0),
                verified_at=res.get('verified_at', '')
            )
        except Exception as e:
            return did_verifier_pb2.VerifyPresentationResponse(
                valid=False,
                record_id='',
                holder_did='',
                credential_types=[],
                errors=[f'InternalServerError: {str(e)}'],
                credentials_count=0,
                verified_at=datetime.now(timezone.utc).isoformat()
            )

    def HealthCheck(self, request, context):
        return did_verifier_pb2.HealthCheckResponse(
            status="SERVING",
            version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
