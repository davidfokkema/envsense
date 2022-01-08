import asyncio
import struct
import time
import uuid

import bleak
import rumps

DEVNAME = "Arduino EnvSense"
BASE_UUID = 0x0000000000001000800000805F9B34FB
TEMP_UUID = uuid.UUID(int=BASE_UUID + (0x2A6E << 96))


def sync(func):
    def f(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(func(*args, **kwargs))

    return f


class AwesomeStatusBarApp(rumps.App):
    def __init__(self):
        super(AwesomeStatusBarApp, self).__init__("EnvSense")

        self.menu_device = rumps.MenuItem("Searching for device...")
        self.menu_temp = rumps.MenuItem("Waiting for data...")
        self.menu = [self.menu_device, self.menu_temp]

        self.device = None

    @rumps.timer(2)
    @sync
    async def update_temperature(self, sender):
        print("Update...")
        if self.device is not None:
            async with bleak.BleakClient(self.device.address) as client:
                temperature = struct.unpack(
                    "<f", await client.read_gatt_char(TEMP_UUID)
                )[0]
                self.title = f"{temperature:.1f} ºC"

    @rumps.timer(5)
    @sync
    async def find_device(self, sender):
        if self.device is None:
            devices = await bleak.BleakScanner.discover()
            for dev in devices:
                if DEVNAME in dev.name:
                    self.device = dev

    # @rumps.clicked("Preferences")
    # def prefs(self, _):
    #     rumps.alert("jk! no preferences available!")

    # @rumps.clicked("Silly button")
    # def onoff(self, sender):
    #     sender.state = not sender.state

    # @rumps.clicked("Say hi")
    # def sayhi(self, _):
    #     rumps.notification("Awesome title", "amazing subtitle", "hi!!1")


if __name__ == "__main__":
    rumps.debug_mode(True)

    AwesomeStatusBarApp().run()
