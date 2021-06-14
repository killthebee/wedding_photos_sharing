import os
import aiofiles
import asyncio
import logging

from aiohttp import web
from dotenv import load_dotenv
load_dotenv()


INTERVAL_SECS = os.getenv('INTERVAL_SECS', None)
if os.getenv('LOGGER', None):
    logger_level = logging.DEBUG
else:
    logger_level = logging.CRITICAL
logging.basicConfig(format=u'%(message)s', level=logger_level)
PATH_TO_FOLDER = os.getenv('PATH_TO_FOLDER', '')


async def kill_zip(parent_pid):
    proc = await asyncio.create_subprocess_exec('pgrep', '-P', f'{parent_pid}', stdout=asyncio.subprocess.PIPE)
    result, _ = await proc.communicate()
    zip_pid = int(result.decode())
    await asyncio.create_subprocess_exec('kill', '-9', f'{zip_pid}')


async def archivate(request):
    folder_name = request.match_info.get('archive_hash', None)
    path = f'{PATH_TO_FOLDER}/{folder_name}'

    if not os.path.exists(os.path.normpath(os.path.join(os.getcwd(), path))):
        async with aiofiles.open('missing_folder.html', mode='r') as missing_folder_file:
            missing_folder_page = await missing_folder_file.read()
        raise web.HTTPNotFound(text=missing_folder_page, content_type='text/html')

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=test.zip'
    await response.prepare(request)

    proc = await asyncio.create_subprocess_shell(f'zip -r -j - {path}', stdout=asyncio.subprocess.PIPE)
    try:
        while True:
            chunk = await proc.stdout.read(100)
            if proc.stdout.at_eof():
                break
            await response.write(chunk)
            if INTERVAL_SECS is not None:
                await asyncio.sleep(int(INTERVAL_SECS))
            logging.info(u'Sending archive chunk ...')
    except asyncio.CancelledError:
        logging.info(u'Download was interrupted')
        await kill_zip(proc.pid)
        await proc.communicate()
        raise
    except:
        logging.info(u'Something went rly wrong')
        await kill_zip(proc.pid)
        await proc.communicate()
        raise web.HTTPInternalServerError()

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
