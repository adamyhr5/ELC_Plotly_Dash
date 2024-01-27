//Ado Haruna
//Dept of Mechatronics Engineering
//Bayero University, Kano - Nigeria
//aharuna.mct@buk.edu.ng
//1/23/2024

#include <WiFi.h>
#include <PubSubClient.h>

//WiFi and MQTT
// Update these with values suitable for your network.
const char* ssid = "Your WiFi SSID";
const char* password = "Your WiFI password";
const char* mqtt_username = "Your MQTT Username";     
const char* mqtt_password = "Your MQTT password";      
const char* mqtt_server = "Your MQTT host address";
const char* clientID = "ESP32";

//Variables
int count=0;
int led_pin = 2;          //ESP32 Devkit1 on-board LED
//generator model variables
int dT = 100;             //Sample Time
int prd_count;            //Sample Period count
int prev_millis=0;
float Ug = 1.00;          //Generator input
float Ud = 0.0;           //Dump load control signal
float Uk = 0.0;           //PI control signal
float delta_Uk = 0.0;     //incremental control signal 
float yk = 0.0;           //Current system output freq
float yk_1= 0.0;          //Previous system output freq
float fg = 0.0;           //Current generator output
float fg_1 = 0.0;         //Previous generator output
float fs = 0.0;           //Current system output freq
float fs_1= 0.0;          //Previous system output freq
float fd = 0.0;           //DL output 
float fc= 10.0;           //Consumer load rating
int CL_prd =200;          //consumer load period
float kp = 0.05;          //proportional gain
float ki = 0.01;          //integral gain
float ek=0.0;             //current error
float ek_1=0.0;           //previous error
float DL_w = -0.2;        //DL weight
int freq_ref=50;          //reference frequency
float V_const = 1.663;    //voltage conversion const
float I_const = 0.12;     //current conversion const
float V_line = 0.0;       //line-line output voltage
float I_DL =0.0;          //Dump load current
float i_RY_amps = 0;      //current in amps
float i_BR_amps = 0;      //current in amps
float i_YB_amps = 0;      //current in amps
//Wifi & MQTT variables
int max_timer = 360;      //maximum time in minutes
int mqtt_rt_set = 60;     //MQTT reconnect time preset (s)
int mqtt_rt_val = 0;      //MQTT reconnect timer value
int wifi_status;          //stores the WiFi connection status;
float time_on = 0;
int mqtt_pub_int = 0;     //mqtt data send interval
unsigned int exit_count = 0; //Idle settings exit counter

//MQTT WiFi Client
WiFiClient espClient;
PubSubClient client(mqtt_server, 1883, espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE  (50)
char msg[MSG_BUFFER_SIZE];
String msg_str = "";
char mqtt_msg[10];

void setup() {
  Serial.begin(57600);
  pinMode(led_pin, OUTPUT);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}
 
void loop(){
  client.loop();
  unsigned long cur_millis = millis();
  if (cur_millis - prev_millis > dT) 
  {
   prev_millis = cur_millis;
   prd_count++;
   mqtt_pub_int++;
   time_on = time_on + dT/1000.0; //(prd_count*dT)/1000;
   if (time_on > 999.0) time_on=0.0;  //reset the time
   Serial.println(prd_count); 
   ELC_model();                       //call the ELC freq model
  }
  if (mqtt_pub_int==5){
    sensor_data();
    if (client.connected() != 0){
      msg_str = String(fs);
      msg_str.toCharArray(mqtt_msg,10);
      client.publish("Freq", mqtt_msg); 
      msg_str = String(time_on);
      msg_str.toCharArray(mqtt_msg,10);
      Serial.print("Timer: ");
      Serial.println(mqtt_msg);
      client.publish("time_on", mqtt_msg);
      msg_str = String(i_RY_amps);
      msg_str.toCharArray(mqtt_msg,10);
      client.publish("R_amps", mqtt_msg);
      msg_str = String(i_BR_amps);
      msg_str.toCharArray(mqtt_msg,10);
      client.publish("Y_amps", mqtt_msg);
      msg_str = String(i_YB_amps);
      msg_str.toCharArray(mqtt_msg,10);
      client.publish("B_amps", mqtt_msg);
      msg_str = String(V_line);
      msg_str.toCharArray(mqtt_msg,10);
      client.publish("Volts", mqtt_msg); 
    }
    else
    {
      //Decrease MQTT timer and reconnect
      mqtt_rt_val--;
      Serial.println(mqtt_rt_val);
      if (mqtt_rt_val < 1) 
        {
          mqtt_rt_val=mqtt_rt_set;
          reconnect(); 
        }
    }
    mqtt_pub_int=0;
  }
  
//Simulate the consumer load
if (prd_count > CL_prd/2)
  {
    fc = 10;
    digitalWrite(led_pin, HIGH);
  }
if (prd_count > CL_prd)
  {
    fc = 0;
    prd_count=0;
    digitalWrite(led_pin, LOW);
  }
}

void ELC_model(){
  fg_1 = fg;                  //update the previous outptut
  fg = 0.905*fg_1 + 6.67*Ug;
  fs = fg-fd-fc;
//PI control algorithm 
  ek_1 = ek;                  //update the error
  ek = freq_ref - fs;
  delta_Uk = (kp+ki)*ek; 
  delta_Uk = delta_Uk -(kp*ek_1);
  Uk = Uk + delta_Uk;
  if (Uk > 0.0) Uk = 0.0;
  if (Uk < -2.0) Uk = -2.0;
  fd = Uk*DL_w*fg;             //weight Ud
}

void sensor_data(){
//Compute the line voltages and currents from the system model
  i_RY_amps = fd*I_const;        
  i_BR_amps = i_RY_amps + 0.1;
  i_YB_amps = i_RY_amps + 0.2;
  V_line = fs*V_const;          //system output voltage
  count++;
}

 // Connect to a WiFi network
void setup_wifi() {
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  int count = 0;
  while (WiFi.status() != WL_CONNECTED) 
  {
    count++;
    if (count>20) break;
    delay(250);
    Serial.println(WiFi.status());
    delay(250);
  }
  delay(500);
  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println(WiFi.status());
    Serial.println("");
    Serial.println("WiFi connected  ");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    delay(2000);
  }
 else
 {
  Serial.println("WiFi NOT connected!");
  delay(2000);
 }
}   // END WiFi setup////////////

void reconnect() {
// Connect to MQTT Broker
    Serial.println();
    Serial.print("WiFi Status: ");
    Serial.println(WiFi.status());
if (WiFi.status()!= 3) 
   {
    setup_wifi();
   }
else
   {
    Serial.println("Attempting MQTT connection...");
// Attempt to connect to MQTT
    if (client.connect(clientID, mqtt_username, mqtt_password)) 
      {
       Serial.println("connected");
       digitalWrite(led_pin, HIGH);
       delay(500);
       client.subscribe("LED");
      } 
    else
      {
        Serial.print("failed, rc=");
        Serial.println(client.state());
    // Wait 2 seconds before retrying
        delay(2000);
      }
   }    
}//END RECONNECT////////////////////


