from fastapi import APIRouter
from . import crud
from .schemas import Product, ProductCreate
router = APIRouter(tags=['Products'])

@router.get('/')
async def get_products(session):
    return await crud.get_product(session=session)


@router.post('/')
async def create_product(session, product_in: ProductCreate ):
    return await crud.create_product(session=session, product_in=product_in)




@router.get('/{product_id}/')
async def get_product(product_id: int , session):
    return await crud.get_product(session=session, product_id=product_id)





