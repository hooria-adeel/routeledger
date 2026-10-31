from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class Strict(BaseModel):
    """Base for all forms: spaces at the start and end of text are removed."""
    model_config = ConfigDict(str_strip_whitespace=True)


# ----------------------------- login / employees -----------------------------
class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1, max_length=128)


class EmployeeOut(BaseModel):
    employee_id: int
    full_name: str
    email: str
    role: str
    can_edit: bool        # these three let the pages show or hide buttons;
    can_delete: bool      # the backend still checks every request itself
    can_manage: bool


class EmployeeCreate(Strict):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=150, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=1, max_length=128)
    role: str = Field(max_length=20)          # Viewer, Editor, Manager or Admin


class EmployeeUpdate(Strict):
    role: str | None = Field(None, max_length=20)
    is_active: bool | None = None
    new_password: str | None = Field(None, max_length=128)


# ---------------------------------------------------------------------
# Add / edit forms.
# "version" = the version number the person was looking at when they
# opened the record (needed for safe editing).
# ---------------------------------------------------------------------
class ProductCreate(Strict):
    category_id: int
    name: str = Field(min_length=2, max_length=150)
    pack_size: int = Field(gt=0, le=100000)
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class ProductUpdate(Strict):
    category_id: int | None = None
    name: str | None = Field(None, min_length=2, max_length=150)
    pack_size: int | None = Field(None, gt=0, le=100000)
    unit_price: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    version: int = Field(ge=1)


class RetailerCreate(Strict):
    name: str = Field(min_length=2, max_length=120)


class RetailerUpdate(Strict):
    name: str | None = Field(None, min_length=2, max_length=120)
    version: int = Field(ge=1)


class BranchCreate(Strict):
    retailer_id: int
    area_id: int
    branch_name: str = Field(min_length=2, max_length=80)


class BranchUpdate(Strict):
    area_id: int | None = None
    branch_name: str | None = Field(None, min_length=2, max_length=80)
    version: int = Field(ge=1)


class AreaCreate(Strict):
    name: str = Field(min_length=2, max_length=80)
    district: str | None = Field(None, max_length=80)


class AreaUpdate(Strict):
    name: str | None = Field(None, min_length=2, max_length=80)
    district: str | None = Field(None, max_length=80)
    version: int = Field(ge=1)


class OrderItemIn(Strict):
    product_id: int
    cartons: int = Field(gt=0, le=100000)
    # leave empty to use the product's normal carton price
    carton_price: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)


class OrderCreate(Strict):
    retailer_id: int
    branch_id: int | None = None
    order_date: date
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)


class OrderUpdate(Strict):
    retailer_id: int | None = None
    branch_id: int | None = None
    order_date: date | None = None
    version: int = Field(ge=1)


class OrderItemUpdate(Strict):
    cartons: int | None = Field(None, gt=0, le=100000)
    carton_price: Decimal | None = Field(None, ge=0, max_digits=14, decimal_places=2)
    version: int = Field(ge=1)
