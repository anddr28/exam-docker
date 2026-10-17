from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)  # price > 0
    stock: int = Field(ge=0)


class BookOut(BookCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderCreate(BaseModel):
    book_id: int = Field(gt=0)
    quantity: int = Field(gt=0)  # quantity > 0


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_id: int
    quantity: int
    created_at: datetime
    book: BookOut
