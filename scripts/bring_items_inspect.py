import os
import asyncio
import aiohttp
from python_bring_api.bring import Bring

async def main():
    email = os.getenv('BRING_EMAIL')
    password = os.getenv('BRING_PASSWORD')
    if not email or not password:
        print('Set BRING_EMAIL and BRING_PASSWORD')
        return
    async with aiohttp.ClientSession() as session:
        bring = Bring(email, password, sessionAsync=session)
        await bring.loginAsync()
        lists = (await bring.loadListsAsync()).get('lists', [])
        if not lists:
            print('No lists')
            return
        items = await bring.getItemsAsync(lists[0]['listUuid'])
        print('type(items)=', type(items))
        print('repr(items)=', repr(items))

if __name__ == '__main__':
    asyncio.run(main())
