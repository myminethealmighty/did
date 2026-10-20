import os
import sys
import logging
from concurrent import futures
import grpc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from generated import did_verifier_pb2_grpc
from grpc_service.servicer import DidVerifierServicer
from core.database import init_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('grpc_server')

def create_grpc_server(host: str = '0.0.0.0', port: int = 50051) -> grpc.Server:
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = DidVerifierServicer()
    did_verifier_pb2_grpc.add_DidVerifierServicer_to_server(servicer, server)
    server.add_insecure_port(f'{host}:{port}')
    return server

def serve(host: str = '0.0.0.0', port: int = 50051):
    server = create_grpc_server(host, port)
    server.start()
    logger.info(f'gRPC DID Verifier service started on {host}:{port}')
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info('Stopping gRPC server...')
        server.stop(grace=2)

if __name__ == '__main__':
    port = int(os.environ.get('GRPC_PORT', 50051))
    serve(port=port)
