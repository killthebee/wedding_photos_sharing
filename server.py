import aiofiles
import datetime
import asyncio

from aiohttp import web

INTERVAL_SECS = 0.5


async def archivate(request):
    folder_name = request.match_info.get('archive_hash', None)
    print(folder_name)
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=test.zip'

    await response.prepare(request)

    path = f'test_photos/{folder_name}'
    proc = await asyncio.create_subprocess_shell(f'zip -r -j - {path}', stdout=asyncio.subprocess.PIPE)
    while True:
        chunk = await proc.stdout.read(100)
        if proc.stdout.at_eof():
            break
        await response.write(chunk)
        # await asyncio.sleep(INTERVAL_SECS)
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')




if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
