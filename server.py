import os
import aiofiles
import asyncio
import logging
import argparse

from aiohttp import web


async def kill_zip(parent_pid):
    proc = await asyncio.create_subprocess_exec('pgrep', '-P', f'{parent_pid}', stdout=asyncio.subprocess.PIPE)
    result, _ = await proc.communicate()
    zip_pid = int(result.decode())
    await asyncio.create_subprocess_exec('kill', '-9', f'{zip_pid}')


async def archivate(request):
    folder_name = request.match_info.get('archive_hash', None)
    path = f"{request.app['path_to_folder']}/{folder_name}"

    if not os.path.exists(os.path.normpath(os.path.join(os.getcwd(), path))):
        async with aiofiles.open('missing_folder.html', mode='r') as missing_folder_file:
            missing_folder_page = await missing_folder_file.read()
        raise web.HTTPNotFound(text=missing_folder_page, content_type='text/html')

    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=test.zip'
    await response.prepare(request)

    proc = await asyncio.create_subprocess_shell(f'zip -r - .', cwd=path, stdout=asyncio.subprocess.PIPE)
    try:
        while True:
            chunk = await proc.stdout.read(100)
            if proc.stdout.at_eof():
                logging.info(u'Finish sending archive chunks')
                break
            await response.write(chunk)
            if request.app['interval_secs'] is not None:
                await asyncio.sleep(int(request.app['interval_secs']))
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
    parser = argparse.ArgumentParser(description='server settings')
    parser.add_argument('-i', '--interval_secs', default=None, help='interval between downloading zip chunks')
    parser.add_argument('-p', '--ptf', default='test_photos', help='path to folder with photos')
    parser.add_argument('-l', '--logger', default=True, help='logging level')
    args = parser.parse_args()

    logger_level = logging.CRITICAL
    if args.logger:
        logger_level = logging.DEBUG
    logging.basicConfig(format=u'%(message)s', level=logger_level)

    app = web.Application()
    app['interval_secs'] = args.interval_secs
    app['path_to_folder'] = args.ptf

    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
