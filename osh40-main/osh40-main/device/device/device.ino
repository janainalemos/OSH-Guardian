/*
  University of Beira Interior
  PhD Thesis - Industrial Engineering and Management
  Occupational Health and Safety 4.0 – New approach to individual environmental risk assessment and management

  Monitoring device for dust, noise, UV, illuminance, temperature, humidity, and gas

  The device reads the above mentioned variables and publishes their values through MQTT every 10 minutes. 
  
  Temperature and humidity are checked every ten minutes by the device and if their values are too high or too low the yellow LED 
  (that advises attention) is activated by the device.

  The gas sensor is read every minute and if gas is detected, the blue LED is activated by the device. The gas status (true or false) 
  is sent through MQTT every ten minutes along with the other values.
  
  If dust, noise and/or UV thresholds have been exceeded according to the aplicable standards, laws etc. 
  the red LED must be turned on, otherwise, it must be kept off. To calculate the daily doses of radiation and noise, 
  the device adds the values read from the sensors to the values obtained previously.

  For dust the device considers the values obtained from the sensors each ten minutes and decide to turn the red LED on or not.

  Illuminance level is read every ten minutes - very bright, bright, light, dim, dark. 
  This information does not generate alarms, but is used by the AI to identify abrupt changes in illuminance, which can facilitate the occurrence of accidents.

  To know more details the worker should consult the app, that will show all measures, max and min values etc. 

  All this information is stored in a database on the server and is analyzed by the AI application.
*/

/*
 * References
 * 
 * Interface to Shinyei Model PPD42NS Particle Sensor
 * Program by Christopher Nafis, Written April 2012
 */

#include <DHT.h>
#include <Adafruit_Sensor.h>

#include <Wire.h>

#include <WiFiClientSecure.h>
#include <PubSubClient.h>

#include "SPIFFS.h"

#define ERROR -1
#define SUCCESS 0

// GAS  
#define GAS_ANALOG 39 //(VN)

// UV
#define UVPIN 36 // (VP)

// NOISE
#define NOISE_ANALOG 35 

// DHT11 - Temperature and humidity
#define DHTTYPE    DHT11     

#define DHTPIN 27

// LIGHT
#define LIGHTPIN 33

// DUST
#define DUST_PIN 32

// Limits
// GAS_LIMIT: 0,1% v/v = 1000 ppm
#define GAS_LIMIT 1000

// Humidity (%)
#define HUMIDITY_MIN 50
#define HUMIDITY_MAX 70

// Temperature (Celsius degrees)
#define TEMPERATURE_MIN 10
#define TEMPERATURE_MAX 30

// Alarms
// Noise, light, dust, UV alarm (red LED)
#define ALARM_RED_LED 19

// Temperature and humidity alarm (yellow LED)
#define ALARM_YELLOW_LED 5

// Gas alarm (blue LED)
#define GAS_LED 4

// Gas present
#define GAS_TRUE 1
#define GAS_FALSE 0

// Light level

#define DARK 1
#define DIM 2
#define LIGHT 3
#define BRIGHT 4
#define VERY_BRIGHT 5

// Number of measurements

// Performs 10 gas measurements and then read the other sensors
#define GAS_MEASUREMENTS 10

// Checks the gas every minute and the other variables every 10 minutes
#define INTERVAL_GAS 60000

// We reset the counters when it completes 9 hours of work - 6 measurements/hour
#define MAX_MEASUREMENTS 54 

// Files
// We use files to store the daily doses for UV (SED) and noise. 
// This approach prevents data loss if the device resets during the work shift.

#define FILE_DAY_SED "/daySed.txt"
#define FILE_DAY_NOISE_7H "/dayNoise7h.txt"
#define FILE_DAY_NOISE_6H "/dayNoise6h.txt"
#define FILE_DAY_NOISE_5H "/dayNoise5h.txt"
#define FILE_DAY_NOISE_4H "/dayNoise4h.txt"

// File with the number of measurements
#define FILE_MEASUREMENTS "/measurements.txt"

unsigned long starttime; // dust

