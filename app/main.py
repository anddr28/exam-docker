from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import crud, schemas
from .database import Base, SessionLocal, engine, get_db
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте создаём таблицы и наполняем каталог (вместо миграций Alembic)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Интернет-магазин книг", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")


# ======================= HTML-страницы (5 шт.) =======================

@app.get("/", response_class=HTMLResponse)
def catalog_page(request: Request, db: Session = Depends(get_db)):
    """Страница 1. Каталог книг."""
    return templates.TemplateResponse(request, "catalog.html", {"books": crud.list_books(db)})


@app.get("/books/{book_id}", response_class=HTMLResponse)
def book_page(book_id: int, request: Request, db: Session = Depends(get_db)):
    """Страница 2. Карточка книги."""
    return templates.TemplateResponse(request, "book.html", {"book": crud.get_book(db, book_id)})

@app.get("/books/{book_id}/reviews", response_class=HTMLResponse)
def reviews_page(book_id: int, request: Request, db: Session = Depends(get_db)):
    """Страница 6. Отзывы о книге."""
    return templates.TemplateResponse(
        request, "reviews.html", {"book": crud.get_book(db, book_id), "form": {}, "error": None}
    )


@app.post("/books/{book_id}/reviews", response_class=HTMLResponse)
def reviews_submit(
    book_id: int,
    request: Request,
    author: str = Form(""),
    rating: int = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        data = schemas.ReviewCreate(author=author, rating=rating, text=text)
        crud.create_review(db, book_id, data)
    except ValidationError:
        error = "Заполните имя и текст отзыва, оценка — от 1 до 5"
    else:
        return RedirectResponse(f"/books/{book_id}/reviews", status_code=303)
    return templates.TemplateResponse(
        request,
        "reviews.html",
        {"book": crud.get_book(db, book_id),
         "form": {"author": author, "rating": rating, "text": text},
         "error": error},
        status_code=400,
    )


@app.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request, db: Session = Depends(get_db)):
    """Страница 3. Список заказов."""
    return templates.TemplateResponse(request, "orders.html", {"orders": crud.list_orders(db)})


@app.get("/orders/new", response_class=HTMLResponse)
def new_order_page(request: Request, book_id: int | None = None, db: Session = Depends(get_db)):
    """Страница 5. Оформление заказа (форма)."""
    return templates.TemplateResponse(
        request,
        "order_new.html",
        {"books": crud.list_books(db), "selected": book_id, "quantity": 1, "error": None},
    )


@app.post("/orders/new", response_class=HTMLResponse)
def new_order_submit(
    request: Request,
    book_id: int = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db),
):
    """Обработка формы: валидация Pydantic -> запись в БД -> редирект (Post/Redirect/Get)."""
    try:
        data = schemas.OrderCreate(book_id=book_id, quantity=quantity)
        order = crud.create_order(db, data)
    except ValidationError as e:
        error = "Количество должно быть больше 0" if any(
            err["loc"] == ("quantity",) for err in e.errors()
        ) else "Некорректные данные"
    except HTTPException as e:
        error = e.detail
    else:
        return RedirectResponse(f"/orders/{order.id}", status_code=303)
    return templates.TemplateResponse(
        request,
        "order_new.html",
        {"books": crud.list_books(db), "selected": book_id, "quantity": quantity, "error": error},
        status_code=400,
    )


@app.get("/orders/{order_id}", response_class=HTMLResponse)
def order_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Страница 4. Страница заказа."""
    return templates.TemplateResponse(request, "order.html", {"order": crud.get_order(db, order_id)})


# ============================ JSON API ============================

@app.get("/api/books", response_model=list[schemas.BookOut], tags=["books"])
def api_list_books(db: Session = Depends(get_db)):
    return crud.list_books(db)


@app.get("/api/books/{book_id}", response_model=schemas.BookOut, tags=["books"])
def api_get_book(book_id: int, db: Session = Depends(get_db)):
    return crud.get_book(db, book_id)


@app.post("/api/books", response_model=schemas.BookOut, status_code=201, tags=["books"])
def api_create_book(data: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.create_book(db, data)


@app.get("/api/orders", response_model=list[schemas.OrderOut], tags=["orders"])
def api_list_orders(db: Session = Depends(get_db)):
    return crud.list_orders(db)


@app.get("/api/orders/{order_id}", response_model=schemas.OrderOut, tags=["orders"])
def api_get_order(order_id: int, db: Session = Depends(get_db)):
    return crud.get_order(db, order_id)


@app.post("/api/orders", response_model=schemas.OrderOut, status_code=201, tags=["orders"])
def api_create_order(data: schemas.OrderCreate, db: Session = Depends(get_db)):
    order = crud.create_order(db, data)
    return crud.get_order(db, order.id)


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok"}
