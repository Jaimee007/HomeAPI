from fastapi import APIRouter, HTTPException, status
from typing import List
from .. import crud
from ..schemas import MealIn, MealOut, MealUpdate

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get("/", response_model=List[MealOut])
def listar_comidas():
    """Obtener todas las comidas"""
    return crud.listar_comidas()


@router.post("/", response_model=MealOut, status_code=status.HTTP_201_CREATED)
def crear_comida(payload: MealIn):
    """Crear una nueva comida"""
    return crud.crear_comida(payload.nombre, payload.precio, payload.category_ids)


@router.get("/{meal_id}", response_model=MealOut)
def obtener_comida(meal_id: int):
    """Obtener una comida específica"""
    meal = crud.obtener_comida(meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")
    return meal


@router.put("/{meal_id}", response_model=MealOut)
def actualizar_comida(meal_id: int, payload: MealUpdate):
    """Actualizar una comida"""
    meal = crud.actualizar_comida(meal_id, payload.nombre, payload.precio, payload.category_ids)
    if not meal:
        raise HTTPException(status_code=404, detail="Comida no encontrada")
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_comida(meal_id: int):
    """Eliminar una comida"""
    if not crud.eliminar_comida(meal_id):
        raise HTTPException(status_code=404, detail="Comida no encontrada")


@router.get("/category/{category_id}", response_model=List[MealOut])
def obtener_comidas_por_categoria(category_id: int):
    """Obtener todas las comidas de una categoría específica"""
    meals = crud.obtener_comidas_por_categoria(category_id)
    if not meals:
        raise HTTPException(status_code=404, detail="No hay comidas en esa categoría")
    return meals
