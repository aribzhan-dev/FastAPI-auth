from typing import Annotated
from fastapi import Path, APIRouter



router = APIRouter(prefix="/items", tags=["items"])





@router.get("/")
def list_items():
    return [
        "item1",
        "item2",
    ]

@router.get("/{item_id}/")
def get_item_id(item_id: Annotated[int, Path(ge=0, lt=1_000_000)]):
    return {
        "item": {
            "id": item_id,
        },
    }