from pydantic import BaseModel, Field
from typing import Dict, List, Optional
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


class MealStepIn(BaseModel):
    texto: str = Field(..., min_length=1)


class MealStepOut(BaseModel):
    orden: int
    texto: str


# ==================== COMIDAS ====================
class MealIn(BaseModel):
    nombre: str = Field(..., min_length=1)
    category_ids: List[int] = Field(default_factory=list)
    ingredient_entries: List[MealIngredientIn] = Field(default_factory=list)
    steps: List[MealStepIn] = Field(default_factory=list)


class MealOut(BaseModel):
    id: int
    nombre: str
    categories: List[CategoryOut]
    ingredients: List[MealIngredientOut]
    steps: List[MealStepOut]


class MealUpdate(BaseModel):
    nombre: Optional[str] = None
    category_ids: Optional[List[int]] = None
    ingredient_entries: Optional[List[MealIngredientIn]] = None
    steps: Optional[List[MealStepIn]] = None


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


# ==================== BRING ====================
class BringAddIngredientsIn(BaseModel):
    meal_ids: List[int] = Field(..., min_length=1)
    list_uuid: Optional[str] = None
    bring_email: Optional[str] = None
    bring_password: Optional[str] = None


class BringAddedItemOut(BaseModel):
    meal_id: int
    ingredient_id: int
    name: str
    spec: Optional[str] = None


class BringAddIngredientsOut(BaseModel):
    added: List[BringAddedItemOut]
    skipped_duplicates: List[BringAddedItemOut]
    errors: List[str]


# ==================== GOOGLE CALENDAR ====================
class CalendarFailureOut(BaseModel):
    mes: int
    año: int
    dia: int
    slot: str
    attempts: int
    last_error: Optional[str] = None


class CalendarStatusOut(BaseModel):
    enabled: bool
    calendar_id: Optional[str] = None
    pending: int
    published_events: int
    recent_failures: List[CalendarFailureOut]


class CalendarSyncOut(BaseModel):
    queued: int
    results: Dict[str, int]
    pending: int
