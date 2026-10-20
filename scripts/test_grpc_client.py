import os
import sys
import json
import grpc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from generated import did_verifier_pb2, did_verifier_pb2_grpc

def run_grpc_tests(server_target='localhost:50051'):
    print("=" * 60)
    print(f"Connecting to gRPC DidVerifier Service at {server_target}...")
    print("=" * 60)

    channel = grpc.insecure_channel(server_target)
    stub = did_verifier_pb2_grpc.DidVerifierStub(channel)

    # 1. Health check
    try:
        health = stub.HealthCheck(did_verifier_pb2.HealthCheckRequest())
        print(f"[✓] HealthCheck: status={health.status}, version={health.version}, ts={health.timestamp}")
    except Exception as e:
        print(f"[✗] HealthCheck failed: {e}")
        return False

    # Load test credentials
    data_path = os.path.join(BASE_DIR, 'data', 'sample_credentials.json')
    with open(data_path, 'r') as f:
        samples = json.load(f)

    creds = samples['credentials']

    # Test Case 1: Valid Employment Credential
    print("\n--- Test 1: Verify Valid Employment Credential ---")
    emp_req = did_verifier_pb2.VerifyCredentialRequest(
        credential_data=creds['valid_employment']['jwt']
    )
    res1 = stub.VerifyCredential(emp_req)
    print(f"Valid: {res1.valid}")
    print(f"Type: {res1.credential_type}")
    print(f"Issuer: {res1.issuer_did}")
    print(f"Holder: {res1.holder_did}")
    print(f"Record ID: {res1.record_id}")
    assert res1.valid is True, "Expected valid=True"
    print("[✓] Test 1 PASSED")

    # Test Case 2: Valid Degree Credential
    print("\n--- Test 2: Verify Valid University Degree Credential ---")
    edu_req = did_verifier_pb2.VerifyCredentialRequest(
        credential_data=creds['valid_degree']['jwt']
    )
    res2 = stub.VerifyCredential(edu_req)
    print(f"Valid: {res2.valid}")
    print(f"Type: {res2.credential_type}")
    print(f"Record ID: {res2.record_id}")
    assert res2.valid is True, "Expected valid=True"
    print("[✓] Test 2 PASSED")

    # Test Case 3: Tampered Credential (Negative Test)
    print("\n--- Test 3: Verify Deliberately Tampered Credential ---")
    tampered_req = did_verifier_pb2.VerifyCredentialRequest(
        credential_data=creds['tampered_employment']['jwt']
    )
    res3 = stub.VerifyCredential(tampered_req)
    print(f"Valid: {res3.valid}")
    print(f"Errors: {res3.errors}")
    assert res3.valid is False, "Expected valid=False for tampered token"
    assert len(res3.errors) > 0, "Expected error messages for tampered token"
    print("[✓] Test 3 PASSED (Correctly rejected tampered VC)")

    # Test Case 4: Expired Credential (Negative Test)
    print("\n--- Test 4: Verify Expired Credential ---")
    expired_req = did_verifier_pb2.VerifyCredentialRequest(
        credential_data=creds['expired_badge']['jwt']
    )
    res4 = stub.VerifyCredential(expired_req)
    print(f"Valid: {res4.valid}")
    print(f"Expired: {res4.expired}")
    print(f"Errors: {res4.errors}")
    assert res4.valid is False or res4.expired is True, "Expected expired or invalid token"
    print("[✓] Test 4 PASSED (Correctly flagged expired VC)")

    print("\n" + "=" * 60)
    print("ALL gRPC VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    run_grpc_tests()
