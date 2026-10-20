import time
from typing import Dict, Any, Tuple, Optional, List
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from openvc import multibase, keys
from openvc.proof.vc_jwt import VcJwtProofSuite

def generate_did_key() -> Tuple[str, str, ed25519.Ed25519PrivateKey, keys.Ed25519SigningKey]:
    """
    Generates an Ed25519 keypair and formats the public key as a W3C did:key.
    Returns: (did_uri, kid_uri, private_key_obj, openvc_signing_key)
    """
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    raw_pub = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    # Multicodec prefix for Ed25519 pubkey: 0xed, 0x01
    multicodec_pub = b'\xed\x01' + raw_pub
    mb = multibase.encode_multibase(multicodec_pub)
    did_uri = f"did:key:{mb}"
    kid_uri = f"{did_uri}#{mb}"
    signing_key = keys.Ed25519SigningKey(priv, kid=kid_uri)
    return did_uri, kid_uri, priv, signing_key

def create_signed_vc(
    issuer_did: str,
    issuer_signing_key: keys.Ed25519SigningKey,
    subject_did: str,
    claims: Dict[str, Any],
    credential_types: Optional[List[str]] = None,
    expires_in_s: Optional[int] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Constructs and signs a W3C Verifiable Credential using VC-JWT.
    Returns: (jwt_token, raw_vc_dict)
    """
    types = ['VerifiableCredential']
    if credential_types:
        for t in credential_types:
            if t not in types:
                types.append(t)
    
    subject_payload = {'id': subject_did}
    subject_payload.update(claims)

    vc_payload = {
        '@context': [
            'https://www.w3.org/ns/credentials/v2'
        ],
        'type': types,
        'issuer': issuer_did,
        'credentialSubject': subject_payload
    }

    suite = VcJwtProofSuite()
    jwt_token = suite.sign(vc_payload, signing_key=issuer_signing_key, expires_in_s=expires_in_s)
    return jwt_token, vc_payload

def create_tampered_vc(valid_jwt: str) -> str:
    """
    Tamper with payload part of the JWT to invalidate its signature.
    """
    parts = valid_jwt.split('.')
    if len(parts) != 3:
        return valid_jwt + '_corrupted'
    # Flip characters in payload or header
    header, payload, sig = parts
    # Alter payload slightly
    corrupted_payload = payload[:-2] + ('AA' if payload[-2:] != 'AA' else 'BB')
    return f"{header}.{corrupted_payload}.{sig}"
