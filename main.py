import os
import subprocess
import asyncio
import aiofiles

# subprocess.call("gedit")
# program = "gedit"
# process = subprocess.Popen(program)
# code = process.wait()

# print(code)

# process = subprocess.Popen(['zip', '-r', '-', 'test'], stdout=subprocess.PIPE)
# archive, _ = process.communicate()

async def write_to_file(data):
    async with aiofiles.open('test.zip', 'wb') as f:
        await f.write(data)


async def archive(path):
    proc = await asyncio.create_subprocess_shell(f'zip -r - {path}', stdout=asyncio.subprocess.PIPE)
    archive = b''
    while True:
        chunk = await proc.stdout.read(100)
        if proc.stdout.at_eof():
            break
        archive += chunk
    print(archive)
    await write_to_file(archive)
    # with open('test.zip', 'wb') as outfile:
    #     outfile.write(archive)


asyncio.run(archive('test1'))