import aioserial
import asyncio


async def read_and_print(aioserial_instance: aioserial.AioSerial):
    while True:
        number_of_byte_like_data_written: int = await aioserial_instance.write_async(b"Some data")
        raw_data: bytes = await aioserial_instance.read_async()
        print(raw_data.decode(errors="ignore"), end="", flush=True)


serialInterface = aioserial.AioSerial(port="COM5")
asyncio.run(read_and_print(serialInterface))
