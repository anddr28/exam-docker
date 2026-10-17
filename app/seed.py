from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Book

BOOKS = [
    ("Мастер и Маргарита — М. Булгаков", 650, 10),
    ("Преступление и наказание — Ф. Достоевский", 520, 7),
    ("1984 — Дж. Оруэлл", 480, 12),
    ("Чистый код — Р. Мартин", 1290, 5),
    ("Грокаем алгоритмы — А. Бхаргава", 990, 3),
]


def seed(db: Session) -> None:
    """Заполняет каталог демо-книгами, если таблица пустая."""
    if db.scalar(select(Book.id).limit(1)) is not None:
        return
    db.add_all(Book(title=t, price=p, stock=s) for t, p, s in BOOKS)
    db.commit()