// Limits 
const int noiseMax8h = 85;
const int noiseMax7h = 86;
const int noiseMax6h = 87;
const int noiseMax5h = 88; // (if noise = 89 we also consider 5h of max exposure)
const int noiseMax4h = 90; 
const int sedMax = 1;
const int dustMax = 1415000;

// Counters 
float daySed = 0;

// We consider 6 measurements/hour
int dayNoise7h = 0;  // 42 to reach the limit (7h) 
int dayNoise6h = 0;  // 36 to reach the limit (6h)
int dayNoise5h = 0;  // 30 to reach the limit (5h)
int dayNoise4h = 0;  // 24 to reach the limit (4h)

// We reset the counters when it completes 9 hours of work (54 measurements)
int measurements = 0;

const float hExp = 0.2; // hours in the sun - 10-12 min

const float errorDHT = 111; // Temperature / humidity

// Alarms - red LED
int alarmNoise = 0;
int alarmDust = 0;
int alarmUv = 0;


// Alarms - yellow LED
int alarmTemperature = 0;
int alarmHumidity = 0;

///////////////////////////////////////////////
// MQTT - must be different for each device
#define TOPIC_TEMPERATURE "6000/temperature"
#define TOPIC_HUMIDITY "6000/humidity"
#define TOPIC_NOISE "6000/noise"
#define TOPIC_UV "6000/uv"
#define TOPIC_DUST "6000/dust"
#define TOPIC_LIGHT "6000/light"
#define TOPIC_GAS "6000/gas"

/////////////////////////////////////////////////

// MQTT seguro
#define MQTT_PORT 8883

IPAddress mqttServer;  // Server IP address

const char*  pskIdent = "D6000"; // PSK identity (sometimes called key hint)
const char*  psKey = "8387343820202122"; // PSK Key (must be hex string without 0x)

// WI-FI
const char* ssid     = "Sunrise";
const char* password = "janaina1983";

/////////////////////////////////////////////////

WiFiClientSecure client;
PubSubClient mqttClient(client);

// NOISE - Sample window width in mS (50 mS = 20Hz)
const int sampleWindow = 50;                             
unsigned int sample;

DHT dht(DHTPIN, DHTTYPE);

//////////////////

/*
 * Reads and write doses from files.
 */
float readFloatFile(char* fileName)
{
  File file;
  char content[10];
  float num=0;
  int i;
    
  file = SPIFFS.open(fileName);
 
  if(!file)
  {
    Serial.println("Failed to open file for reading");
    return ERROR;
  }

  i=0;
  while(file.available())
  {
    content[i]=file.read();
    i++;
  }
    
  content[i]='\0';

  num=atof(content);
    
  file.close();

  return num;
}

float writeFloatFile(char* fileName, float value)
{
  File file;
  char content[10];
    
  file = SPIFFS.open(fileName, FILE_WRITE);
 
  if(!file)
  {
    Serial.println("Failed to open file for writing");
    return ERROR;
  }

  dtostrf(value, (-3), 2, content);

  if (!file.print(content)) 
  {
    file.close();
    return ERROR;
  }
    
  file.close();

  return SUCCESS;
}

void readDosesFiles()
{
  float num;

  if(!SPIFFS.begin(true))
  {
    Serial.println("An Error has occurred while mounting SPIFFS");
    return;
  }
  
  num = readFloatFile(FILE_DAY_SED);
  if(num != ERROR)
  {
    daySed = num;
  }
  else
  {
    daySed = 0;
  }
  
  Serial.print("FILE_DAY_SED = ");
  Serial.println(num);

  num = readFloatFile(FILE_DAY_NOISE_7H);
  if(num != ERROR)
  {
    dayNoise7h = num;
  }
  else
  {
    dayNoise7h = 0;
  }
  
  Serial.print("FILE_DAY_NOISE_7H = ");
  Serial.println(num);

  num = readFloatFile(FILE_DAY_NOISE_6H);
  if(num != ERROR)
  {
    dayNoise6h = num;
  }
  else
  {
    dayNoise6h = 0;
  }
  
  Serial.print("FILE_DAY_NOISE_6H = ");
  Serial.println(num);  

  num = readFloatFile(FILE_DAY_NOISE_5H);
  if(num != ERROR)
  {
    dayNoise5h = num;
  }
  else
  {
    dayNoise5h = 0;
  }
  
  Serial.print("FILE_DAY_NOISE_5H = ");
  Serial.println(num); 

  num = readFloatFile(FILE_DAY_NOISE_4H);
  if(num != ERROR)
  {
    dayNoise4h = num;
  }
  else
  {
    dayNoise4h = 0;
  }
  
  Serial.print("FILE_DAY_NOISE_4H = ");
  Serial.println(num);

  num = readFloatFile(FILE_MEASUREMENTS);
  if(num != ERROR)
  {
    measurements = num;
  }
  else
  {
    measurements = 0;
  }
  
  Serial.print("FILE_MEASUREMENTS = ");
  Serial.println(num);
}

