from fastapi import APIRouter, HTTPException, status
from typing import List
from .. import crud
from ..schemas import IngredientIn, IngredientOut

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/", response_model=List[IngredientOut])
def listar_ingredientes():
    return crud.listar_ingredientes()


@router.post("/", response_model=IngredientOut, status_code=status.HTTP_201_CREATED)
def crear_ingrediente(payload: IngredientIn):
    try:
        return crud.crear_ingrediente(payload.nombre)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ingredient_id}", response_model=IngredientOut)
def obtener_ingrediente(ingredient_id: int):
    ingredient = crud.obtener_ingrediente(ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    return ingredient


@router.put("/{ingredient_id}", response_model=IngredientOut)
def actualizar_ingrediente(ingredient_id: int, payload: IngredientIn):
    try:
        ingredient = crud.actualizar_ingrediente(ingredient_id, payload.nombre)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    return ingredient


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ingrediente(ingredient_id: int):
    if not crud.eliminar_ingrediente(ingredient_id):
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
