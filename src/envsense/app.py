import asyncio
import struct
import threading
import uuid

import bleak
import rumps

DEVNAME = "Arduino EnvSense"
BASE_UUID = 0x0000000000001000800000805F9B34FB
TEMP_UUID = uuid.UUID(int=BASE_UUID + (0x2A6E << 96))


def sync(func):
    def f(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        loop.run_until_complete(func(*args, **kwargs))

    return f


class AwesomeStatusBarApp(rumps.App):

    device = None
    scan_thread = None

    def __init__(self):
        super(AwesomeStatusBarApp, self).__init__("EnvSense")

        self.menu_device = rumps.MenuItem("Searching for device...")
        self.menu_temp = rumps.MenuItem("Waiting for data...")
        self.menu = [self.menu_device, self.menu_temp]

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
    def start_scan_if_needed(self, sender):
        print("Start scan")
        if self.device is None and (
            self.scan_thread is None or not self.scan_thread.is_alive()
        ):
            self.scan_thread = threading.Thread(target=self.scan_devices)
            self.scan_thread.start()
        print("Done")

    @sync
    async def scan_devices(self):
        print("Scanning...")
        devices = await bleak.BleakScanner.discover()
        for dev in devices:
            if DEVNAME in dev.name:
                self.device = dev
        print("Scanning done.")

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
