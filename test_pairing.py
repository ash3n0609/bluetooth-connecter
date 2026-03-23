import asyncio

async def linux_test():
    import sys
    if sys.platform != "linux": return
    process = await asyncio.create_subprocess_exec(
        'bluetoothctl', 'paired-devices',
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    print("Paired:", stdout.decode())

asyncio.run(linux_test())
