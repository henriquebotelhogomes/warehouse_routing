from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference


def setup_scalar_docs(app: FastAPI) -> None:
    """
    Configura a documentação OpenAPI viva via Scalar.
    Substitui expressamente o Swagger UI tradicional por uma interface
    moderna estilo Stripe/Vercel com playground de testes integrado.
    """

    @app.get("/docs", include_in_schema=False)
    async def scalar_html():
        return get_scalar_api_reference(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} — API Documentation (Scalar)",
            servers=[{"url": "/", "description": "Servidor Atual"}],
        )
