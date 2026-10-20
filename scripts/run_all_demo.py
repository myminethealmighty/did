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
        failed = False

        # 4. Step 4: Run Python gRPC Client Tests
        print("\n[STEP 4] Executing Python gRPC client checks...")
        grpc_test_proc = subprocess.run([PYTHON_EXE, os.path.join(BASE_DIR, "scripts", "test_grpc_client.py")])
        if grpc_test_proc.returncode != 0:
            print("Python gRPC client check failed!")
            failed = True

        # 5. Step 5: Run Go gRPC Client
        print("\n[STEP 5] Executing Go gRPC client checks...")
        go_test_proc = subprocess.run(["go", "run", "./goclient"], cwd=BASE_DIR)
        if go_test_proc.returncode != 0:
            print("Go gRPC client check failed!")
            failed = True

        # 6. Step 6: Run GraphQL Client Queries
        print("\n[STEP 6] Executing GraphQL queries...")
        gql_test_proc = subprocess.run([PYTHON_EXE, os.path.join(BASE_DIR, "scripts", "test_graphql_client.py")])
        if gql_test_proc.returncode != 0:
            print("GraphQL client query failed!")
            failed = True

        print("\n" + "=" * 70)
        if failed:
            print("               DEMO FINISHED WITH FAILURES")
        else:
            print("               ALL DEMO STEPS COMPLETED!")
        print("               - Python gRPC server: localhost:50051")
        print("               - Go gRPC client:     goclient/")
        print("               - GraphQL Web UI:     http://localhost:8000/graphql")
        print("=" * 70)
        if failed:
            sys.exit(1)

    finally:
        print("\nShutting down background service processes...")
        grpc_proc.terminate()
        graphql_proc.terminate()
        grpc_proc.wait()
        graphql_proc.wait()
        print("Clean shutdown complete.")

if __name__ == "__main__":
    main()