/*
 * Resets counters and files
 */
void resetCounters()
{
  Serial.println(".....Reseting counters and files.....");
      
  // Resets counters 
  daySed = 0;
  dayNoise7h = 0;  
  dayNoise6h = 0;  
  dayNoise5h = 0;  
  dayNoise4h = 0;  
  measurements = 0;

  // Resets files
  writeFloatFile(FILE_DAY_SED, 0);
  writeFloatFile(FILE_DAY_NOISE_7H, 0);
  writeFloatFile(FILE_DAY_NOISE_6H, 0);
  writeFloatFile(FILE_DAY_NOISE_5H, 0);
  writeFloatFile(FILE_DAY_NOISE_4H, 0);
  writeFloatFile(FILE_MEASUREMENTS, 0);
}

/*
 * Handles MQTT incoming messages.
 */
void callback(char* topic, byte* payload, unsigned int length) 
{
   Serial.print("New message [");
   Serial.print(topic);
   Serial.println("]");
}

/*
 * Checks the temperature.
 */
float readDHTTemperature() 
{
  // Read temperature as Celsius (the default)
  float t = dht.readTemperature();

  // Check if any reads failed and exit early (to try again).
  if (isnan(t)) 
  {    
    Serial.println("Failed to read from DHT sensor!");
    return errorDHT;
  }
  else 
  {
    if ((t < TEMPERATURE_MIN) || (t > TEMPERATURE_MAX))
    {
      alarmTemperature = 1; // Yellow LED ON
    }
    else
    {
      alarmTemperature = 0; // Yellow LED OFF
    }
    return t;
  }
}

/*
 * Checks the humidity.
 */
float readDHTHumidity() 
{
  // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
  float h = dht.readHumidity();
  if (isnan(h)) 
  {
    Serial.println("Failed to read from DHT sensor!");
    return errorDHT;
  }
  else 
  {
    if ((h < HUMIDITY_MIN) || (h > HUMIDITY_MAX))
    {
      alarmHumidity = 1; // Yellow LED ON    
    }
    else
    {
      alarmHumidity = 0; // Yellow LED OFF
    }
    return h;
  }
}

/*
 * Checks the noise level
 */
