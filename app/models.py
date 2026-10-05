"""Pydantic models shared between the bot, the web API and the frontend."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Category = Literal["coffee", "desserts", "breakfast"]

CATEGORY_TITLES: dict[str, str] = {
    "coffee": "Кофе",
    "desserts": "Десерты",
    "breakfast": "Завтраки",
}


class Product(BaseModel):
    """A single catalogue item returned by GET /api/products."""

    id: int
    title: str
    description: str
    price: float
    category: Category
    image_url: str


class OrderItem(BaseModel):
    """One line of an order created inside the Mini App."""

    product_id: int
    title: str
    price: float = Field(gt=0)
    quantity: int = Field(ge=1, le=99)


class OrderCreate(BaseModel):
    """Payload accepted by POST /api/order."""

    items: list[OrderItem] = Field(min_length=1, max_length=50)
    address: str = Field(min_length=1, max_length=200)
    comment: str = Field(default="", max_length=500)
    # Sent by the frontend in standalone browser mode (no Telegram initData).
    guest_name: str = Field(default="", max_length=100)

    @field_validator("address")
    @classmethod
    def address_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Адрес или номер столика не может быть пустым")
        return value


class OrderItemOut(BaseModel):
    """Server-side order line (prices taken from the database)."""

    product_id: int
    title: str
    price: float
    quantity: int