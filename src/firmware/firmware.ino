#include <ArduinoBLE.h>
#include "Adafruit_MCP9808.h"
#include "bsec.h"


BLEService envService("181A");
BLEFloatCharacteristic temperatureCharacteristic("2A6E", BLERead | BLENotify);
BLEDescriptor temperatureDescriptor("2901", "Ambient temperature (ºC)");

BLEFloatCharacteristic pressureCharacteristic("2A6D", BLERead | BLENotify);
BLEDescriptor pressureDescriptor("2901", "Atmospheric pressure (hPa)");
BLEFloatCharacteristic humidityCharacteristic("2A6F", BLERead | BLENotify);
BLEDescriptor humidityDescriptor("2901", "Relative humidity (%)");
BLEFloatCharacteristic eCO2Characteristic("2BD3", BLERead | BLENotify);
BLEDescriptor eCO2Descriptor("2901", "Equivalent CO2 (ppm)");


Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();
Bsec iaqSensor;

unsigned long lastMeasurementTime = 0;

void setup() {
  BLE.begin();
  
  BLE.setLocalName("Arduino EnvSense");
  BLE.setDeviceName("Arduino EnvSense");

  envService.addCharacteristic(temperatureCharacteristic);
  envService.addCharacteristic(pressureCharacteristic);
  envService.addCharacteristic(humidityCharacteristic);
  envService.addCharacteristic(eCO2Characteristic);
  temperatureCharacteristic.addDescriptor(temperatureDescriptor);
  pressureCharacteristic.addDescriptor(pressureDescriptor);
  humidityCharacteristic.addDescriptor(humidityDescriptor);
  eCO2Characteristic.addDescriptor(eCO2Descriptor);
  BLE.addService(envService);

  BLE.setAdvertisedService(envService);
  BLE.advertise();

  tempsensor.begin(0x18);
  tempsensor.setResolution(3); // sets the resolution mode of reading, the modes are defined in the table bellow:
  // Mode Resolution SampleTime
  //  0    0.5°C       30 ms
  //  1    0.25°C      65 ms
  //  2    0.125°C     130 ms
  //  3    0.0625°C    250 ms

  Wire.begin();
  iaqSensor.begin(BME680_I2C_ADDR_SECONDARY, Wire);
  bsec_virtual_sensor_t sensorList[3] = {
    BSEC_OUTPUT_RAW_PRESSURE,
    BSEC_OUTPUT_CO2_EQUIVALENT,
    BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_HUMIDITY,
  };
  iaqSensor.updateSubscription(sensorList, 3, BSEC_SAMPLE_RATE_LP);
}

void loop() {
  unsigned long now;
  
  BLE.poll();
  
  now = millis();
  if ((now - lastMeasurementTime) > 1000) {
    lastMeasurementTime = now;
    tempsensor.wake();
    temperatureCharacteristic.writeValue(tempsensor.readTempC());
    tempsensor.shutdown_wake(1);
  }

  if (iaqSensor.run()) {
    pressureCharacteristic.writeValue(iaqSensor.pressure / 100);
    humidityCharacteristic.writeValue(iaqSensor.humidity);
    eCO2Characteristic.writeValue(iaqSensor.co2Equivalent);
  }
}
