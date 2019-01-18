/*****************************************************************/
// FullSwitch
// 02/09/2017
// 
// Implementation for arduino to control relays for eCall fault
//    simulation  
// Utilizes the custom classes declared in component.h and defined
//    in component.h
// Reads serial input from a control program, parses the input,
//    and responds accordingly. This program handles the serial
//    parsinga and control

#include "component.h"
//Include SPI library

#include <SPI.h>

#include <TimerOne.h>


/*****************************************************************/
// Defines the constants to be used in pin selection

#define ENS 7 // ENS Transistor pin
#define ENABLE 8  // Global enable for each driver
#define DRIVER1 9 // SPI slave select for Driver 1
#define DRIVER2 10  // SPI slave select for Driver 2

Board board;


// Need to write teh EN pin HIGH to start and reset everything

void reset()
{
  pinMode(ENABLE, OUTPUT);
  digitalWrite(ENABLE, LOW);
  delay(100);
  digitalWrite(ENABLE, HIGH);

  delay(100);
}

/*****************************************************************/
// One time setup for the arduino. It declares the pin states on
//    the board, sets them to their default setting and opens a 
//    serial connection. It also sets the states of all currently
//    declared components based on their circuit design


SPISettings settings(5000000, MSBFIRST, SPI_MODE1);

void setup() {
  // put your setup code here, to run once:
  pinMode(DRIVER1, OUTPUT);
  pinMode(DRIVER2, OUTPUT);
  reset();

  pinMode(ENS, OUTPUT);
  digitalWrite(ENS, LOW);

  // initialize timerOne
  Timer1.initialize(1000);    // 1000 um = 1 ms over flow rate
  Timer1.attachInterrupt(ensSignal);

  SPI.begin();

  board.makeBoard();
  
  Serial.begin(9600);
  while(!Serial)
  {
    ; // Wait for port to connect
  }
  Serial.println("Connected");  
}

/*****************************************************************/
// Nomral - Continuous 10 Hz --> 50 ms High, 50 ms Low
// Deployment - Continuous 250 Hz --> 2 ms High, 2 ms Low
// Fuel Cutoff - Alternate 500 Hz and 250 Hz 5x each --> (1 ms High, 1 ms Low) x 5 and (2 ms High, 2 ms Low) x 5
// Pass Through - Pin Low
// Short to Ground - Pin High

int ticks = 0;
int freq[2] = {1,2};
int normFreq = 50;
int deploy = 0;
bool swap = false;
bool ENS_Timer_On = false;
bool fuelcutoff = false;
bool deployment = false;

// interrupt service routine that wraps a user defined function 
// supplied by attachInterrupt

void ensSignal()        
{
  if(ENS_Timer_On)
  {
    ++ticks;
    if(fuelcutoff)
    {
      if(deploy > 10)
      {
        swap = !swap;
        deploy = 0;
      }
      
      if(ticks >= freq[swap])
      {
        digitalWrite(ENS, digitalRead(ENS) ^ 1);
        ticks = 0;
        ++deploy;
      }
    }
    else if(deployment)
    {
      if(ticks >= freq[1])
      {
         digitalWrite(ENS, digitalRead(ENS) ^ 1);
         ticks = 0;         
      }
    }
    else
    {          
      if(ticks >= normFreq)
      {
        digitalWrite(ENS, digitalRead(ENS) ^ 1);
        ticks = 0;
      }
    }
  }
}


/*
ISR(TIMER1_OVF_vect)        
{
  TCNT1 = 65411;            // preload timer
      
  if(ENS_Timer_On)
  {
    ++ticks;
    if(fuelcutoff)
    {
      if(deploy > 10)
      {
        swap = !swap;
        deploy = 0;
      }
      
      if(ticks >= freq[swap])
      {
        digitalWrite(ENS, digitalRead(ENS) ^ 1);
        ticks = 0;
        ++deploy;
      }       
    } else
    {
      if(ticks >= normFreq)
      {
        digitalWrite(ENS, digitalRead(ENS) ^ 1);
        ticks = 0;
      }
    }
  }
}
*/
//This will turn the output on 
void writeState(byte byte11, byte byte12, byte byte21, byte byte22)
{  
  SPI.beginTransaction(settings);
  
  digitalWrite(DRIVER2, LOW);
  SPI.transfer(byte22);
  SPI.transfer(byte21);
  digitalWrite(DRIVER2, HIGH);
    
  digitalWrite(DRIVER1, LOW);
  SPI.transfer(byte12);
  SPI.transfer(byte11);
  digitalWrite(DRIVER1, HIGH);

  SPI.endTransaction();
  
  Serial.print(byte11); Serial.print("-"); Serial.print(byte12); Serial.print("-");
  Serial.print(byte21); Serial.print("-"); Serial.println(byte22);
}

