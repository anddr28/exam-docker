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


class ReviewCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)  # "   " не пройдёт как текст
    author: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=1, le=5)  # оценка от 1 до 5
    text: str = Field(min_length=1, max_length=2000)