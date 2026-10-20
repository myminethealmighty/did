import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter
import uvicorn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import init_db
from graphql_service.schema import schema

def create_app() -> FastAPI:
    init_db()
    app = FastAPI(
        title="Decentralized Identity (DID) Verifier - GraphQL API",
        description="GraphQL Query & Inspection Layer for DID Credentials & Presentations",
        version="1.0.0"
    )

    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "graphql-query-api"}

    @app.get("/", response_class=HTMLResponse)
    def index():
        return """
        <html>
            <head><title>DID Verifier GraphQL API</title></head>
            <body style="font-family: system-ui, -apple-system, sans-serif; padding: 2rem; max-width: 800px; margin: auto; line-height: 1.6;">
                <h2>Decentralized Identity (DID) Verifier Query API</h2>
                <p>Welcome to the GraphQL interface for DID credential verification history and inspection.</p>
                <p><a href="/graphql" style="display: inline-block; background: #2563eb; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-weight: 600;">Open GraphQL Playground (/graphql)</a></p>
                <div style="background: #f1f5f9; padding: 16px; border-radius: 8px; margin-top: 20px;">
                    <h3>Example GraphQL Query:</h3>
                    <pre style="background: #1e293b; color: #f8fafc; padding: 14px; border-radius: 6px; overflow-x: auto;">
query GetVerifications {
  verifications(limit: 5) {
    id
    holderDid
    issuerDid
    credentialType
    valid
    verifiedAt
    errors
    claimsJson
  }
  stats {
    totalVerifications
    validCount
    invalidCount
  }
}
                    </pre>
                </div>
            </body>
        </html>
        """

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('GRAPHQL_PORT', 8000))
    uvicorn.run('graphql_service.server:app', host='0.0.0.0', port=port, reload=False)