/*****************************************************************/
// Variables to be used throughout each serial communicaiton
  
String _input;

String _component = "";
String _state = "";
STATE _stateENUM;
bool _sequence = false;
int _t1 = -1;
int _t2 = -1;
int _t3 = -1;
int _t4 = -1;
int t[4] = {-1,-1,-1,-1};

bool newCommand = false;

byte b11 = 0;
byte b12 = 0;
byte b21 = 0;
byte b22 = 0;

/*****************************************************************/

unsigned long currentTime;
unsigned long previousTime;
bool inSequence = false;

String _seqComp = "";

int _seqIndex = 0;
COMPONENT _seqCompENUM = SWITCH;
STATE states[2] = {NORMAL, NORMAL};

/*****************************************************************/
// "Main" how it controls the whole arduino loop
// Checks to see if new serial data is available, then it will 
//    grab the input, parse the input by calling _parseInput()
//    then, if it is a new command, it will execute either a 
//    command send or a sequence command based on the input

void loop() {
  // put your main code here, to run repeatedly:   
  
  if(inSequence and _seqIndex < 4)
  {
    if(_seqIndex == 3)
    {
      inSequence = false;
    }
    else 
    {
      currentTime = millis();
      if(currentTime - previousTime >= t[_seqIndex])
      {
        _seqIndex++;
        triggerSequence(_seqCompENUM);
        previousTime = currentTime;
      }
    }
  }
  
  if(Serial.available() > 0)
  {
      _input = Serial.readString();
      //Serial.print("Received: ");
      //Serial.println(_input);

      _parseInput();
  }
  
  // Determine, if it is a new command, which to send
  if(newCommand)
  {
    String current;
    if(_sequence and !inSequence)
    {
      inSequence = true;
      _seqIndex = 0;
      _seqComp = _component;
  
      states[0] = NORMAL;
      states[1] = NORMAL;
      
      if(_seqComp == "Switch")
      {
        _seqCompENUM = SWITCH;
        states[0] = _stateENUM;
      }
      else
      {
        _seqCompENUM = PWR;
        if(_stateENUM == NORMAL)
          states[1] = OPEN;
        else 
          states[0] = _stateENUM;
      }
        
      previousTime = millis();

      triggerSequence(_seqCompENUM);
      newCommand = false;
    }
    else
    {
      sendCommand(); 
      board.printStatus(current);
      Serial.println(current); 
      Serial.println("Done");
    }
  }

  // Resets the command status to default "no new data" after 
  //  executing
  newCommand = false;
}

/*****************************************************************/
// Function for parsing the input read in from the serial port in 
//    in the main loop. It parses the input commands based on the
//    API defined in faultcommands.txt
//    It parses the input by looking for the "-" separating the 
//    input pieces by calling getInputPiece helper function.
//    The function will send back what it received after parsing
//    the data to insure it was properly received/sent
 
void _parseInput()
{
  // Command Examples
  // Switch-Press-0-150-0-0-0
  
  int _delimIndex = 0;
  int _begin = 0;

  _component = getInputPiece(_begin, _delimIndex);
  if(_component == "Reset")
  {
    Serial.println("Reset");
    newCommand = true;
    return;
  }
  _state = getInputPiece(_begin, _delimIndex);
  if(_component == "ENS")
  {
    Serial.println("Received: " + _component + "_" + _state);
    newCommand = true;
    convertState(_state);
    return;
  }
  
  _sequence = getInputPiece(_begin, _delimIndex).toInt();
  if(_sequence)
  {
    t[0] = _t1 = getInputPiece(_begin, _delimIndex).toInt();
    t[1] = _t2 = getInputPiece(_begin, _delimIndex).toInt();
    t[2] = _t3 = getInputPiece(_begin, _delimIndex).toInt();
    t[3] = _t4 = getInputPiece(_begin, _delimIndex).toInt();       
  }  

  // Prints the command back to the driver program to ensure accuracy and tracability
  Serial.println("Received: " + _component + "_" + _state + "_" + _sequence + "_" + _t1 + "_" + _t2 + "_" + _t3 + "_" + _t4);

  convertState(_state);
  
  newCommand = true;
}

/*****************************************************************/

// Helper funciton to _parseInput to parse by looking for the "-"
//  separating the input commands
String getInputPiece(int &start, int &delim)
{
  String _piece = "";
  
  delim = _input.indexOf('-', start);
  _piece = _input.substring(start, delim); // Get Component
  //Serial.println(_piece);
  start = ++delim;
  delim = _input.indexOf('-', delim);

  return _piece;
}

