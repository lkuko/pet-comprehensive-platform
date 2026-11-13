"""商城数据访问层。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mall import Order, Product, ProductCategory


class MallRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_category(self, category_id: int) -> ProductCategory | None:
        return self.db.get(ProductCategory, category_id)

    def get_product(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id)

    def get_product_for_update(self, product_id: int) -> Product | None:
        return self.db.get(Product, product_id, with_for_update=True)

    def get_order(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id)

    def get_order_for_update(self, order_id: int) -> Order | None:
        return self.db.get(Order, order_id, with_for_update=True)

    def count_products_for_category(self, category_id: int) -> int:
        stmt = select(Product.id).where(Product.category_id == category_id)
        return len(self.db.execute(stmt).all())
