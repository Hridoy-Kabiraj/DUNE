#include <Servo.h>

Servo myServo;
int servoPin = 9;
int ledRGBRedPin = 11;
int ledRGBBluePin = 6;
int motorPWM = 3;    // PWM pin for motor speed control

bool scramActive = false;
void setup(void){
  Serial.begin(9600);
  myServo.attach(servoPin);
  myServo.write(5);  //set default position
  pinMode(ledRGBRedPin, OUTPUT);
  pinMode(ledRGBBluePin, OUTPUT);
  analogWrite(ledRGBRedPin, 0);
  analogWrite(ledRGBBluePin, 0);
  
  // Initialize motor pin
  pinMode(motorPWM, OUTPUT);
  analogWrite(motorPWM, 0);   // Start with motor off
  
  loop();
}

void loop(void){
  int ledPowerSetting;
  int rodHeightSetting;
  int scramCondition;
  int motorSpeed;
  
  if (Serial.available() > 0)
  {
    char inByte = Serial.read();
    switch(inByte)
    {
    case 'p': //power
      // led glows blue (don't touch red if scram is active)
      ledPowerSetting = numberFromSerial();
      analogWrite(ledRGBBluePin, ledPowerSetting);
      // Map power (0-255) to motor speed (20-180)
      motorSpeed = map(ledPowerSetting, 0, 255, 20, 180);
      analogWrite(motorPWM, motorSpeed);
      break;
    case 'r': //rod position
      rodHeightSetting = numberFromSerial();
      myServo.write(rodHeightSetting);
      break;
    case 's': //scram condition
      // led glows red and stays on while scram is active
      scramCondition = numberFromSerial();
      Serial.print("SCRAM received: ");
      Serial.println(scramCondition);
      if (scramCondition > 0) {
        analogWrite(ledRGBRedPin, 255);
        scramActive = true;
      } else {
        analogWrite(ledRGBRedPin, 0);
        scramActive = false;
      }
      break;
    }
    Serial.flush();
  }
}
 
int numberFromSerial(void)
{
  char numberString[8];
  unsigned char index=0;
  delay(10);
  while(Serial.available() > 0)
  {
    delay(10);
    numberString[index++]=Serial.read();
    if(index>6)
    {
      break;
    }
  }
  numberString[index]=0;
  return atoi(numberString);
}
