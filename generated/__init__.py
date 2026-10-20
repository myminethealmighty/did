import os
import sys

# Ensure generated directory is in sys.path so pb2_grpc can find pb2
_dir = os.path.dirname(__file__)
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from . import did_verifier_pb2
from . import did_verifier_pb2_grpc

__all__ = ['did_verifier_pb2', 'did_verifier_pb2_grpc']
