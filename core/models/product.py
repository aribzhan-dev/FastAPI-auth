from .base import Base
from sqlalchemy.orm import Mapped

class Product(Base):
    __tablename__ = "products"

    name: Mapped[str]
    decs: Mapped[str]
    price: Mapped[float]