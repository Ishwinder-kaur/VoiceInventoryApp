import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_alias import CustomerAlias
from app.models.product import Product
from app.models.product_alias import ProductAlias


def normalize_name(value: str) -> str:
    normalized = value.lower().strip()

    # Remove punctuation.
    normalized = re.sub(
        r"[^\w\s]",
        "",
        normalized,
    )

    # Collapse repeated spaces.
    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    words = normalized.split()

    # Handle common spoken plurals:
    # "ceramic cup sets" -> "ceramic cup set"
    if words:
        last_word = words[-1]

        if (
            len(last_word) > 3
            and last_word.endswith("s")
            and not last_word.endswith("ss")
        ):
            words[-1] = last_word[:-1]

    return " ".join(words)


def resolve_customer(
    db: Session,
    business_id: int,
    name: str,
) -> Customer | None:
    search_name = normalize_name(name)

    customers = list(
        db.scalars(
            select(Customer).where(
                Customer.business_id == business_id
            )
        ).all()
    )

    for customer in customers:
        if normalize_name(customer.name) == search_name:
            return customer

    aliases = list(
        db.scalars(
            select(CustomerAlias)
            .join(
                Customer,
                Customer.id == CustomerAlias.customer_id,
            )
            .where(
                Customer.business_id == business_id
            )
        ).all()
    )

    for alias in aliases:
        if normalize_name(alias.alias) == search_name:
            return db.get(
                Customer,
                alias.customer_id,
            )

    return None


def resolve_product(
    db: Session,
    business_id: int,
    name: str,
) -> Product | None:
    search_name = normalize_name(name)

    products = list(
        db.scalars(
            select(Product).where(
                Product.business_id == business_id,
                Product.active.is_(True),
            )
        ).all()
    )

    for product in products:
        if normalize_name(product.name) == search_name:
            return product

    aliases = list(
        db.scalars(
            select(ProductAlias)
            .join(
                Product,
                Product.id == ProductAlias.product_id,
            )
            .where(
                Product.business_id == business_id,
                Product.active.is_(True),
            )
        ).all()
    )

    for alias in aliases:
        if normalize_name(alias.alias) == search_name:
            return db.get(
                Product,
                alias.product_id,
            )

    return None


def resolve_product_from_phrase(
    db: Session,
    business_id: int,
    phrase: str,
) -> Product | None:
    """
    Resolve a product from a longer clarification phrase.

    Example:
        "I mean the Ceramic Cup Set"
        -> Ceramic Cup Set

    Returns a product only when exactly one product matches.
    """
    normalized_phrase = normalize_name(phrase)

    products = list(
        db.scalars(
            select(Product).where(
                Product.business_id == business_id,
                Product.active.is_(True),
            )
        ).all()
    )

    aliases = list(
        db.scalars(
            select(ProductAlias)
            .join(
                Product,
                Product.id == ProductAlias.product_id,
            )
            .where(
                Product.business_id == business_id,
                Product.active.is_(True),
            )
        ).all()
    )

    matching_product_ids: set[int] = set()

    for product in products:
        candidate = normalize_name(product.name)

        if (
            normalized_phrase == candidate
            or candidate in normalized_phrase
        ):
            matching_product_ids.add(product.id)

    for alias in aliases:
        candidate = normalize_name(alias.alias)

        if (
            normalized_phrase == candidate
            or candidate in normalized_phrase
        ):
            matching_product_ids.add(alias.product_id)

    if len(matching_product_ids) != 1:
        return None

    product_id = next(iter(matching_product_ids))

    return db.get(Product, product_id)


def resolve_customer_from_phrase(
    db: Session,
    business_id: int,
    phrase: str,
) -> Customer | None:
    """
    Resolve a customer from a longer clarification phrase.

    Example:
        "I mean ABC Customer"
        -> ABC Customer

    Returns a customer only when exactly one customer matches.
    """
    normalized_phrase = normalize_name(phrase)

    customers = list(
        db.scalars(
            select(Customer).where(
                Customer.business_id == business_id
            )
        ).all()
    )

    aliases = list(
        db.scalars(
            select(CustomerAlias)
            .join(
                Customer,
                Customer.id == CustomerAlias.customer_id,
            )
            .where(
                Customer.business_id == business_id
            )
        ).all()
    )

    matching_customer_ids: set[int] = set()

    for customer in customers:
        candidate = normalize_name(customer.name)

        if (
            normalized_phrase == candidate
            or candidate in normalized_phrase
        ):
            matching_customer_ids.add(customer.id)

    for alias in aliases:
        candidate = normalize_name(alias.alias)

        if (
            normalized_phrase == candidate
            or candidate in normalized_phrase
        ):
            matching_customer_ids.add(alias.customer_id)

    if len(matching_customer_ids) != 1:
        return None

    customer_id = next(iter(matching_customer_ids))

    return db.get(Customer, customer_id)