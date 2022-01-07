import asyncio
import struct
import time
import uuid

import bleak

DEVNAME = "Arduino EnvSense"
BASE_UUID = 0x0000000000001000800000805F9B34FB
TEMP_UUID = uuid.UUID(int=BASE_UUID + (0x2A6E << 96))


async def find_device():
    devices = await bleak.BleakScanner.discover()
    for dev in devices:
        if DEVNAME in dev.name:
            return dev
    else:
        return None


async def connect_client(address):
    client = bleak.BleakClient(address)
    await client.connect()
    return client


def callback(sender, data):
    print(sender, data)


async def main():
    dev = await find_device()
    if dev is not None:
        client = await connect_client(dev.address)
        temperature = struct.unpack("<f", await client.read_gatt_char(TEMP_UUID))[0]
        print(f"{temperature:.1f} ºC")
    else:
        print("Device not found!")


asyncio.run(main())
