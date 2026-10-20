import os
import sys
import pytest
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import init_db, get_verification_records, get_verification_stats
from core.did_crypto import generate_did_key, create_signed_vc, create_tampered_vc
from core.verifier_service import VerifierService
from generated import did_verifier_pb2
from grpc_service.servicer import DidVerifierServicer
from graphql_service.schema import schema

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()

def test_did_key_generation():
    did_uri, kid_uri, priv, signing_key = generate_did_key()
    assert did_uri.startswith("did:key:z6Mk"), f"Unexpected DID prefix: {did_uri}"
    assert kid_uri.startswith(did_uri), "KID must reference the DID"
    assert signing_key is not None

def test_vc_signing_and_verification():
    iss_did, iss_kid, iss_priv, iss_key = generate_did_key()
    sub_did, sub_kid, sub_priv, sub_key = generate_did_key()

    jwt_token, vc_data = create_signed_vc(
        issuer_did=iss_did,
        issuer_signing_key=iss_key,
        subject_did=sub_did,
        claims={"role": "Engineer", "clearance": "TopSecret"},
        credential_types=["SecurityClearanceCredential"]
    )

    verifier = VerifierService()
    res = verifier.verify_credential(jwt_token)
    assert res["valid"] is True
    assert res["issuer_did"] == iss_did
    assert res["holder_did"] == sub_did
    assert res["credential_type"] == "SecurityClearanceCredential"
    assert len(res["errors"]) == 0

def test_tampered_vc_rejection():
    iss_did, iss_kid, iss_priv, iss_key = generate_did_key()
    sub_did, sub_kid, sub_priv, sub_key = generate_did_key()

    jwt_token, _ = create_signed_vc(
        issuer_did=iss_did,
        issuer_signing_key=iss_key,
        subject_did=sub_did,
        claims={"amount": 1000}
    )

    tampered_jwt = create_tampered_vc(jwt_token)
    verifier = VerifierService()
    res = verifier.verify_credential(tampered_jwt)
    assert res["valid"] is False
    assert len(res["errors"]) > 0

def test_grpc_servicer_methods():
    iss_did, iss_kid, iss_priv, iss_key = generate_did_key()
    sub_did, sub_kid, sub_priv, sub_key = generate_did_key()

    jwt_token, _ = create_signed_vc(
        issuer_did=iss_did,
        issuer_signing_key=iss_key,
        subject_did=sub_did,
        claims={"membership": "Gold"}
    )

    servicer = DidVerifierServicer()
    
    # Test HealthCheck
    health_res = servicer.HealthCheck(did_verifier_pb2.HealthCheckRequest(), None)
    assert health_res.status == "SERVING"

    # Test VerifyCredential
    req = did_verifier_pb2.VerifyCredentialRequest(credential_data=jwt_token)
    grpc_res = servicer.VerifyCredential(req, None)
    assert grpc_res.valid is True
    assert grpc_res.holder_did == sub_did
    assert grpc_res.issuer_did == iss_did

def test_graphql_schema_queries():
    query = """
    query TestVerificationQuery {
      verifications(limit: 5) {
        id
        valid
        credentialType
      }
      stats {
        totalVerifications
        validCount
      }
    }
    """
    res = schema.execute_sync(query)
    assert res.errors is None
    assert "verifications" in res.data
    assert "stats" in res.data
    assert res.data["stats"]["totalVerifications"] >= 0
