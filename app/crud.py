from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from . import models, schemas


def list_books(db: Session) -> list[models.Book]:
    return list(db.scalars(select(models.Book).order_by(models.Book.id)))


def get_book(db: Session, book_id: int) -> models.Book:
    book = db.get(models.Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


def create_book(db: Session, data: schemas.BookCreate) -> models.Book:
    book = models.Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def list_orders(db: Session) -> list[models.Order]:
    stmt = (
        select(models.Order)
        .options(joinedload(models.Order.book))
        .order_by(models.Order.id.desc())
    )
    return list(db.scalars(stmt))


def get_order(db: Session, order_id: int) -> models.Order:
    order = db.get(models.Order, order_id, options=[joinedload(models.Order.book)])
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


def create_order(db: Session, data: schemas.OrderCreate) -> models.Order:
    # SELECT ... FOR UPDATE: блокируем строку книги, чтобы параллельные заказы
    # не увели остаток на складе в минус
    book = db.get(models.Book, data.book_id, with_for_update=True)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    if book.stock < data.quantity:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"На складе только {book.stock} шт.")
    book.stock -= data.quantity
    order = models.Order(book_id=book.id, quantity=data.quantity)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
