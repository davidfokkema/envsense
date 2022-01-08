import asyncio
import struct
import threading
import time
import uuid

import bleak
import rumps

DEVNAME = "Arduino EnvSense"
BASE_UUID = 0x0000000000001000800000805F9B34FB
TEMP_UUID = uuid.UUID(int=BASE_UUID + (0x2A6E << 96))


def sync(func):
    def f(*args, **kwargs):
        asyncio.run(func(*args, **kwargs))

    f.__name__ = func.__name__
    return f


class AwesomeStatusBarApp(rumps.App):

    device = None
    scan_thread = None

    last_update = None
    temperature = 0.0

    def __init__(self):
        super(AwesomeStatusBarApp, self).__init__("EnvSense")

        self.menu_device = rumps.MenuItem("Searching...")
        self.menu_last_update = rumps.MenuItem("")
        self.menu_temp = rumps.MenuItem("temperature")
        self.menu = [self.menu_device, self.menu_last_update, self.menu_temp, None]

        self.menu_temp.title = "Temperature: Unknown"
        self.menu_temp.state = True

    @rumps.timer(5)
    @sync
    async def update_temperature(self, sender):
        if self.device is not None:
            try:
                async with bleak.BleakClient(self.device.address) as client:
                    (self.temperature,) = struct.unpack(
                        "<f", await client.read_gatt_char(TEMP_UUID)
                    )
                    self.last_update = time.time()
                    self.menu_temp.title = f"Temperature: {self.temperature:.1f} ºC"
                    self.update_title()
            except (asyncio.TimeoutError, bleak.BleakError):
                self.device = None
                self.menu_device.title = "Searching..."

    def update_title(self):
        title_items = []
        if self.menu_temp.state:
            title_items.append(f"{self.temperature:.1f} ºC")
        if title_items:
            self.title = " ".join(title_items)
        else:
            self.title = "EnvSense"

    @rumps.timer(10)
    def start_scan_if_needed(self, sender):
        # only execute when there is no connected device and there is not a
        # currently running scan thread
        if self.device is None and (
            self.scan_thread is None or not self.scan_thread.is_alive()
        ):
            self.scan_thread = threading.Thread(target=self.scan_devices)
            self.scan_thread.start()

    @sync
    async def scan_devices(self):
        devices = await bleak.BleakScanner.discover()
        for dev in devices:
            if DEVNAME in dev.name:
                self.device = dev
                self.menu_device.title = dev.name

    @rumps.timer(1)
    def update_last_update(self, sender):
        text = "Last update: "
        if self.last_update is None:
            text += "never"
        else:
            delta_t = time.time() - self.last_update
            if delta_t < 5:
                text += "just now"
            elif delta_t < 60:
                text += f"{delta_t:.0f} seconds ago"
            elif delta_t < 2 * 60:
                text += "1 minute ago"
            elif delta_t < 60 * 60:
                text += f"{delta_t / 60:.0f} minutes ago"
            elif delta_t < 2 * 60 * 60:
                text += "1 hour ago"
            else:
                text += f"{delta_t / 3600:.0f} hours ago"
        self.menu_last_update.title = text

    @rumps.clicked("temperature")
    def change_temperature_state(self, sender):
        sender.state = not sender.state
        self.update_title()

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
