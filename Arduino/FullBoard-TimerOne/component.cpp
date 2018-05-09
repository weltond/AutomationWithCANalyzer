/*****************************************************************/
// component.cpp
// Alexander Swantek
// aswantek@ford.com
// 02/09/2017
// 
// Implementation for the class declared in component.h

/*****************************************************************/

#include "Arduino.h"
#include "component.h"

/*****************************************************************/

Component::Component()
{
 
}

/*****************************************************************/

void Component::setBounds(int index, int numRelays)
{
  indexBegin = index;
  len = numRelays; 
}

/*****************************************************************/

int Component::getIndex()
{
  return indexBegin;  
}

/*****************************************************************/

int Component::getLen()
{
  return len;
}

/*****************************************************************/

int Component::getRelay(STATE state, int index)
{
  switch(state)
  {
    case NORMAL:
    {
      return _normal.r[index];
      break;  
    }
    case PRESS:
    {
      return _press.r[index];
      break;
    }
    case VBATT:
    {
      return _vbatt.r[index];
      break;
    }
    case GROUND:
    {
      return _ground.r[index];
      break;
    }
    case OPEN:
    {
      return _open.r[index];
      break;
    }
    case LEADTOLEAD:
    {
      return _leadTolead.r[index];
      break;
    }
    default:
    {
      return -1;
      break;
    }
  } 
}

/*****************************************************************/
void Component::set(STATE state, int r1, int r2, int r3, int r4)
{
  // Switches on the desired state to set the relay positions for 
  //    that desired state
  switch(state)
  {
    case NORMAL:
    {
      setStates(_normal, r1, r2, r3, r4);
      break;  
    }
    case PRESS:
    {
      setStates(_press, r1, r2, r3, r4);
      break;
    }
    case VBATT:
    {
      setStates(_vbatt, r1, r2, r3, r4);
      break;
    }
    case GROUND:
    {
      setStates(_ground, r1, r2, r3, r4);
      break;
    }
    case OPEN:
    {
      setStates(_open, r1, r2, r3, r4);
      break;
    }
    case LEADTOLEAD:
    {
      setStates(_leadTolead, r1, r2, r3, r4);
      break;
    }
    default:
    {
      break;
    }
  }  
}

/*****************************************************************/

void Component::setStates(RelayStates &state, int r1, int r2, int r3, int r4)
{
  state.r[0] = r1;
  state.r[1] = r2;
  state.r[2] = r3;
  state.r[3] = r4;
}

/*****************************************************************/

Board::Board()
{
    _switch.setBounds(3,4);
    si.setBounds(1,3);
    mic.setBounds(7,3);
    ls.setBounds(12,4);
    rs.setBounds(10,4);
    pwr.setBounds(0,1);
    ens.setBounds(-1,0);  

    _switch.set(NORMAL, 0, 0, 0, 0);
    _switch.set(PRESS, 0, 1, 0, 0);
    _switch.set(OPEN, 0, 0, 1, 1);
    _switch.set(GROUND, 0, 0, 0, 1);
    _switch.set(VBATT, 1, 0, 0, 1);

    si.set(NORMAL, 0, 0, 0);
    si.set(OPEN, 1, 1, 0);
    si.set(GROUND, 1, 0, 0);
    si.set(VBATT, 1, 0, 1);    

    mic.set(NORMAL, 0, 0, 0);
    mic.set(OPEN, 0, 1, 1);
    mic.set(GROUND, 0, 0, 1);
    mic.set(VBATT, 1, 0, 1);   

    ls.set(NORMAL, 0, 0, 0, 0);
    ls.set(LEADTOLEAD, 0, 0, 1, 1);
    ls.set(OPEN, 0, 1, 0, 1);
    ls.set(GROUND, 0, 0, 0, 1);
    ls.set(VBATT, 1, 0, 0, 1);

    rs.set(NORMAL, 0, 0, 0, 0);
    rs.set(LEADTOLEAD, 1, 1, 0, 0);
    rs.set(OPEN, 1, 0, 1, 0);
    rs.set(GROUND, 1, 0, 0, 0);
    rs.set(VBATT, 1, 0, 0, 1);

    pwr.set(NORMAL, 0);
    pwr.set(OPEN, 1);            
}

/*****************************************************************/

void Board::makeBoard()
{
  Board();
}

/*****************************************************************/

void Board::calcBytes()
{
  byte11 = 0;
  byte12 = 0;
  byte21 = 0;
  byte22 = 0;
  
  for(int i = 0; i < 16; i++)
  {
    if (i < 4)
    {
      byte11 += relays[i] * binaries[(i % 4)];
    }
    else if (i < 8)
    {
      byte12 += relays[i] * binaries[(i % 4)];
    }
    else if (i < 12)
    {
      byte21 += relays[i] * binaries[(i % 4)];
    }
    else
    {
      byte22 += relays[i] * binaries[(i % 4)];     
    }   
  }  
}

void Board::writeUpdate(Component &component, STATE state)
{
  int index = component.getIndex();
  int len = component.getLen(); 
  
  for(int i = 0; i < len; i++)
  {
    relays[i + index] = component.getRelay(state, i);
  }  
}

void Board::updateBoard(COMPONENT component, STATE state)
{
  switch(component)
  {
    case SWITCH:
    {
      writeUpdate(_switch, state);
      break;
    }
    case SI:
    {
      writeUpdate(si, state);
      break;
    }
    case MIC:
    {
      writeUpdate(mic, state);
      break;
    }
    case LS:
    {
      writeUpdate(ls, state);
      break;
    }
    case RS:
    {
      writeUpdate(rs, state);
      break;
    }
    case PWR:
    {
      writeUpdate(pwr, state);
      break;
    }
    default:
    {
      break;
    }    
  }

  calcBytes();    
}

/*****************************************************************/

void Board::getWriteBytes(byte &d1b1, byte &d1b2, byte &d2b1, byte &d2b2)
{     
  d1b1 = byte11;
  d1b2 = byte12;
  d2b1 = byte21;
  d2b2 = byte22;
}

/*****************************************************************/

void Board::reset()
{
  String old = "";
  String _new = "";
  for(int i = 0; i < 16; i++)
  {
    old += relays[i];
    relays[i] = 0;
    _new += relays[i];
  }
  Serial.println(old);
  Serial.println(_new);
  
  byte11 = 0;
  byte12 = 0;
  byte21 = 0;
  byte22 = 0;
}

/*****************************************************************/
void Board::printStatus(String &currentStatus)
{  
  currentStatus += relays[0];
  currentStatus += "...";
  
  currentStatus =+ "\n";

  currentStatus += "Bytes: ";
  currentStatus += byte11;
  currentStatus += "-";
  currentStatus += byte12;
  currentStatus += "-";
  currentStatus += byte21;
  currentStatus += "-";
  currentStatus += byte22;
  currentStatus += "\n";
}





