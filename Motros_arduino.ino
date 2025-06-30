#define rpm1 6   // Motor1 RPM
#define fwd1 2   // Motor1 forward direction pin
#define rev1 4   // Motor1 reverse direction pin
#define rpm2 12  // Motor2 RPM
#define fwd2 3   // Motor2 forward direction pin
#define rev2 5   // Motor2 reverse direction pin
#define rpm3 7   // Motor3 RPM
#define fwd3 8   // Motor3 forward direction pin
#define rev3 10  // Motor3 reverse direction pin

// Improved global variables with more robust types
volatile float rpmValue1 = 0, rpmValue2 = 0, rpmValue3 = 0;
volatile float rpmValue1_f, rpmValue2_f, rpmValue3_f;
volatile int dirValue1 = 0, dirValue2 = 0, dirValue3 = 0;
const float m1 = 0.23, m2 = 0.23, m3 = 0.23; // SCALING FOR REDUCERS

// Variables for current measurement
const int currentPin1 = A0;  // Current sensing pin for Motor 1
const int currentPin2 = A2;  // Current sensing pin for Motor 2
const int currentPin3 = A4;  // Current sensing pin for Motor 3

unsigned long previousMillis = 0;
const long currentInterval = 10; // Interval for reading current (in milliseconds)

// Buffer for serial communication
const uint8_t MAX_BUFFER_LENGTH = 64;
char inputBuffer[MAX_BUFFER_LENGTH];
uint8_t bufferIndex = 0;

void setup() {
  // Configure motor control pins
  pinMode(rpm1, OUTPUT);
  pinMode(fwd1, OUTPUT);
  pinMode(rev1, OUTPUT);
  pinMode(rpm2, OUTPUT);
  pinMode(fwd2, OUTPUT);
  pinMode(rev2, OUTPUT);
  pinMode(rpm3, OUTPUT);
  pinMode(fwd3, OUTPUT);
  pinMode(rev3, OUTPUT);

  // Set current sensing pins as inputs
  pinMode(currentPin1, INPUT);
  pinMode(currentPin2, INPUT);
  pinMode(currentPin3, INPUT);

  // Initialize serial communication with larger buffer
  Serial.begin(115200);
  while (!Serial); // Wait for serial port to connect

  // Disable serial input buffering to prevent latency
  Serial.setTimeout(50);  // Set a short timeout

  // Print labels for Serial Plotter
  Serial.println("Motor1 Motor2 Motor3");

  // Optional: Initialize motors to a safe state
  stopAllMotors();
}

void stopAllMotors() {
  digitalWrite(fwd1, LOW);
  digitalWrite(rev1, LOW);
  digitalWrite(fwd2, LOW);
  digitalWrite(rev2, LOW);
  digitalWrite(fwd3, LOW);
  digitalWrite(rev3, LOW);
  analogWrite(rpm1, 0);
  analogWrite(rpm2, 0);
  analogWrite(rpm3, 0);
}

float processCurrentReading(int currentPin) {
  // Improved current reading with noise reduction
  float total = 0;
  const int numReadings = 5;
  
  for (int i = 0; i < numReadings; i++) {
    float FeedbackCurrent = analogRead(currentPin);
    float ActualFeedbackCurrent = (FeedbackCurrent * 5.0 / 1023.0) - 2.3;
    total += (ActualFeedbackCurrent != 0) ? 1000 * (ActualFeedbackCurrent * 0.0135) : 0;
    delay(1);  // Small delay between readings
  }
  
  return total / numReadings;
}

void parseSerialCommand() {
  // Tokenize the input buffer
  char* token = strtok(inputBuffer, " ");
  float values[6] = {0};
  int count = 0;

  // Parse numeric values safely
  while (token != NULL && count < 6) {
    values[count] = atof(token);
    token = strtok(NULL, " ");
    count++;
  }

  // Validate input
  if (count == 6) {
    rpmValue1 = values[0];
    dirValue1 = (int)values[1];
    rpmValue2 = values[2];
    dirValue2 = (int)values[3];
    rpmValue3 = values[4];
    dirValue3 = (int)values[5];

    // Apply scaling
    rpmValue1_f = (rpmValue1 / m1) / 1.1;
    rpmValue2_f = (rpmValue2 / m2) / 2.3;
    rpmValue3_f = (rpmValue3 / m3) / 1.5;

    controlMotors();
  } else {
    // Invalid command, stop motors
    stopAllMotors();
  }
}

void controlMotors() {
  if (rpmValue1_f == 0 && rpmValue2_f == 0 && rpmValue3_f == 0) {
    stopAllMotors();
  } else {
    // Motor 1
    analogWrite(rpm1, abs(rpmValue1_f));   
    digitalWrite(fwd1, dirValue1 == 0 ? HIGH : LOW);
    digitalWrite(rev1, dirValue1 == 0 ? LOW : HIGH);

    // Motor 2
    analogWrite(rpm2, abs(rpmValue2_f));
    digitalWrite(fwd2, dirValue2 == 0 ? HIGH : LOW);
    digitalWrite(rev2, dirValue2 == 0 ? LOW : HIGH);

    // Motor 3
    analogWrite(rpm3, abs(rpmValue3_f));  // abs for handling rpm values and directions separately
    digitalWrite(fwd3, dirValue3 == 0 ? HIGH : LOW);
    digitalWrite(rev3, dirValue3 == 0 ? LOW : HIGH);
  }
}

void loop() {
  unsigned long currentMillis = millis();

  // Non-blocking serial read
  while (Serial.available() > 0) {
    char inChar = Serial.read();
    
    // Check for newline or buffer overflow
    if (inChar == '\n' || bufferIndex >= MAX_BUFFER_LENGTH - 1) {
      inputBuffer[bufferIndex] = '\0';  // Null-terminate the string
      
      if (bufferIndex > 0) {
        parseSerialCommand();
      }
      
      bufferIndex = 0;  // Reset buffer
      break;
    }
    
    // Store character in buffer
    inputBuffer[bufferIndex++] = inChar;
  }

  // Continuously read and print current at a fixed interval
  if (currentMillis - previousMillis >= currentInterval) {
    previousMillis = currentMillis;

    // Read current for all motors
    float currentValue1 = processCurrentReading(currentPin1);
    float currentValue2 = processCurrentReading(currentPin2);
    float currentValue3 = processCurrentReading(currentPin3);

    // Print current values for Serial Plotter
    Serial.print(currentValue1, 2);
    Serial.print(" ");
    Serial.print(currentValue2, 2);
    Serial.print(" ");
    Serial.println(currentValue3, 2);
  }
}
