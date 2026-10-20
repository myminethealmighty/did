#!/usr/bin/env python3
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO_DIR = os.path.join(BASE_DIR, 'proto')
GENERATED_DIR = os.path.join(BASE_DIR, 'generated')
PROTO_FILE = os.path.join(PROTO_DIR, 'did_verifier.proto')

def compile_proto():
    print(f'Compiling {PROTO_FILE} into {GENERATED_DIR}...')
    cmd = [
        sys.executable, '-m', 'grpc_tools.protoc',
        f'-I{PROTO_DIR}',
        f'--python_out={GENERATED_DIR}',
        f'--grpc_python_out={GENERATED_DIR}',
        PROTO_FILE
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print('Error compiling proto:', res.stderr)
        sys.exit(1)
    print('Compilation successful!')

if __name__ == '__main__':
    compile_proto()
