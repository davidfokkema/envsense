import asyncio
import struct
import uuid

import bleak
import rumps

DEVNAME = "Arduino EnvSense"
BASE_UUID = 0x0000000000001000800000805F9B34FB
TEMP_UUID = uuid.UUID(int=BASE_UUID + (0x2A6E << 96))


class AwesomeStatusBarApp(rumps.App):
    def __init__(self):
        super(AwesomeStatusBarApp, self).__init__("Awesome App")
        self.menu = ["Preferences", "Silly button", "Say hi"]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.read_temperature())

    async def read_temperature(self):
        dev = await self.find_device()
        if dev is not None:
            client = bleak.BleakClient(dev.address)
            await client.connect()
            temperature = struct.unpack("<f", await client.read_gatt_char(TEMP_UUID))[0]
            self.title = f"{temperature:.1f} ºC"

    async def find_device(self):
        devices = await bleak.BleakScanner.discover()
        for dev in devices:
            if DEVNAME in dev.name:
                return dev
        else:
            return None

    @rumps.clicked("Preferences")
    def prefs(self, _):
        rumps.alert("jk! no preferences available!")

    @rumps.clicked("Silly button")
    def onoff(self, sender):
        sender.state = not sender.state

    @rumps.clicked("Say hi")
    def sayhi(self, _):
        rumps.notification("Awesome title", "amazing subtitle", "hi!!1")


if __name__ == "__main__":
    asyncio.run(AwesomeStatusBarApp().run())
