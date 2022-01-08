#include <ArduinoBLE.h>
#include "Adafruit_MCP9808.h"


BLEService envService("181A");
BLEFloatCharacteristic temperatureCharacteristic("2A6E", BLERead | BLENotify);
BLEDescriptor temperatureDescriptor("2901", "Ambient temperature (ºC)");

Adafruit_MCP9808 tempsensor = Adafruit_MCP9808();

unsigned long lastMeasurementTime = 0;

void setup() {
  Serial.begin(9600);
  BLE.begin();
  
  BLE.setLocalName("Arduino EnvSense");
  BLE.setDeviceName("Arduino EnvSense");

  envService.addCharacteristic(temperatureCharacteristic);
  temperatureCharacteristic.addDescriptor(temperatureDescriptor);
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
}

void loop() {
  unsigned long now;
  
  // put your main code here, to run repeatedly:
  BLE.poll();
  now = millis();
  if ((now - lastMeasurementTime) > 1000) {
    lastMeasurementTime = now;
    tempsensor.wake();
    temperatureCharacteristic.writeValue(tempsensor.readTempC());
    tempsensor.shutdown_wake(1);
  }
}
