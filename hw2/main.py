from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional, Annotated
from uuid import uuid4
from pydantic import NonNegativeInt, PositiveInt, PositiveFloat
from http import HTTPStatus

app = FastAPI()


# Модели данных
class ItemCreate(BaseModel):
    name: str
    price: float
    deleted: bool = False


class ItemPatch(BaseModel):
    name: str | None = None
    price: float | None = None

    model_config = ConfigDict(extra="forbid")


class Item(BaseModel):
    id: int
    name: str
    price: float
    deleted: bool = False

    @staticmethod
    def from_item(item: ItemCreate, id) -> Item:
        return Item(
            id=id,
            name=item.name,
            price=item.price,
            deleted=item.deleted,
        )


class CartItem(BaseModel):
    id: int
    name: str
    quantity: int
    available: bool


class Cart(BaseModel):
    id: int
    items: List[CartItem]
    price: float = 0.0


# Данные в памяти
items: Dict[int, Item] = {}
carts: Dict[int, Cart] = {}


# CRUD для товаров
@app.post("/item", response_model=Item, status_code=201)
def create_item(_item: ItemCreate):
    item = Item.from_item(_item, len(items) + 1)
    items[item.id] = item
    return item


@app.get("/item/{id}", response_model=Item)
def get_item(id: int):
    if id not in items or items[id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[id]


@app.get("/item", response_model=List[Item])
def get_items(
    offset: Annotated[NonNegativeInt, Query()] = 0,
    limit: Annotated[PositiveInt, Query()] = 10,
    min_price: Annotated[PositiveFloat, Query()] = None,
    max_price: Annotated[PositiveFloat, Query()] = None,
    show_deleted: Annotated[bool, Query()] = False,
):
    filtered_items = [
        item for item in items.values() if (show_deleted or not item.deleted)
    ]
    if min_price:
        filtered_items = [item for item in filtered_items if item.price >= min_price]
    if max_price:
        filtered_items = [item for item in filtered_items if item.price <= max_price]
    return filtered_items[offset : offset + limit]


@app.put("/item/{id}", response_model=Item)
def update_item(id: int, item: ItemCreate):
    if id not in items or items[id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    items[id] = Item.from_item(item, id)
    return items[id]


@app.patch("/item/{id}", response_model=Item)
def patch_item(id: int, item_data: ItemPatch):
    if id not in items or items[id].deleted:
        raise HTTPException(
            status_code=HTTPStatus.NOT_MODIFIED, detail="Item not found"
        )
    item = items[id]

    updated_item = item.model_copy(update=item_data.model_dump())
    items[id] = updated_item
    return updated_item


@app.delete("/item/{id}", response_model=Item)
def delete_item(id: int):
    print(id)
    if id not in items.keys():
        raise HTTPException(status_code=404, detail="Item not found")
    items[id].deleted = True
    return items[id]


# CRUD для корзин
@app.post("/cart", status_code=201)
def create_cart(response: Response):
    cart_id = len(carts) + 1
    carts[cart_id] = Cart(id=cart_id, items=[])
    response.headers["location"] = f"/cart/{cart_id}"
    return {"id": cart_id}


@app.get("/cart/{id}", response_model=Cart)
def get_cart(id: int):
    if id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    return carts[id]


@app.get("/cart", response_model=List[Cart])
def get_carts(
    offset: Annotated[NonNegativeInt, Query()] = 0,
    limit: Annotated[PositiveInt, Query()] = 10,
    min_price: Annotated[PositiveFloat, Query()] = None,
    max_price: Annotated[PositiveFloat, Query()] = None,
    min_quantity: Annotated[NonNegativeInt, Query()] = None,
    max_quantity: Annotated[NonNegativeInt, Query()] = None,
):
    answer = []
    curr = 0
    for id, data in carts.items():
        if offset <= curr < offset + limit:

            if min_price != None:
                if data.price < min_price:
                    continue

            if max_price != None:
                if data.price > max_price:
                    continue

            quantity = 0
            for one in data.items:
                quantity += one.quantity

            if min_quantity != None:
                if quantity <= min_quantity:
                    continue

            if max_quantity != None:
                if quantity >= max_quantity:
                    continue
            answer.append(data)
    return answer


@app.post("/cart/{cart_id}/add/{item_id}", response_model=Cart)
def add_item_to_cart(cart_id: int, item_id: int):
    if cart_id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    if item_id not in items or items[item_id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    cart = carts[cart_id]
    item = items[item_id]

    for cart_item in cart.items:
        if cart_item.id == item.id:
            cart_item.quantity += 1
            cart.price += item.price
            return cart

    cart.items.append(
        CartItem(id=item.id, name=item.name, quantity=1, available=not item.deleted)
    )
    cart.price += item.price
    return cart
