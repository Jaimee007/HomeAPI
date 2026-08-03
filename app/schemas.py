from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== CATEGORÍAS ====================
class CategoryIn(BaseModel):
    nombre: str = Field(..., min_length=1)


class CategoryOut(BaseModel):
    id: int
    nombre: str


# ==================== INGREDIENTES ====================
class IngredientIn(BaseModel):
    nombre: str = Field(..., min_length=1)


class IngredientOut(BaseModel):
    id: int
    nombre: str


class MealIngredientIn(BaseModel):
    ingredient_id: int
    spec: Optional[str] = None


class MealIngredientOut(BaseModel):
    ingredient_id: int
    nombre: str
    spec: Optional[str] = None


# ==================== COMIDAS ====================
class MealIn(BaseModel):
    nombre: str = Field(..., min_length=1)
    category_ids: List[int] = Field(default_factory=list)
    ingredient_entries: List[MealIngredientIn] = Field(default_factory=list)


class MealOut(BaseModel):
    id: int
    nombre: str
    categories: List[CategoryOut]
    ingredients: List[MealIngredientOut]


class MealUpdate(BaseModel):
    nombre: Optional[str] = None
    category_ids: Optional[List[int]] = None
    ingredient_entries: Optional[List[MealIngredientIn]] = None


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
