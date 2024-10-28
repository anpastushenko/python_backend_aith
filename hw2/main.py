from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from uuid import uuid4

app = FastAPI()

# Модели данных
class Item(BaseModel):
    id: int
    name: str
    price: float
    deleted: bool = False

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
def create_item(item: Item):
    item.id = len(items) + 1
    items[item.id] = item
    return item

@app.get("/item/{id}", response_model=Item)
def get_item(id: int):
    if id not in items or items[id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[id]

@app.get("/item", response_model=List[Item])
def get_items(offset: int = 0, limit: int = 10, min_price: Optional[float] = None, max_price: Optional[float] = None, show_deleted: bool = False):
    filtered_items = [item for item in items.values() if (show_deleted or not item.deleted)]
    if min_price:
        filtered_items = [item for item in filtered_items if item.price >= min_price]
    if max_price:
        filtered_items = [item for item in filtered_items if item.price <= max_price]
    return filtered_items[offset:offset + limit]

@app.put("/item/{id}", response_model=Item)
def update_item(id: int, item: Item):
    if id not in items or items[id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    items[id] = item
    return item

@app.patch("/item/{id}", response_model=Item)
def patch_item(id: int, item_data: dict):
    if id not in items or items[id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    item = items[id]
    updated_item = item.copy(update=item_data)
    items[id] = updated_item
    return updated_item

@app.delete("/item/{id}", response_model=Item)
def delete_item(id: int):
    if id not in items or items[id].deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    items[id].deleted = True
    return items[id]

# CRUD для корзин
@app.post("/cart", status_code=201)
def create_cart():
    cart_id = len(carts) + 1
    carts[cart_id] = Cart(id=cart_id, items=[])
    return {"id": cart_id}

@app.get("/cart/{id}", response_model=Cart)
def get_cart(id: int):
    if id not in carts:
        raise HTTPException(status_code=404, detail="Cart not found")
    return carts[id]

@app.get("/cart", response_model=List[Cart])
def get_carts(offset: int = 0, limit: int = 10, min_price: Optional[float] = None, max_price: Optional[float] = None):
    filtered_carts = list(carts.values())
    if min_price:
        filtered_carts = [cart for cart in filtered_carts if cart.price >= min_price]
    if max_price:
        filtered_carts = [cart for cart in filtered_carts if cart.price <= max_price]
    return filtered_carts[offset:offset + limit]

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

    cart.items.append(CartItem(id=item.id, name=item.name, quantity=1, available=not item.deleted))
    cart.price += item.price
    return cart

