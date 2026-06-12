import redis
from fastapi import FastAPI, HTTPException
from models import ItemPayload

app = FastAPI()

redis_client = redis.StrictRedis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

# Agregar producto
@app.post("/items/{item_name}/{quantity}")
def add_item(item_name: str, quantity: int):

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0."
        )

    item_id_str = redis_client.hget(
        "item_name_to_id",
        item_name
    )

    if item_id_str is not None:

        item_id = int(item_id_str)

        redis_client.hincrby(
            f"item_id:{item_id}",
            "quantity",
            quantity
        )

    else:

        item_id = redis_client.incr("item_ids")

        redis_client.hset(
            f"item_id:{item_id}",
            mapping={
                "item_id": item_id,
                "item_name": item_name,
                "quantity": quantity,
            }
        )

        redis_client.hset(
            "item_name_to_id",
            item_name,
            item_id
        )

    return {
        "item": ItemPayload(
            item_id=item_id,
            item_name=item_name,
            quantity=quantity
        )
    }

# Buscar por ID
@app.get("/items/{item_id}")
def list_item(item_id: int):

    if not redis_client.hexists(
        f"item_id:{item_id}",
        "item_id"
    ):
        raise HTTPException(
            status_code=404,
            detail="Item not found."
        )

    return {
        "item":
        redis_client.hgetall(
            f"item_id:{item_id}"
        )
    }

# Listar todos
@app.get("/items")
def list_items():

    items = []

    stored_items = redis_client.hgetall(
        "item_name_to_id"
    )

    for name, id_str in stored_items.items():

        item_id = int(id_str)

        item_name = redis_client.hget(
            f"item_id:{item_id}",
            "item_name"
        )

        quantity = redis_client.hget(
            f"item_id:{item_id}",
            "quantity"
        )

        items.append({
            "item_id": item_id,
            "item_name": item_name,
            "quantity": int(quantity)
        })

    return {"items": items}

# Eliminar producto
@app.delete("/items/{item_id}")
def delete_item(item_id: int):

    if not redis_client.hexists(
        f"item_id:{item_id}",
        "item_id"
    ):
        raise HTTPException(
            status_code=404,
            detail="Item not found."
        )

    item_name = redis_client.hget(
        f"item_id:{item_id}",
        "item_name"
    )

    redis_client.hdel(
        "item_name_to_id",
        item_name
    )

    redis_client.delete(
        f"item_id:{item_id}"
    )

    return {
        "result": "Item deleted."
    }