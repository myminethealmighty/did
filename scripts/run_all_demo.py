import os
import sys
import time
import subprocess
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PYTHON_EXE = sys.executable

def main():
    print("=" * 70)
    print("   DECENTRALIZED IDENTITY (DID) VERIFIER: gRPC + GraphQL DEMO")
    print("=" * 70)

    # 1. Step 1: Issue test credentials
    print("\n[STEP 1] Generating Test DIDs and W3C Verifiable Credentials...")
    issue_proc = subprocess.run([PYTHON_EXE, os.path.join(BASE_DIR, "scripts", "issue_test_credentials.py")])
    if issue_proc.returncode != 0:
        print("Failed to issue test credentials!")
        return

    # 2. Step 2: Start gRPC Server
    print("\n[STEP 2] Starting gRPC Verification Service (port 50051)...")
    grpc_proc = subprocess.Popen([PYTHON_EXE, os.path.join(BASE_DIR, "grpc_service", "server.py")])
    time.sleep(2)

    # 3. Step 3: Start GraphQL Server
    print("\n[STEP 3] Starting GraphQL Query API (port 8000)...")
    graphql_proc = subprocess.Popen([PYTHON_EXE, os.path.join(BASE_DIR, "graphql_service", "server.py")])
    time.sleep(2.5)

    try:
        # 4. Step 4: Run gRPC Client Tests
        print("\n[STEP 4] Executing gRPC Client Tests against DidVerifier service...")
        grpc_test_proc = subprocess.run([PYTHON_EXE, os.path.join(BASE_DIR, "scripts", "test_grpc_client.py")])
        if grpc_test_proc.returncode != 0:
            print("gRPC client test failed!")

        # 5. Step 5: Run GraphQL Client Queries
        print("\n[STEP 5] Executing GraphQL Queries & Aggregations...")
        gql_test_proc = subprocess.run([PYTHON_EXE, os.path.join(BASE_DIR, "scripts", "test_graphql_client.py")])
        if gql_test_proc.returncode != 0:
            print("GraphQL client query failed!")

        print("\n" + "=" * 70)
        print("               ALL DEMO STEPS COMPLETED!")
        print("               - gRPC Server:    localhost:50051")
        print("               - GraphQL Web UI: http://localhost:8000/graphql")
        print("=" * 70)

    finally:
        print("\nShutting down background service processes...")
        grpc_proc.terminate()
        graphql_proc.terminate()
        grpc_proc.wait()
        graphql_proc.wait()
        print("Clean shutdown complete.")

if __name__ == "__main__":
    main()
