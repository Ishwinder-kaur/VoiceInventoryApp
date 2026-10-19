from sqlalchemy import text

from app.db import engine


with engine.connect() as conn:
    rows = conn.execute(
        text(
            "SELECT id, name, quantity_on_hand "
            "FROM products ORDER BY id"
        )
    ).fetchall()

    print("Product count:", len(rows))
    print("Products:", rows)