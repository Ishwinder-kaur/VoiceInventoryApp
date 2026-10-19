from pydantic import BaseModel, ConfigDict


class AliasCreate(BaseModel):
    alias: str


class CustomerAliasRead(BaseModel):
    id: int
    customer_id: int
    alias: str

    model_config = ConfigDict(from_attributes=True)


class ProductAliasRead(BaseModel):
    id: int
    product_id: int
    alias: str

    model_config = ConfigDict(from_attributes=True)