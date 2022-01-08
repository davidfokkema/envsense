import asyncio
import struct
import threading
import time
import uuid

import bleak
import rumps

DEVNAME = "Arduino EnvSense"
BASE_UUID = 0x0000000000001000800000805F9B34FB
PRESSURE_UUID = uuid.UUID(int=BASE_UUID + (0x2A6D << 96))
TEMPERATURE_UUID = uuid.UUID(int=BASE_UUID + (0x2A6E << 96))
HUMIDITY_UUID = uuid.UUID(int=BASE_UUID + (0x2A6F << 96))
ECO2_UUID = uuid.UUID(int=BASE_UUID + (0x2BD3 << 96))


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
    pressure = 0.0
    humidity = 0.0
    eCO2 = 0.0

    def __init__(self):
        super(AwesomeStatusBarApp, self).__init__("EnvSense")

        self.menu_device = rumps.MenuItem("Searching...")
        self.menu_last_update = rumps.MenuItem("")
        self.menu_temperature = rumps.MenuItem("temperature")
        self.menu_pressure = rumps.MenuItem("pressure")
        self.menu_humidity = rumps.MenuItem("humidity")
        self.menu_eCO2 = rumps.MenuItem("eCO2")
        self.menu = [
            self.menu_device,
            self.menu_last_update,
            self.menu_temperature,
            self.menu_pressure,
            self.menu_humidity,
            self.menu_eCO2,
            None,
        ]

        self.menu_temperature.title = "Temperature: unknown"
        self.menu_temperature.state = True
        self.menu_pressure.title = "Pressure: unknown"
        self.menu_humidity.title = "Humidity: unknown"
        self.menu_eCO2.title = "eCO₂: unknown"

    @rumps.timer(5)
    @sync
    async def update_values(self, sender):
        if self.device is not None:
            try:
                async with bleak.BleakClient(self.device.address) as client:
                    (self.temperature,) = struct.unpack(
                        "<f", await client.read_gatt_char(TEMPERATURE_UUID)
                    )
                    (self.pressure,) = struct.unpack(
                        "<f", await client.read_gatt_char(PRESSURE_UUID)
                    )
                    (self.humidity,) = struct.unpack(
                        "<f", await client.read_gatt_char(HUMIDITY_UUID)
                    )
                    (self.eCO2,) = struct.unpack(
                        "<f", await client.read_gatt_char(ECO2_UUID)
                    )

                    self.last_update = time.time()
                    self.menu_temperature.title = (
                        f"Temperature: {self.temperature:.1f} ºC"
                    )
                    self.menu_pressure.title = f"Pressure: {self.pressure:.1f} hPa"
                    self.menu_humidity.title = f"Humidity: {self.humidity:.1f} %"
                    self.menu_eCO2.title = f"eCO₂: {self.eCO2:.0f} ppm"
                    self.update_title()
            except (asyncio.TimeoutError, bleak.BleakError):
                self.device = None
                self.menu_device.title = "Searching..."

    def update_title(self):
        title_items = []
        if self.menu_temperature.state:
            title_items.append(f"{self.temperature:.1f}ºC")
        if self.menu_pressure.state:
            title_items.append(f"{self.pressure:.0f}hPa")
        if self.menu_humidity.state:
            title_items.append(f"{self.humidity:.0f}%")
        if self.menu_eCO2.state:
            title_items.append(f"{self.eCO2:.0f}ppm")

        if title_items:
            self.title = " / ".join(title_items)
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
    @rumps.clicked("pressure")
    @rumps.clicked("humidity")
    @rumps.clicked("eCO2")
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


def main():
    AwesomeStatusBarApp().run()


if __name__ == "__main__":
    main()
