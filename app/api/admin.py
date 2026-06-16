from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_product_repository
from app.models.product import ProductConfig, ProductCreate, ProductUpdate
from app.repositories.product_repository import ProductRepository

router = APIRouter(prefix="/admin/products", tags=["admin"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, object]:
    existing = await repo.get(body.product_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product '{body.product_id}' already exists",
        )
    product = ProductConfig(**body.model_dump())
    created = await repo.create(product)
    return {"data": created.model_dump(mode="json")}


@router.get("")
async def list_products(
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, object]:
    products = await repo.list()
    return {"data": [p.model_dump(mode="json") for p in products]}


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, object]:
    product = await repo.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return {"data": product.model_dump(mode="json")}


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdate,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, object]:
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    updated = await repo.update(product_id, data)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return {"data": updated.model_dump(mode="json")}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    repo: ProductRepository = Depends(get_product_repository),
) -> None:
    deleted = await repo.delete(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
