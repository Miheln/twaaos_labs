from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Catalog produse", version="1.0.0")


class Produs(BaseModel):
    id: int
    nume: str
    pret: float
    stoc: int = 0


products: list[Produs] = []


@app.get("/")
def health_check():
    return {
        "aplicatie": "Catalog produse",
        "status": "pornit",
        "documentatie": "/docs",
    }


def get_product_position(product_id: int) -> int:
    for position, item in enumerate(products):
        if item.id == product_id:
            return position

    raise HTTPException(
        status_code=404,
        detail=f"Produsul cu ID-ul {product_id} nu a fost gasit.",
    )


@app.get("/produse")
def list_products(stoc_minim: int | None = None):
    if stoc_minim is None:
        return products

    return [item for item in products if item.stoc < stoc_minim]


@app.get("/produse/{produs_id}")
def read_product(produs_id: int):
    position = get_product_position(produs_id)
    return products[position]


@app.post("/produse", status_code=201)
def create_product(product: Produs):
    products.append(product)
    return product


@app.delete("/produse/{produs_id}")
def remove_product(produs_id: int):
    position = get_product_position(produs_id)
    deleted_product = products.pop(position)
    return {
        "mesaj": "Produs sters din catalog.",
        "produs": deleted_product,
    }


@app.put("/produse/{produs_id}")
def replace_product(produs_id: int, product: Produs):
    position = get_product_position(produs_id)
    products[position] = product
    return product
