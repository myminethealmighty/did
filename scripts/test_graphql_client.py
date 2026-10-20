import os
import sys
import json
import requests

def run_graphql_tests(endpoint="http://localhost:8000/graphql"):
    print("=" * 60)
    print(f"Querying GraphQL API at {endpoint}...")
    print("=" * 60)

    # 1. Query all verifications
    q1 = """
    query GetAllVerifications {
      verifications(limit: 10) {
        id
        holderDid
        issuerDid
        credentialType
        valid
        expired
        verifiedAt
        errors
      }
    }
    """
    res = requests.post(endpoint, json={"query": q1})
    assert res.status_code == 200, f"HTTP error: {res.text}"
    data = res.json()
    assert "errors" not in data, f"GraphQL error: {data.get('errors')}"
    records = data["data"]["verifications"]
    print(f"\n[✓] Query 1 (List All): Retrieved {len(records)} records:")
    for r in records[:4]:
        rec_id = r["id"][:8] if r.get("id") else "unknown"
        print(f"    - [{rec_id}...] Type: {r.get('credentialType')}, Valid: {r.get('valid')}, Errors: {r.get('errors')}")

    # 2. Query Statistics
    q2 = """
    query GetStats {
      stats {
        totalVerifications
        validCount
        invalidCount
        lastVerifiedAt
      }
    }
    """
    res2 = requests.post(endpoint, json={"query": q2})
    stats = res2.json()["data"]["stats"]
    print("\n[✓] Query 2 (Aggregates & Stats):")
    print(f"    - Total Processed: {stats.get('totalVerifications')}")
    print(f"    - Valid: {stats.get('validCount')}")
    print(f"    - Invalid/Rejected: {stats.get('invalidCount')}")
    print(f"    - Latest Verification: {stats.get('lastVerifiedAt')}")

    # 3. Query single verification by ID
    if records:
        target_id = records[0]["id"]
        q3 = """
        query GetSingle($id: ID!) {
          verification(id: $id) {
            id
            holderDid
            issuerDid
            credentialType
            valid
            claimsJson
            verifiedAt
          }
        }
        """
        res3 = requests.post(endpoint, json={"query": q3, "variables": {"id": target_id}})
        single = res3.json()["data"]["verification"]
        print(f"\n[✓] Query 3 (Single Item Lookup by ID): ID = {target_id}")
        print(f"    - Holder DID: {single.get('holderDid')}")
        print(f"    - Issuer DID: {single.get('issuerDid')}")
        print(f"    - Credential Type: {single.get('credentialType')}")
        print(f"    - Claims Payload: {single.get('claimsJson')}")

    # 4. Filter by valid=true
    q4 = """
    query FilterValidOnly {
      verifications(valid: true, limit: 5) {
        id
        credentialType
        valid
      }
    }
    """
    res4 = requests.post(endpoint, json={"query": q4})
    valid_recs = res4.json()["data"]["verifications"]
    print(f"\n[✓] Query 4 (Field Filtering valid=true): Returned {len(valid_recs)} records")
    assert all(r["valid"] is True for r in valid_recs), "Filter query returned invalid records"

    print("\n" + "=" * 60)
    print("ALL GraphQL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_graphql_tests()
