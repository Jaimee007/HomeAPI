from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== CATEGORÍAS ====================
class CategoryIn(BaseModel):
    nombre: str = Field(..., min_length=1)


class CategoryOut(BaseModel):
    id: int
    nombre: str


# ==================== COMIDAS ====================
class MealIn(BaseModel):
    nombre: str = Field(..., min_length=1)
    precio: float = Field(..., gt=0)
    category_ids: List[int] = Field(default_factory=list)


class MealOut(BaseModel):
    id: int
    nombre: str
    precio: float
    categories: List[CategoryOut]


class MealUpdate(BaseModel):
    nombre: Optional[str] = None
    precio: Optional[float] = None
    category_ids: Optional[List[int]] = None


# ==================== MENÚ DIARIO ====================
class DailyMenuIn(BaseModel):
    mes: int = Field(..., ge=1, le=12)
    año: int = Field(..., ge=2000)
    dia: int = Field(..., ge=1, le=31)
    meal_lunch_id: Optional[int] = None
    meal_dinner_id: Optional[int] = None


class DailyMenuOut(BaseModel):
    id: int
    mes: int
    año: int
    dia: int
    meal_lunch_id: Optional[int] = None
    meal_lunch: Optional[MealOut]
    meal_dinner_id: Optional[int] = None
    meal_dinner: Optional[MealOut]
    created_at: datetime
    updated_at: datetime


class DailyMenuUpdate(BaseModel):
    meal_lunch_id: Optional[int] = None
    meal_dinner_id: Optional[int] = None
