/*****************************************************************/
// component.h
// Alexander Swantek
// aswantek@ford.com
// 02/09/2017
// 
// Header function declaring the component class used to simulate
//    eCall faults and other components used in that class

/*****************************************************************/

#ifndef COMPONENT_H
#define COMPONENT_H

#include "arduino.h"

using namespace std;


/*****************************************************************/
// And enum dfining the available components.

enum COMPONENT {SWITCH, SI, MIC, LS, RS, PWR, ENS};


/*****************************************************************/
// And enum dfining what the different states are for the
//    defferent possible components.

enum STATE {NORMAL, PRESS, VBATT, GROUND, OPEN, LEADTOLEAD, PASS, CUTOFF, DEPLOY};

/*****************************************************************/
// RelayStates struct is used to dfine whether a given relay should
//    be powered or not to reach a certain outcome/fault. This is 
//    used within the component class.

struct RelayStates
{
  int r[4] = {0,0,0,0};
};

/*****************************************************************/
// The component class is used to represent an eCall component 
//    (button/Switch, L/R Speakers, Status Indicator, and 
//    microphone).

class Component
{
  public:
    // Default constructor, used to set the relay's pin assignemnts
    Component();

    // Set Parameters for the binary array
    void setBounds(int index, int numRelays);
    
    // Sets the relay positions for a desired state
    void set(STATE state, int r1 = -1, int r2 = -1, int r3 = -1, int r4 = -1);

    int getIndex();
    int getLen();

    int getRelay(STATE state, int index);
      
  private:
    // Used by the public set function to set the relay position for a desired
    //    fault or action to be used when triggered
    void setStates(RelayStates &state, int r1, int r2, int r3, int r4); 
  
    // These structs define the relay state combinations for the different
    //    actions/faults desired
    RelayStates _normal;
    RelayStates _press;
    RelayStates _vbatt;
    RelayStates _ground;
    RelayStates _open;
    RelayStates _leadTolead;


    int indexBegin;
    int len;
    
    // The lag is the itme it takes for the relays to activate, 3ms in
    //    this case
    int _lag = 3;
};


/*****************************************************************/
// The baord class is used to represent teh eCall board 
// 

class Board
{
  public:
    // Default constructor, used to set the board's states
    Board();

    void makeBoard();
    
    void updateBoard(COMPONENT component, STATE state);
 
    void getWriteBytes(byte &d1b1, byte &d1b2, byte &d2b1, byte &d2d2);

    void printStatus(String &currentStatus);
    
    void reset();
    
  private:
    void calcBytes();
    void writeUpdate(Component &component, STATE state);
    
    Component _switch;
    Component si;
    Component mic;
    Component ls;
    Component rs;
    Component pwr;
    Component ens;

    int relays[16] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
    int binaries[4] = {2,8,32,128};
    int byte11 = 0;
    int byte12 = 0;
    int byte21 = 0;
    int byte22 = 0;
    
};

#endif
