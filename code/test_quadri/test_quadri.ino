/**
   code permettant de tester la demarche du quadripode
   par Thibaut Boissin
   github: thib-s
*/
#include <Servo.h>

/* le tableau indexes permet de faire le lien entre
   l'id du servo <=> numero de la pin associée
   le id des servo sont donné de la manière suivante:
   1: epaule avnt droite
   2: coude avant droit
   3: epaule avant gauche
   4: coude avant gauche
   5: epaule arriere droite
   6: coude arriere droite
   7: epaule arriere gauche
   8: coude arriere gauche

   ici, nous avons: le coude avant droit (servo numero 1, dans la premiere case du tableau)
   associe a la pin 9 de l'arduino
*/
int indexes[] = { 9, 4, 7, 2, 5, 8, 3, 6};

Servo servos[8];  // tableau contenant les objet servos
// heureusement pour nous, un max de 8 objets servos peuvent etre crées


/*
   le tableau init_angles indique quel angles doivent prendre chaque servo au debut du programm
   (position de repos). On le lit de la manière suivante:
   angle de l'epaule avant droite = 90 degrees (servo 1, associe a la premiere case du tableau,
   cf commentaire surle tableau indexes)
   angle du coude avant droite = 120 degrees (seconde case du tableau)
   etc...
*/
int init_angles[] = {90, 120, 90, 60, 90, 60, 90, 120};

/*
   ce tableau permet d'jouter un offset sur les servomoteurs, cela permet de corriger les
   erreurs d'assemblage, ici, par ex, l'epaule arriere droite (servo 5) etait trop en arriere,
   d'ou une correction de 20 degrees
*/
int correction[] = { -10, 10, 10, -10,  20, -10, -10, 10};

/*
   au setup, on alloue les pin aux servos, et on donne au quadripod sa position initiale
*/
void setup()
{
  /*
     un petit delay a été mis au début, cela vient d'un soucis sur la revA de la carte
     sur la revA, il n'y a pas de diodes entre le 5V et l'étage d'alim, le 5v de l'arduino
     alimente donc indirectement les servos, et l'arduino se retrouve sous alimenté quand
     les servos bougent, rendant la reprogrammation impossible. Ce delay laisse donc un laps de temps
     pour pouvoir reflasher l'arduino (oui c'esttrès gitan, mais j'ai la flemme de fraver un pcb pour
     la revB)
  */
  delay(1000);
  // on alloue les pins, et on place les servos dans leurs positions initiales
  for (int i = 0; i < 8; i++) {
    servos[i].attach(indexes[i]);
    servos[i].write(init_angles[i]);
    // un petit delay est ajouté afin d'éviter que tous les servos bougent en même
    // temps, les alims, sont un peu limite pour l'usage qui en est fait ^^
    delay(250);
  }
}

/*
   dans la loop on utilise a outrance la fonction move_general pour faire bouger le robot.
   Dans cetrte version, le robot fonctionne comme un automate ( pour l'instant )
   TODO: ajouter une lecture de commandes sur le serial pour pouvoir le piloter
*/
void loop()
{
  // et 20 pas en avant!
  for (int i = 0; i < 20; i++) {
    move_general(0.75, 0.5);
  }
  perform_step(init_angles);
  delay(1000);
  //et 5 pas sur le coté!
  for (int i = 0; i < 5; i++) {
    move_general(0.5, 0.1);
  }
  perform_step(init_angles);
  delay(1000);
  // il etait un robot, qui essayait d'marcher
  for (int i = 0; i < 20; i++) {
    move_general(0.75, 0.5);
  }
  perform_step(init_angles);
  delay(1000);
  // il chantait haut et fort, qu'il n'allait pas griller
  for (int i = 0; i < 20; i++) {
    move_general(0.75, 0.25);
  }
}

/*
   fonction qui permet de faire un deplacement
   on lui donne deux paramêtres:
   float linear: vitesse lineaire du robot
                 c'est un valeur entre 0 et 1
                 a 0 on recule, et 1 on avance, 0.5, sur place
   float angular: vitesse angular du robot
                  valeur entre 0 et 1
                  a 0 rotation sens trigo, a 1 rotation sens horaire, a 0.5 pas de rotation
   il est bien sur possible de combiner les deux pour avancer en tournant!
   le robot est donc quasi holonome. ;)
*/
void move_general(float linear, float angular) {
  /*
     comment ca marche la dedans ? on a une sequence de positions préenregistrées
     pour une marche en ligne droite dans la matrice suivante
     chaque colonne correspond a un servo, chaque ligne correspond à une étape de la marche
     on a donc un demarche en quatre etape:
     pour chaque pate:
        1. lever la pate
        2. avance la pate
        3. poser la pate
        4. reculer la pate

     la marche arrière est obtenue en jouant la sequence a l'envers
  */
  int angles_linear[4][8] = {
    {75, 90, 70, 30,  110, 30, 105, 90},
    {75, 150, 70, 90,  110, 90, 105, 150},
    {110, 150, 110, 90,  75, 90, 60, 150},
    {110, 90, 110, 30,  75, 30, 60, 90}
  };
  /*
     on fait de meme pour une demarche de rotation pure
      de la meme manière la rotation dans l'autre sens est obtenue en
      jouant la sequence a l"envers
  */
  int angles_angular[4][8] = {
    {110, 90, 70, 30,  75, 30, 105, 90},
    {110, 150, 70, 90,  75, 90, 105, 150},
    {75, 150, 110, 90,  110, 90, 60, 150},
    {75, 90, 110, 30,  110, 30, 60, 90}
  };
  // on joue sequentiellement chaque etape de la marche
  for (int act = 0; act < 4; act++) {
    // a chaque etape de la marche, on actualise tous les servos
    for (int serv = 0; serv < 8; serv++) {
      /*
         la demarche en ligne droite est calculé en combinant de manière pondérée les demarche de marche
         avant et de marche arrière, si linear vaut 0.5, le deux se compensent et le robot fait du sur place

         la demarche obtenue permet d'avance ou de reculer a n'importe quelle vitesse
      */
      float consigne_linear =
        linear * (float) angles_linear[act][serv]
        + (1 - linear) * (float) angles_linear[3 - act][serv];
      /*
         de la meme maniere la demarche angulaire est calculée

         la demarche obtenue permet de tourner dans les deux sens a n'importe quelle vitesse
      */
      float consigne_angular =
        angular * (float) angles_angular[act][serv]
        + (1 - angular) * (float) angles_angular[3 - act][serv];
      /*
         finalement on combine les demarches lineaire et angulaire pour obtenir la demarche generale
         la demarche obtenue permet d'avancer/reculer tout en tournant
      */
      servos[serv].write((int)(0.5 * consigne_linear + 0.5 * consigne_angular + correction[serv]));
    }
    // un delay est ajouter le temps que tous les servos aient atteint leur consigne
    // attention a ne pas trop le diminuer, en plus de ne plus atteindre les consignes
    // cela pomperait beaucoup de courant sur des alimentations qui sont déjà limite
    // sorry je suis pas très bon en électronique ^^
    delay(250);
  }
}


/*
   petite fonction qui permet d'appliquer une consigne a tous les servomoteurs
*/
void perform_step(int angles[]) {
  for (int i = 0; i < 8; i++) {
    servos[i].write(angles[i] + correction[i]);
  }
}

