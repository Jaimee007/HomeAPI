import os
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from .. import crud
from python_bring_api.bring import Bring

router = APIRouter(prefix="/bring", tags=["bring"])


@router.post("/add-recipe-ingredients")
def add_recipe_ingredients(payload: Dict[str, Any]):
    email = os.getenv('BRING_EMAIL')
    password = os.getenv('BRING_PASSWORD')
    default_list_uuid = os.getenv('BRING_LIST_UUID')
    list_uuid = payload.get('list_uuid') or default_list_uuid
    meal_ids = payload.get('meal_ids')

    if not email or not password:
        raise HTTPException(status_code=400, detail='Bring credentials are not configured')
    if not list_uuid:
        raise HTTPException(status_code=400, detail='Bring list UUID is not configured')
    if not meal_ids or not isinstance(meal_ids, list):
        raise HTTPException(status_code=400, detail='meal_ids must be a non-empty list of meal IDs')

    bring = Bring(email, password)
    try:
        bring.login()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Bring login failed: {e}')

    added = []
    errors = []
    for meal_id in meal_ids:
        meal = crud.obtener_comida(meal_id)
        if not meal:
            errors.append(f'Meal {meal_id} not found')
            continue
        ingredients = meal.get('ingredients', [])
        for ingredient in ingredients:
            try:
                bring.saveItem(list_uuid, ingredient['nombre'], ingredient.get('spec'))
                added.append({'meal_id': meal_id, 'ingredient_id': ingredient['ingredient_id'], 'name': ingredient['nombre']})
            except Exception as e:
                errors.append(f"Failed to add {ingredient['nombre']} from meal {meal_id}: {e}")

    return {'added': added, 'errors': errors}
