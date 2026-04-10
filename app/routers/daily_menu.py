from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from .. import crud
from ..schemas import DailyMenuIn, DailyMenuOut, DailyMenuUpdate

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/", response_model=List[DailyMenuOut])
def listar_menu(mes: Optional[int] = Query(None), año: Optional[int] = Query(None)):
    """
    Obtener el menú del mes especificado.
    Si no se especifica mes/año, obtiene todos los menús
    """
    return crud.listar_menu(mes, año)


@router.post("/", response_model=DailyMenuOut, status_code=status.HTTP_201_CREATED)
def crear_dia_menu(payload: DailyMenuIn):
    """Crear una asignación de menú para un día específico"""
    try:
        return crud.crear_dia_menu(payload.mes, payload.año, payload.dia, payload.meal_lunch_id, payload.meal_dinner_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{daily_menu_id}", response_model=DailyMenuOut)
def obtener_dia_menu(daily_menu_id: int):
    """Obtener el menú de un día específico"""
    menu = crud.obtener_dia_menu(daily_menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menú no encontrado")
    return menu


@router.put("/{daily_menu_id}", response_model=DailyMenuOut)
def actualizar_dia_menu(daily_menu_id: int, payload: DailyMenuUpdate):
    """Actualizar las comidas asignadas a un día"""
    menu = crud.actualizar_dia_menu(daily_menu_id, payload.meal_lunch_id, payload.meal_dinner_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menú no encontrado")
    return menu


@router.delete("/{daily_menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_dia_menu(daily_menu_id: int):
    """Eliminar la asignación de menú de un día"""
    if not crud.eliminar_dia_menu(daily_menu_id):
        raise HTTPException(status_code=404, detail="Menú no encontrado")
