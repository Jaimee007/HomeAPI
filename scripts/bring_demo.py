import argparse
import asyncio
import getpass
import os
import sys

import aiohttp
from python_bring_api.bring import Bring


async def show_purchase_items(bring, list_uuid, list_name):
    items = await bring.getItemsAsync(list_uuid)
    if not isinstance(items, dict):
        print(f'Ítems en "{list_name}": {len(items)}')
        for item in items:
            print(f" - {item}")
        return

    purchase = items.get('purchase', []) or []
    print(f'Ítems de compra en "{list_name}": {len(purchase)}')
    for item in purchase:
        specification = item.get('specification')
        if specification is None:
            specification = item.get('spec')
        print(f" - {item.get('name')} (spec={specification})")


async def add_purchase_item(bring, list_uuid, item_name, specification=None):
    print(f'Añadiendo ítem "{item_name}" a Bring!...')
    await bring.saveItemAsync(list_uuid, item_name, specification)
    print('Ítem añadido con éxito.')


async def main():
    parser = argparse.ArgumentParser(description='Prueba Bring! API para tu lista de compras.')
    parser.add_argument('--email', help='Correo de Bring!')
    parser.add_argument('--password', help='Contraseña de Bring!')
    parser.add_argument('--add', help='Nombre del ingrediente a añadir a la lista')
    parser.add_argument('--spec', help='Especificación del ingrediente (opcional)')
    parser.add_argument('--list-uuid', help='UUID de la lista Bring! a usar')
    args = parser.parse_args()

    email = args.email or os.getenv('BRING_EMAIL')
    password = args.password or os.getenv('BRING_PASSWORD')

    if not email:
        email = input('Correo de Bring!: ').strip()
    if not password:
        password = getpass.getpass('Contraseña de Bring!: ').strip()

    if not email or not password:
        print('Error: faltan credenciales de Bring!')
        sys.exit(1)

    target_uuid = args.list_uuid or os.getenv('BRING_LIST_UUID', 'a5492637-1aff-45e0-b1e3-1c0a1e48bde9')

    async with aiohttp.ClientSession() as session:
        bring = Bring(email, password, sessionAsync=session)

        print('Iniciando sesión en Bring!...')
        await bring.loginAsync()
        print('Login correcto.')

        lists = (await bring.loadListsAsync()).get('lists', [])
        print(f'Listas encontradas: {len(lists)}')
        for idx, lst in enumerate(lists, start=1):
            print(f"{idx}. {lst.get('name')} - UUID: {lst.get('listUuid')}")

        chosen_list = next((lst for lst in lists if lst.get('listUuid') == target_uuid), None)
        if not chosen_list:
            print(f'Error: no se encontró la lista con UUID {target_uuid}')
            return

        print(f'\nUsando lista fija: {chosen_list.get("name")} - UUID: {target_uuid}')

        if args.add:
            await add_purchase_item(bring, target_uuid, args.add, args.spec)
            print('\nLista después de añadir el ítem:')
            await show_purchase_items(bring, target_uuid, chosen_list.get('name'))
        else:
            await show_purchase_items(bring, target_uuid, chosen_list.get('name'))


if __name__ == '__main__':
    asyncio.run(main())