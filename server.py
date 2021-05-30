import os
import aiofiles
import datetime
import asyncio

from aiohttp import web

INTERVAL_SECS = 0.5


async def archivate(request):
    folder_name = request.match_info.get('archive_hash', None)
    path = f'test_photos/{folder_name}'

    if not os.path.exists(os.path.normpath(os.path.join(os.getcwd(), path))):
        async with aiofiles.open('missing_folder.html', mode='r') as missing_folder_file:
            missing_folder_page = await missing_folder_file.read()
        raise web.HTTPNotFound(text=missing_folder_page, content_type='text/html')

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=test.zip'
    await response.prepare(request)

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
