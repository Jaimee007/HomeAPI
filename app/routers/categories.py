from fastapi import APIRouter, HTTPException, status
from typing import List
from .. import crud
from ..schemas import CategoryIn, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[CategoryOut])
def listar_categorias():
    """Obtener todas las categorías"""
    return crud.listar_categorias()


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(payload: CategoryIn):
    """Crear una nueva categoría"""
    try:
        return crud.crear_categoria(payload.nombre)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{category_id}", response_model=CategoryOut)
def obtener_categoria(category_id: int):
    """Obtener una categoría específica"""
    cat = crud.obtener_categoria(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


@router.put("/{category_id}", response_model=CategoryOut)
def actualizar_categoria(category_id: int, payload: CategoryIn):
    """Actualizar una categoría"""
    cat = crud.actualizar_categoria(category_id, payload.nombre)
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(category_id: int):
    """Eliminar una categoría"""
    if not crud.eliminar_categoria(category_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