float readNoise()
{
  unsigned long startMillis = millis();
  
  unsigned int signalMax = 0;                           //minimum value
  unsigned int signalMin = 1024;                        //maximum value

  float peakToPeak = 0;

  int noise;
                                                        // collect data for 50 ms
  while (millis() - startMillis < sampleWindow)
  {
    sample = analogRead(NOISE_ANALOG);                  //get reading from microphone
    if (sample < 1024)                                  // toss out spurious readings
    {
      if (sample > signalMax)
      {
        signalMax = sample;                             // save just the max levels
      }
      else if (sample < signalMin)
      {
        signalMin = sample;                             // save just the min levels
      }
    }
  }
 
  peakToPeak = signalMax - signalMin;                 // max - min = peak-peak amplitude

 // Serial.print("peakToPeak: ");
 // Serial.println(peakToPeak);

  noise = map(peakToPeak,20,900,49.5,90);

  if (noise > noiseMax8h)
  {
    if (noise == noiseMax7h)
    {
      dayNoise7h = dayNoise7h + 1;
    }
    else if (noise == noiseMax6h)
    {
      dayNoise6h = dayNoise6h + 1;
    }
    else if (noise >= noiseMax5h and noise < noiseMax4h)
    {
      dayNoise5h = dayNoise5h + 1;
    }
    else
    {
      dayNoise4h = dayNoise4h + 1;     
    }
            
  }      
  
  if ((dayNoise7h >= 42) || (dayNoise6h >= 36) || (dayNoise5h >= 30) || (dayNoise4h >= 24))
  {
     Serial.println("alarmRedLed = 1");
     Serial.print("dayNoise7h = ");
     Serial.println(dayNoise7h);
     Serial.print("dayNoise6h = ");
     Serial.println(dayNoise6h);
     Serial.print("dayNoise5h = ");
     Serial.println(dayNoise5h);
     Serial.print("dayNoise4h = ");
     Serial.println(dayNoise4h);

     Serial.println("noise: alarmRedLed = 1");
     
     alarmNoise = 1;
  }
  else
  {
     Serial.println("noise: alarmRedLed = 0");

     alarmNoise = 0;
  }

  // Updates files
  writeFloatFile(FILE_DAY_NOISE_7H, dayNoise7h);
  writeFloatFile(FILE_DAY_NOISE_6H, dayNoise6h);
  writeFloatFile(FILE_DAY_NOISE_5H, dayNoise5h);
  writeFloatFile(FILE_DAY_NOISE_4H, dayNoise4h);

  return noise;
}

/*
 * Reads the UV index and calculates the standard erythemal dose (SED).
 */ 
float readUv()
{
  float sensorVoltage; 
  float sensorValue;
  float uvIndex;
  float jm2;
  float sed;

  sensorValue = analogRead(UVPIN);
  sensorVoltage = sensorValue/(4095*3.3); // 3.3

  //Serial.print("sensor voltage = ");
  //Serial.print(sensorVoltage);
  //Serial.println(" V");

  uvIndex = sensorVoltage/0.1; 
  Serial.print("UV index: ");
  Serial.println(uvIndex);

  jm2 = (uvIndex/40)*3600*hExp;
  sed = jm2/100;
   
  daySed = daySed + sed;
  
  if (daySed >= sedMax)
  {
    Serial.print("alarmRedLed = 1, daySed = ");
    Serial.println(daySed);
    
    alarmUv = 1;
  }
  else
  {
    Serial.print("alarmRedLed = 0, daySed = ");
    Serial.println(daySed);

    alarmUv = 0;
  }

  // Updates file
  writeFloatFile(FILE_DAY_SED, daySed);

  return sed;
}

/*
 * Reads the illuminance (lux).
 */
float readLight()
{
  float light;
  int lightLevel;

  light = analogRead(LIGHTPIN); 

  // We'll have a few threshholds, qualitatively determined
  if (light < 40) 
  {
    Serial.println(" => Dark");
    lightLevel = DARK;
  } 
  else if (light < 800) 
  {
    Serial.println(" => Dim");
    lightLevel = DIM;
  } 
  else if (light < 2000) 
  {
    Serial.println(" => Light");
    lightLevel = LIGHT;
  } 
  else if (light < 3200) 
  {
    Serial.println(" => Bright");
    lightLevel = BRIGHT;
  } 
  else 
  {
    Serial.println(" => Very bright");
    lightLevel = VERY_BRIGHT;
  }
    
  return lightLevel;
}

