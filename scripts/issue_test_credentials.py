import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.did_crypto import generate_did_key, create_signed_vc, create_tampered_vc

def generate_samples():
    print('=== Generating Test DIDs and Verifiable Credentials ===')
    
    # 1. Issuer Key & DID
    iss_did, iss_kid, iss_priv, iss_key = generate_did_key()
    print(f'Issuer DID: {iss_did}')
    print(f'Issuer KID: {iss_kid}')

    # 2. Holder Key & DID
    holder_did, holder_kid, holder_priv, holder_key = generate_did_key()
    print(f'Holder DID: {holder_did}')

    # 3. Valid Employment Credential
    valid_emp_jwt, emp_vc = create_signed_vc(
        issuer_did=iss_did,
        issuer_signing_key=iss_key,
        subject_did=holder_did,
        claims={
            'employeeName': 'Alice Johnson',
            'jobTitle': 'Principal Cloud Security Architect',
            'department': 'Enterprise Infrastructure',
            'employmentStatus': 'Active',
            'startDate': '2023-01-15'
        },
        credential_types=['EmploymentCredential'],
        expires_in_s=3600 * 24 * 365
    )
    print('[+] Generated Valid Employment Credential (VC-JWT)')

    # 4. Valid University Degree Credential
    valid_edu_jwt, edu_vc = create_signed_vc(
        issuer_did=iss_did,
        issuer_signing_key=iss_key,
        subject_did=holder_did,
        claims={
            'recipientName': 'Alice Johnson',
            'degree': 'Master of Science',
            'fieldOfStudy': 'Computer Science & Cryptography',
            'graduationYear': 2022,
            'gpa': '3.92'
        },
        credential_types=['UniversityDegreeCredential'],
        expires_in_s=3600 * 24 * 365 * 10
    )
    print('[+] Generated Valid University Degree Credential (VC-JWT)')

    # 5. Tampered Credential
    tampered_jwt = create_tampered_vc(valid_emp_jwt)
    print('[+] Generated Deliberately Tampered Credential')

    # 6. Expired Credential (-3600s)
    expired_jwt, exp_vc = create_signed_vc(
        issuer_did=iss_did,
        issuer_signing_key=iss_key,
        subject_did=holder_did,
        claims={
            'badgeType': 'Temporary Visitor Clearance',
            'building': 'HQ Data Center',
            'escortRequired': False
        },
        credential_types=['TemporaryAccessBadge'],
        expires_in_s=-3600
    )
    print('[+] Generated Deliberately Expired Credential (-1 hour)')

    samples = {
        'issuer': {
            'did': iss_did,
            'kid': iss_kid
        },
        'holder': {
            'did': holder_did,
            'kid': holder_kid
        },
        'credentials': {
            'valid_employment': {
                'jwt': valid_emp_jwt,
                'vc_json': emp_vc
            },
            'valid_degree': {
                'jwt': valid_edu_jwt,
                'vc_json': edu_vc
            },
            'tampered_employment': {
                'jwt': tampered_jwt
            },
            'expired_badge': {
                'jwt': expired_jwt,
                'vc_json': exp_vc
            }
        }
    }

    out_path = os.path.join(BASE_DIR, 'data', 'sample_credentials.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(samples, f, indent=2)

    print(f'Saved all test credentials to {out_path}')
    return samples

if __name__ == '__main__':
    generate_samples()
