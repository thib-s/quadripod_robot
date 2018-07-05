// code afin de tester la demarche du quadripod

#include <Servo.h>

// lien entre id du servo <=> numero de la pin associée
int indexes[] = {0,1,2,3,4,5,6,7};
Servo servos[8];  // tableau contenant les objet servos
// heureusement pour nous, un max de 8 objets servos peuvent etre crées


int init_angles[] = {90, 120, 90, 60, 90, 60, 90, 120};

void setup()
{
  for (int i = 0; i < 8; i++) {
    servos[i].attach(indexes[i]);
  }
  perform_step(init_angles);
  delay(2000);
}


void loop()
{
  for (int i = 0; i < 20; i++) {
    move_general(0.75, 0.5);
  }
  perform_step(init_angles);
  delay(1000);
  for (int i = 0; i < 5; i++) {
    move_general(0.5, 0.1);
  }
  perform_step(init_angles);
  delay(1000);
  for (int i = 0; i < 20; i++) {
    move_general(0.75, 0.5);
  }
  perform_step(init_angles);
  delay(1000);
  for (int i = 0; i < 20; i++) {
    move_general(0.75, 0.25);
  }
}

void move_general(float linear, float angular) {
  int angles_linear[4][8] = {
    {75, 90, 70, 30,  110, 30, 105, 90},
    {75, 150, 70, 90,  110, 90, 105, 150},
    {110, 150, 110, 90,  75, 90, 60, 150},
    {110, 90, 110, 30,  75, 30, 60, 90}
  };
  int angles_angular[4][8] = {
    {110, 90, 70, 30,  75, 30, 105, 90},
    {110, 150, 70, 90,  75, 90, 105, 150},
    {75, 150, 110, 90,  110, 90, 60, 150},
    {75, 90, 110, 30,  110, 30, 60, 90}
  };
  for (int act = 0; act < 4; act++) {
    for (int serv = 0; serv < 8; serv++) {
      float consigne_linear = linear * (float) angles_linear[act][serv] + (1 - linear) * (float) angles_linear[3 - act][serv];
      float consigne_angular = angular * (float) angles_angular[act][serv] + (1 - angular) * (float) angles_angular[3 - act][serv];
      servos[serv].write((int)(0.5 * consigne_linear + 0.5 * consigne_angular));
    }
    delay(250);
  }
}

void perform_step(int angles[]) {
  for (int i = 0; i < 8; i++) {
    servos[i].write(angles[i]);
  }
}