float readDust()
{
  unsigned long duration;
  unsigned long sampletime_ms = 30000;
  unsigned long lowpulseoccupancy = 0;
  float ratio = 0;
  float concentration = 0;
  
  duration = pulseIn(DUST_PIN, LOW);
  lowpulseoccupancy = lowpulseoccupancy+duration;

  if ((millis()-starttime) > sampletime_ms)
  {
    ratio = lowpulseoccupancy/(sampletime_ms*10.0);  // Integer percentage 0=>100
    concentration = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62; // using spec sheet curve

    /*
    Serial.print("lowpulseoccupancy: ");
    Serial.println(lowpulseoccupancy);
    Serial.print("ratio: ");
    Serial.println(ratio);
    */
    Serial.print("dust concentration: ");
    
    //Serial.print(concentration);
    //Serial.println(" pcs/0.01cf");
    
    concentration = concentration*100; // pcs/0.01cf -> pcs/1cf
    
    //Serial.print(concentration);
    //Serial.println(" pcs/cf");
    
    concentration = concentration/35.315; // pcs/1cf -> pcs/cubic meter
    Serial.print(concentration);
    Serial.println(" pcs/cubic meter");
    
    lowpulseoccupancy = 0;

    if (concentration > dustMax)
    {
        Serial.print("alarmalarmRedLed = 1, dust = ");
        Serial.println(concentration);
        
        alarmDust = 1;      
    }
    else
    {
        Serial.print("alarmalarmRedLed = 0, dust = ");
        Serial.println(concentration);
        
        alarmDust = 0;     
    }
    
    starttime = millis();

    return concentration;
  }
}

/*
 * Checks if there is gas or smoke in the environment.
 */
int readGas()
{
  int gassensorAnalog = analogRead(GAS_ANALOG);
  int gas = GAS_FALSE;

  Serial.print("Gas Sensor: ");
  Serial.println(gassensorAnalog);

  if (gassensorAnalog >= GAS_LIMIT) 
  {
    gas = GAS_TRUE;
    digitalWrite (GAS_LED, HIGH) ; // Blue LED ON
  }
  else
  {
    gas = GAS_FALSE;
    digitalWrite (GAS_LED, LOW) ; // Blue LED OFF
  }
  return gas;
}

void setup() 
{
  // initialize serial communication 
  Serial.begin(115200);

  pinMode(NOISE_ANALOG, INPUT);
  pinMode(GAS_ANALOG, INPUT);  
  pinMode(LIGHTPIN, INPUT);

  // GAS
  pinMode(GAS_LED, OUTPUT); 

  // TEMP/HUM
  pinMode(ALARM_YELLOW_LED, OUTPUT); 

  // DUST
  pinMode(DUST_PIN,INPUT);

  // ALARM_RED_LED
  pinMode(ALARM_RED_LED, OUTPUT); 

  delay(5000); /////////////////

  
  starttime = millis(); // dust

  // Reads daily doses for noise and UV(SED)
  readDosesFiles();

  if(measurements >= MAX_MEASUREMENTS)
  {
    resetCounters();
  }
 
  // MQTT
  Serial.print("Attempting to connect to SSID: ");
  Serial.println(ssid);

  
  WiFi.begin(ssid, password);

  // attempt to connect to Wifi network:
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    // wait 1 second for re-trying
    delay(1000);
  }

  Serial.print("Connected to ");
  Serial.println(ssid);


  // DNS 

  if(WiFi.hostByName("devices.osh40.online", mqttServer) == 1)
  {
    Serial.print("devices.osh40.online = ");
    Serial.println(mqttServer);
  }
  else 
  {
    Serial.println("dns lookup failed");
  }

  // MQTT port and PSK
  mqttClient.setServer(mqttServer, MQTT_PORT);

  client.setPreSharedKey(pskIdent, psKey); //client

  mqttClient.setCallback(callback);
  /////////////////////////////
  
  dht.begin();

}

