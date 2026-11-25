import os
import re
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, HTTPException
from typing import Dict
from .. import crud
from ..schemas import BringAddIngredientsIn, BringAddIngredientsOut
from python_bring_api.bring import Bring

router = APIRouter(prefix="/bring", tags=["bring"])
FIXED_BRING_LIST_UUID = 'a5492637-1aff-45e0-b1e3-1c0a1e48bde9'


def _normalize_spec(spec: str | None) -> str | None:
    if spec is None:
        return None
    cleaned = spec.strip()
    return cleaned if cleaned else None


def _merge_specs(existing: str | None, new_spec: str | None) -> str | None:
    existing = _normalize_spec(existing)
    new_spec = _normalize_spec(new_spec)
    if existing and new_spec:
        existing_parts = [part.strip() for part in existing.split('/') if part.strip()]
        new_parts = [part.strip() for part in new_spec.split('/') if part.strip()]
        for part in new_parts:
            if part not in existing_parts:
                existing_parts.append(part)
        return ' / '.join(existing_parts)
    return existing or new_spec


def _is_numeric_spec(value: str) -> bool:
    return bool(re.fullmatch(r'\d+(?:[\.,]\d+)?', value.strip()))


def _to_decimal(value: str) -> Decimal:
    return Decimal(value.strip().replace(',', '.'))


def _format_decimal(value: Decimal) -> str:
    normalized = value.normalize()
    # Avoid scientific notation when possible.
    as_text = format(normalized, 'f')
    return as_text.rstrip('0').rstrip('.') if '.' in as_text else as_text


def _split_quantity_and_unit(value: str) -> tuple[Decimal, str] | None:
    match = re.fullmatch(r'\s*(\d+(?:[\.,]\d+)?)\s*([^\d\s].*)?\s*', value)
    if not match:
        return None
    amount_raw = match.group(1)
    unit_raw = (match.group(2) or '').strip().lower()
    try:
        return _to_decimal(amount_raw), unit_raw
    except (InvalidOperation, ValueError):
        return None


def _merge_bring_specs(existing: str | None, new_spec: str | None) -> str | None:
    existing = _normalize_spec(existing)
    new_spec = _normalize_spec(new_spec)

    if existing and new_spec:
        existing_parts = _split_quantity_and_unit(existing)
        new_parts = _split_quantity_and_unit(new_spec)
        if existing_parts and new_parts and existing_parts[1] == new_parts[1]:
            total = existing_parts[0] + new_parts[0]
            amount = _format_decimal(total)
            unit = existing_parts[1]
            return f'{amount} {unit}'.strip()

        if _is_numeric_spec(existing) and _is_numeric_spec(new_spec):
            try:
                total = _to_decimal(existing) + _to_decimal(new_spec)
                return _format_decimal(total)
            except (InvalidOperation, ValueError):
                pass
        return f'{existing}, {new_spec}'

    return existing or new_spec


@router.post("/add-recipe-ingredients", response_model=BringAddIngredientsOut)
def add_recipe_ingredients(payload: BringAddIngredientsIn):
    email = payload.bring_email or os.getenv('BRING_EMAIL')
    password = payload.bring_password or os.getenv('BRING_PASSWORD')
    list_uuid = FIXED_BRING_LIST_UUID
    meal_ids = payload.meal_ids

    if not email or not password:
        raise HTTPException(status_code=400, detail='Bring credentials are not configured')
    bring = Bring(email, password)
    try:
        bring.login()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Bring login failed: {e}')

    added = []
    skipped_duplicates = []
    errors = []
    aggregated: Dict[int, Dict[str, int | str | None]] = {}

    existing_items_by_name: Dict[str, Dict[str, str | None]] = {}
    try:
        existing_items_payload = bring.getItems(list_uuid)
        if isinstance(existing_items_payload, dict):
            purchase_items = existing_items_payload.get('purchase', []) or []
            for existing_item in purchase_items:
                if not isinstance(existing_item, dict):
                    continue
                item_name = _normalize_spec(existing_item.get('name'))
                if not item_name:
                    continue
                existing_spec_value = existing_item.get('specification')
                if existing_spec_value is None:
                    existing_spec_value = existing_item.get('spec')
                existing_items_by_name[item_name.lower()] = {
                    'name': item_name,
                    'spec': _normalize_spec(existing_spec_value)
                }
    except Exception as e:
        errors.append(f'Could not load existing Bring items: {e}')

    for meal_id in meal_ids:
        meal = crud.obtener_comida(meal_id)
        if not meal:
            errors.append(f'Meal {meal_id} not found')
            continue
        ingredients = meal.get('ingredients', [])
        for ingredient in ingredients:
            ingredient_id = ingredient['ingredient_id']
            current = aggregated.get(ingredient_id)
            if current is None:
                aggregated[ingredient_id] = {
                    'meal_id': meal_id,
                    'ingredient_id': ingredient_id,
                    'name': ingredient['nombre'],
                    'spec': _normalize_spec(ingredient.get('spec'))
                }
                continue

            current_spec = current.get('spec') if isinstance(current.get('spec'), str) else None
            merged_spec = _merge_specs(current_spec, ingredient.get('spec'))
            current['spec'] = merged_spec
            skipped_duplicates.append({
                'meal_id': meal_id,
                'ingredient_id': ingredient_id,
                'name': ingredient['nombre'],
                'spec': _normalize_spec(ingredient.get('spec'))
            })

    for item in aggregated.values():
        meal_id = int(item['meal_id'])
        ingredient_id = int(item['ingredient_id'])
        name = str(item['name'])
        spec = item.get('spec') if isinstance(item.get('spec'), str) else None
        try:
            existing_item = existing_items_by_name.get(name.lower())
            if existing_item:
                existing_spec = existing_item.get('spec') if isinstance(existing_item.get('spec'), str) else None
                merged_spec = _merge_bring_specs(existing_spec, spec)
                existing_name = existing_item.get('name') if isinstance(existing_item.get('name'), str) else name
                bring.updateItem(list_uuid, existing_name, merged_spec or '')
                existing_items_by_name[name.lower()] = {'name': existing_name, 'spec': merged_spec}
                added.append({'meal_id': meal_id, 'ingredient_id': ingredient_id, 'name': existing_name, 'spec': merged_spec})
                continue

            bring.saveItem(list_uuid, name, spec or '')
            existing_items_by_name[name.lower()] = {'name': name, 'spec': _normalize_spec(spec)}
            added.append({'meal_id': meal_id, 'ingredient_id': ingredient_id, 'name': name, 'spec': _normalize_spec(spec)})
        except Exception as e:
            errors.append(f'Failed to add {name}: {e}')

    return {'added': added, 'skipped_duplicates': skipped_duplicates, 'errors': errors}
