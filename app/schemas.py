from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== CATEGORÍAS ====================
class CategoryIn(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None


class CategoryOut(CategoryIn):
    id: int
    created_at: datetime


# ==================== COMIDAS ====================
class MealIn(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    category_ids: List[int] = Field(default_factory=list)


class MealOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    categories: List[CategoryOut]
    created_at: datetime
    updated_at: datetime


class MealUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
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
    meal_lunch: Optional[MealOut]
    meal_dinner: Optional[MealOut]
    created_at: datetime
    updated_at: datetime


class DailyMenuUpdate(BaseModel):
    meal_lunch_id: Optional[int] = None
    meal_dinner_id: Optional[int] = None
