// code afin de tester la demarche du quadripod

#include <Servo.h>

// lien entre id du servo <=> numero de la pin associée
int indexes[] = {0,1,2,3,4,5,6,7};
Servo servos[8];  // tableau contenant les objet servos
// heureusement pour nous, un max de 8 objets servos peuvent etre crées


int init_angles[] = {90, 90, 90, 60, 90, 60, 90, 90};

void setup()
{
  for (int i = 0; i < 8; i++) {
    servos[i].attach(indexes[i]);
  }
  perform_step(init_angles);
}


void loop()
{
}

void perform_step(int angles[]) {
  for (int i = 0; i < 8; i++) {
    servos[i].write(angles[i]);
  }
}

