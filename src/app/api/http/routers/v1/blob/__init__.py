from litestar import Router

from src.app.api.http.routers.v1.blob.blob_api import BlobController

blob_router = Router(path="/blobs", route_handlers=[BlobController], tags=["Blobs"])

__all__ = ["blob_router"]