void loop() 
{
  // DHT11
  float hum;
  float temp;

  // LIGHT
  float light;
  
  // NOISE
  float dB;

  // DUST
  float dust;

  // UV
  float sed;

  // GAS
  int gas = GAS_FALSE;
  int gasLastTenMinutes = GAS_FALSE;

  int count = 0;

  if(measurements >= MAX_MEASUREMENTS)
  {
    resetCounters();
  }
  else 
  {
    Serial.print("measurements: ");
    Serial.println(measurements);
  }

  // GAS
  // Reads gas sensor once and send the value along with the other values
  gasLastTenMinutes = readGas(); 

  delay(2000);
  
  //Serial.print("GAS (TRUE/FALSE): ");
  //Serial.println(gasLastTenMinutes); 

 
  // DUST
  dust = readDust();
  
  //Serial.print("Dust (pcs/m3): ");
  //Serial.println(dust);
  
  // DHT11
  temp = readDHTTemperature();
  
  //Serial.print("Temperature (Celsius): ");
  //Serial.println(temp);
    
  hum = readDHTHumidity();
  
  //Serial.print("Humidity (%): ");
  //Serial.println(hum);

  // LM393 NOISE
  dB = readNoise();
  
  //Serial.print("Noise (dB): "); 
  //Serial.println(dB);
  
  // LIGHT
  light = readLight();
  
  //Serial.print("Light (lx): ");
  //Serial.println(lux);

  // UV
  sed = readUv(); //Read
  
  //Serial.print("UV (SED): ");
  //Serial.println(sed);

  // ALARM RED LED

  // Checks if there is an alarm for any of the monitored variables and turns the red LED ON / OFF
  if ((alarmNoise == 1) || (alarmDust == 1) || (alarmUv == 1))
  {
    digitalWrite (ALARM_RED_LED, HIGH) ; // ON
  }
  else
  {
    digitalWrite (ALARM_RED_LED, LOW) ; // OFF
  }

  // ALARM YELLOW LED
  // Checks if there is an alarm for any of the monitored variables and turns the yellow LED ON / OFF
  if ((alarmTemperature == 1) || (alarmHumidity == 1))
  {
    digitalWrite (ALARM_YELLOW_LED, HIGH) ; // ON
  }
  else
  {
    digitalWrite (ALARM_YELLOW_LED, LOW) ; // OFF
  }

  // MQTT
  char msg[100];
  int msgLen;
  
   while (!mqttClient.connected()) 
  {
    Serial.println("\nStarting connection to MQTT server..."); 
    if (! mqttClient.connect("esp32_test"))
    {
      Serial.println("MQTT failed!");
    }
    else 
    {
      Serial.println("MQTT works!");    
    }
    delay(10000); // wait 10 sec before retrying
  }

  // Publishes topics

  // dust
  // float to string
  dtostrf(dust, (-3), 2, msg);
  msgLen = strlen(msg);

  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_DUST, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_DUST OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_DUST FAIL");
  }
  
  // temperature
  // float to string
  dtostrf(temp, (-3), 2, msg);
  msgLen = strlen(msg);

  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_TEMPERATURE, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_TEMPERATURE OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_TEMPERATURE FAIL");
  }

  // humidity
  // float to string
  dtostrf(hum, (-3), 2, msg);
  msgLen = strlen(msg);

  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_HUMIDITY, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_HUMIDITY OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_HUMIDITY FAIL");
  }

  // noise
  // float to string
  dtostrf(dB, (-3), 2, msg);
  msgLen = strlen(msg);

  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_NOISE, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_NOISE OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_NOISE FAIL");
  }
  
  // light
  // float to string
  dtostrf(light, (-3), 2, msg);
  msgLen = strlen(msg);

  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_LIGHT, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_LIGHT OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_LIGHT FAIL");
  }

  // uv
  // float to string
  dtostrf(sed, (-3), 2, msg);
  msgLen = strlen(msg);

  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_UV, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_UV OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_UV FAIL");
  }

  // int to string
  itoa(gasLastTenMinutes,msg,2);
  Serial.print("MQTT: msg = ");
  Serial.print(msg);
  
  if(mqttClient.publish(TOPIC_GAS, msg, msgLen))
  {
    Serial.println(", MQTT: TOPIC_GAS OK");
  }
  else
  {
    Serial.println(", MQTT: TOPIC_GAS FAIL");
  }

  // GAS
  // only gasLastTenMinutes is sent through MQTT
  count = 0;
  gasLastTenMinutes = GAS_FALSE;
  while(count < 20) // teste, depois será 10
  {
    gas = readGas(); 
    
    if(gas == GAS_TRUE)
    {
      gasLastTenMinutes = GAS_TRUE;
    }
    Serial.print("GAS (TRUE/FALSE): ");
    Serial.println(gas);

    count++;

    delay(2000);
    //delay(INTERVAL_GAS); // 1 minuto
  }

   // We reset the counters when it completes 9 hours of work - 6 measurements/hour
   measurements++;

   // Updates file
   writeFloatFile(FILE_MEASUREMENTS, measurements);
   
   mqttClient.loop();

}