/****************************************************************/
void convertState(String &state)
{
  if(state == "Normal")
  {
      _stateENUM = NORMAL;
  }
  else if(state == "Press")
  {
      _stateENUM = PRESS;    
  }
  else if(state == "VBATT")
  {
      _stateENUM = VBATT;    
  }
  else if(state == "Ground")
  {
      _stateENUM = GROUND;    
  }  
  else if(state == "Open")
  {
      _stateENUM = OPEN;    
  }
  else if(state == "LeadToLead")
  {
      _stateENUM = LEADTOLEAD;    
  }
  else if(state == "Pass")
  {
      _stateENUM = PASS; 
  }
  else if(state == "Cutoff")
  {
      _stateENUM = CUTOFF;  
  }
  else if(state = "Deploy")
  {
      _stateENUM = DEPLOY;
  }
}

/*****************************************************************/
void triggerSequence(COMPONENT component)
{  
  board.updateBoard(component, states[_seqIndex % 2]);
  board.getWriteBytes(b11, b12, b21, b22);
  writeState(b11, b12, b21, b22); 
}

/*****************************************************************/

// Sennds a command sequence by calling the component's member
//    funciton triggerSequence based on the name of the component
//    being tested. Resets "newCommand" to false after executing

void sendSequence()
{  
  newCommand = false;
}

/*****************************************************************/

// Sennds a command by calling the component's member funciton 
//    triggerRelay based on the name of the component.
//    Resets "newCommand" to false after executing

void sendCommand()
{
  if(_component == "Switch")
  {
    board.updateBoard(SWITCH, _stateENUM); 
  }
  else if(_component == "LSpeaker")
  {
    board.updateBoard(LS, _stateENUM);    
  }
  else if(_component == "RSpeaker")
  {
    board.updateBoard(RS, _stateENUM);    
  }
  else if(_component == "StatusIndc")
  {
    board.updateBoard(SI, _stateENUM);    
  }
  else if(_component == "Mic")
  {
    board.updateBoard(MIC, _stateENUM);    
  }  
  else if(_component == "Power")
  {
    board.updateBoard(PWR, _stateENUM);    
  } 
  else if(_component == "ENS")
  {
    Serial.println("ENS COMMAND");
    Serial.print("Pass:");
    Serial.print(PASS);
    Serial.print("\tGround: ");
    Serial.println(GROUND);
    Serial.println(_stateENUM);
    
    noInterrupts();
    switch(_stateENUM)
    {
      case PASS:
      {       
        ENS_Timer_On = false;
        fuelcutoff = false;
        deployment = false;
        digitalWrite(ENS, LOW);
        Serial.println("ENS OFF");
        break;
      }
      case GROUND:
      {
        ENS_Timer_On = false;
        fuelcutoff = false;
        deployment = false;        
        digitalWrite(ENS, HIGH);
        Serial.println("ENS ON");
        break;
      }      
      case NORMAL:
      {       
        ENS_Timer_On = true;
        fuelcutoff = false;
        deployment = false;        
        break;
      }
      case CUTOFF:
      {
        ENS_Timer_On = true;
        fuelcutoff = true;
        deployment = false;        
        break;
      }
      case DEPLOY:
      {
        ENS_Timer_On = true;
        fuelcutoff = false;
        deployment = true;        
        break;
      }
    }
    interrupts();
    newCommand = false;
    return;
  }
  else if(_component == "Reset")
  {
    board.reset(); 
    noInterrupts(); 
    ENS_Timer_On = false;
    fuelcutoff = false;
    deployment = false;
    digitalWrite(ENS, LOW); 
    interrupts();
  }
  
  board.getWriteBytes(b11, b12, b21, b22);
  writeState(b11, b12, b21, b22);
    
  newCommand = false;
}

/*****************************************************************/

// Retruns the desired state of the component being tested. The 
//    states are defined in component.h

STATE getState()
{
  if(_state == "Normal")
    return NORMAL;
  if(_state == "Press")
    return PRESS;
  if(_state == "VBATT")
    return VBATT;
  if(_state == "Ground")
    return GROUND;
  if(_state == "Open")
    return OPEN;
  if(_state == "LeadToLead")
    return LEADTOLEAD;
  if(_state == "Pass")
    return PASS;
  if(_state == "Cutoff")
    return CUTOFF;
  if(_state == "Deploy")
    return DEPLOY;
}

/*****************************************************************/




