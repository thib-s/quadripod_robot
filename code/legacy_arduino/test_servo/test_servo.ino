// ce code permet de bien placer les servo lors du montage du robot

#include <Servo.h>

// lien entre id du servo <=> numero de la pin associée
int indexes[] = { 9, 4, 7, 2, 5, 8, 3, 6};
Servo servos[8];  // tableau contenant les objet servos
// heureusement pour nous, un max de 8 objets servos peuvent etre crées


int init_angles[] = {90, 90, 90, 90, 90, 90, 90, 90};
int correction[] = { -10, 0, 10, 0,  20, 0, -10, 0};

void setup()
{
  delay(5000);
  for (int i = 0; i < 8; i++) {
    servos[i].attach(indexes[i]);
  }
}


void loop()
{
  for (int i = 0; i < 8; i++) {
    servos[i].write(init_angles[i] + correction[i]);
    delay(1000);
  }
}

void perform_step(int angles[]) {
  for (int i = 0; i < 8; i++) {
    servos[i].write(angles[i]);
  }
}

