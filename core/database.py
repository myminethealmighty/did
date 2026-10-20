import os
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data',
    'verifications.db'
)

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_records (
                id TEXT PRIMARY KEY,
                holder_did TEXT,
                issuer_did TEXT,
                credential_type TEXT,
                format TEXT,
                valid INTEGER NOT NULL,
                expired INTEGER NOT NULL DEFAULT 0,
                errors TEXT,
                claims_json TEXT,
                raw_credential TEXT,
                audience TEXT,
                verified_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_holder ON verification_records(holder_did);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_issuer ON verification_records(issuer_did);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verified_at ON verification_records(verified_at DESC);
        """)
        conn.commit()

def insert_verification_record(record: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> str:
    record_id = record.get('id') or str(uuid.uuid4())
    verified_at = record.get('verified_at') or datetime.now(timezone.utc).isoformat()
    
    errors_val = record.get('errors', [])
    if isinstance(errors_val, list):
        errors_str = json.dumps(errors_val)
    else:
        errors_str = str(errors_val)

    claims_val = record.get('claims', {})
    if isinstance(claims_val, dict):
        claims_str = json.dumps(claims_val)
    else:
        claims_str = str(claims_val)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO verification_records (
                id, holder_did, issuer_did, credential_type, format,
                valid, expired, errors, claims_json, raw_credential,
                audience, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            record.get('holder_did', ''),
            record.get('issuer_did', ''),
            record.get('credential_type', 'VerifiableCredential'),
            record.get('format', 'vc-jwt'),
            1 if record.get('valid') else 0,
            1 if record.get('expired') else 0,
            errors_str,
            claims_str,
            record.get('raw_credential', ''),
            record.get('audience', ''),
            verified_at
        ))
        conn.commit()
    return record_id

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d['valid'] = bool(d['valid'])
    d['expired'] = bool(d['expired'])
    try:
        d['errors'] = json.loads(d['errors']) if d['errors'] else []
    except Exception:
        d['errors'] = [d['errors']] if d['errors'] else []
    try:
        d['claims'] = json.loads(d['claims_json']) if d['claims_json'] else {}
    except Exception:
        d['claims'] = {}
    return d

def get_verification_by_id(record_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM verification_records WHERE id = ?
        """, (record_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return row_to_dict(row)

def get_verification_records(
    holder_did: Optional[str] = None,
    issuer_did: Optional[str] = None,
    valid: Optional[bool] = None,
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    query = "SELECT * FROM verification_records WHERE 1=1"
    params = []

    if holder_did:
        query += " AND holder_did = ?"
        params.append(holder_did)
    if issuer_did:
        query += " AND issuer_did = ?"
        params.append(issuer_did)
    if valid is not None:
        query += " AND valid = ?"
        params.append(1 if valid else 0)

    query += " ORDER BY verified_at DESC LIMIT ?"
    params.append(max(1, min(limit, 200)))

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [row_to_dict(r) for r in rows]

def get_verification_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(valid) FROM verification_records")
        total_row = cursor.fetchone()
        total = total_row[0] or 0
        valid_count = total_row[1] or 0
        invalid_count = total - valid_count
        cursor.execute("SELECT verified_at FROM verification_records ORDER BY verified_at DESC LIMIT 1")
        last_row = cursor.fetchone()
        last_verified_at = last_row[0] if last_row else None
        return {
            'total_verifications': total,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'last_verified_at': last_verified_at
        }
