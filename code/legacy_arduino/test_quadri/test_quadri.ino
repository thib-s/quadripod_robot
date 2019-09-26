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
   indique l'amplitude pour lever et baisser les pates
   la hauteur des pates etant definie comme position au repos +- delta
   pas besoin de trop essayer de comprendre ce bout, ca viendra en lisant le code
*/
static int delta = 20;

/*
   le temps de temporisation entre chaque étape de la démarche
*/
static int temporisation_time = 125;

/*
   le tableau init_angles indique quel angles doivent prendre chaque servo au debut du programm
   (position de repos). On le lit de la manière suivante:
   angle de l'epaule avant droite = 90 degrees (servo 1, associe a la premiere case du tableau,
   cf commentaire surle tableau indexes)
   angle du coude avant droite = 120 degrees (seconde case du tableau)
   etc...
*/
int init_angles[] = {90, 90 + delta, 90, 90 - delta, 90, 90 - delta, 90, 90 + delta};

/*
   ce tableau permet d'jouter un offset sur les servomoteurs, cela permet de corriger les
   erreurs d'assemblage, ici, par ex, l'epaule arriere droite (servo 5) etait trop en arriere,
   d'ou une correction de 20 degrees
*/
int correction[] = { -10, 15, 10, 0,  20, 0, -10, -15};

typedef bool (*funcptr)();

struct command{
  funcptr func;
  String signature;
};

/*
   TODO doc sur la comm
*/

extern bool move_general(float, float);
extern bool set_delta(int);
extern bool tilt_body(int);
extern bool raise_body(int);
extern bool say_hi();
extern bool display_error();


#define INT 1000
#define FLOAT 1001

command MOVE = { &move_general, "ff"};
command SET_DELTA = { &set_delta, "i"};
command TILT_BODY = { &tilt_body, "i"};
command RAISE_BODY = { &raise_body, "i"};
command SAY_HI = { &say_hi, ""};
command FAILED_PARSING = { &display_error, ""};

funcptr func;
int int_params[2];
float float_params[2];
String str_param = "command failed";

String input_string = "";         // a String to hold incoming data
boolean command_refreshed = false;  // whether the string is complete

static int tilt = 0;
static int height = 0;

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
     pour pouvoir reflasher l'arduino (oui c'est très gitan, mais j'ai la flemme de graver un pcb pour
     la revB)
  */
  delay(5000);

  Serial.begin(1200);
  // reserve 200 bytes for the inputString:
  input_string.reserve(2000);
  // on alloue les pins, et on place les servos dans leurs positions initiales
  for (int i = 0; i < 8; i++) {
    servos[i].attach(indexes[i]);
    servos[i].write(init_angles[i] + correction[i]);
    // un petit delay est ajouté afin d'éviter que tous les servos bougent en même
    // temps, les alims, sont un peu limite pour l'usage qui en est fait ^^
    delay(temporisation_time);
  }
}

/*
   dans la loop on utilise a outrance la fonction move_general pour faire bouger le robot.
   Dans cetrte version, le robot fonctionne comme un automate ( pour l'instant )
   TODO: ajouter une lecture de commandes sur le serial pour pouvoir le piloter
*/
void loop()
{
  if (command_refreshed) {
    (*func)(); // call the function
    command_refreshed = false;
  } else {
//    Serial.println("doing nothing");
    perform_step(init_angles);
    delay(50);
  }
  /*
    if (Serial.find("set_delay(")) {
    int val = Serial.parseInt();
    Serial.print("set_delay(");
    Serial.print(val, DEC);
    Serial.println(")");
    }*/
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
extern bool move_general() {
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
  float linear = float_params[0];
  float angular = float_params[1];
  Serial.print("moving ");
  Serial.print(linear);
  Serial.print(",");
  Serial.println(angular);
  int angles_linear[4][8] = {
    {75,  90,       70, 90 - delta,  110, 90 - delta, 105, 90},
    {75,  90 + delta, 70, 90,        110, 90,       105, 90 + delta},
    {110, 90 + delta, 110, 90,       75,  90,       60,  90 + delta},
    {110, 90,       110, 90 - delta, 75,  90 - delta, 60,  90}
  };
  /*
     on fait de meme pour une demarche de rotation pure
      de la meme manière la rotation dans l'autre sens est obtenue en
      jouant la sequence a l"envers
  */
  int angles_angular[4][8] = {
    {110, 90,       70,  90 - delta,  75,  90 - delta, 105, 90},
    {110, 90 + delta, 70,  90,        75,  90,       105, 90 + delta},
    {75,  90 + delta, 110, 90,        110, 90,       60,  90 + delta},
    {75,  90,       110, 90 - delta,  110, 90 - delta, 60,  90}
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
    delay(temporisation_time);
  }
  return true;
}

extern bool say_hi() {
  Serial.println("saying hi");
  int angles_seq[6][8] = {
    {75,  90        , 90, 90 - delta, 90, 90 - delta, 90, 90 + delta},
    {40, 90        , 90, 90 - delta, 90, 90 - delta, 90, 90 + delta},
    {75,  90        , 90, 90 - delta, 90, 90 - delta, 90, 90 + delta},
    {40, 90        , 90, 90 - delta, 90, 90 - delta, 90, 90 + delta},
    {75,  90        , 90, 90 - delta, 90, 90 - delta, 90, 90 + delta},
    {90,  90 + delta, 90, 90 - delta, 90, 90 - delta, 90, 90 + delta}
  };
  // on joue sequentiellement chaque etape
  for (int act = 0; act < 6; act++) {
    // a chaque etape de la marche, on actualise tous les servos
    for (int serv = 0; serv < 8; serv++) {
      servos[serv].write(angles_seq[act][serv] + correction[serv]);
      delay(30);
    }
  }
  return true;
}


/*
   petite fonction qui permet d'appliquer une consigne a tous les servomoteurs
*/
void perform_step(int angles[]) {
  for (int i = 0; i < 8; i++) {
    servos[i].write(angles[i] + correction[i]);
  }
}

/*
   fonction pour changer le delta dynamiquement
   la nouvelle valeur doit être située dans l'intervalle [0, 120[
   renvoie true si la valeur a été changée, false si non
*/
extern bool set_delta() {
  int new_delta = int_params[0];
  Serial.print("setting delta ");
  Serial.println(new_delta);
  if ((new_delta >= 0) && (new_delta < 20)) {
    delta = new_delta;
    return true;
  }
  return false;
}

/**
   fonction pour changer le delai entre les étapes de la marche
   le delai doit être positif
   renvoie true si le delai a été changé, false si non
*/
extern bool set_tempo() {
  int new_tempo = int_params[0];
  Serial.print("setting tempo ");
  Serial.println(new_tempo);
  if (new_tempo > 0) {
    temporisation_time = new_tempo;
    return true;
  }
  return false;
}

/*
   fonction pour modifier la hauteur du corps lors de la demarche
   la variable amount correspond aux nombre de degrés ajoutés aux pates
   afin de faire monter le corps.
   amount peut etre positif (monter) ou négatif (descendre)
*/
extern bool raise_body() {
  int amount = int_params[0];
  Serial.print("raising body");
  Serial.println(amount);
  if (((height + amount) > 20) && ((height + amount) > -20)) {
    correction[1] += amount;
    correction[3] -= amount;
    correction[5] -= amount;
    correction[7] += amount;
    return true;
  } else {
    return false;
  }
}

extern bool tilt_body() {
  int amount = int_params[0];
  Serial.print("tilting body");
  Serial.println(amount);
  if (((height + amount) > 20) && ((height + amount) > -20)) {
    correction[1] += amount;
    correction[3] -= amount;
    correction[5] += amount;
    correction[7] -= amount;
    return true;
  } else {
    return false;
  }
}

extern bool display_error() {
  Serial.println(str_param);
}

/*
   Code from: https://www.arduino.cc/en/Tutorial/SerialEvent
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    input_string += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      refresh_command();
    }
  }
}

/*
 * this function find which function id is associed to the command string
 */
command get_command(){
  command result = FAILED_PARSING;
  input_string.trim();
  if ((input_string.startsWith("move(")) && (input_string.endsWith(")"))){
    result = MOVE;
  }
  if ((input_string.startsWith("set_delta(")) && (input_string.endsWith(")"))){
    result = SET_DELTA;
  }
  if ((input_string.startsWith("tilt_body(")) && (input_string.endsWith(")"))){
    result = TILT_BODY;
  }
  if ((input_string.startsWith("raise_body(")) && (input_string.endsWith(")"))){
    result = RAISE_BODY;
  }
  if ((input_string.startsWith("say_hi(")) && (input_string.endsWith(")"))){
    result = SAY_HI;
  }
  return result;
}

bool parse_param(int from, int param_no, char param_type){
  int result = false;
  switch (param_type){
    case 'f':
    float_params[param_no] = input_string.substring(from).toFloat();
    result = true;
    break;
    case 'i':
    int_params[param_no] = input_string.substring(from).toInt();
    result = true;
    break;
  }
  return result;
}

void refresh_command() {
  input_string.trim();
  // first we get the command to run
  command com = get_command();
  // second we get params type list and the position of the next param
  int count = com.signature.length();
  int next_param_index = input_string.indexOf('(') + 1;
  int offset = next_param_index;
  bool parse_success = true;
  for (int i = 0; i < count; i++)
  {
    if ((! parse_success) || ( offset == 0 )){
      // if the function returned false, it means that it failed to parse the params
      com = FAILED_PARSING;
      str_param = "unable to parse params for command";
      break;
    }
    // we parse params one by one
    parse_success = parse_param(next_param_index, i, com.signature[i]);
    offset = input_string.substring(next_param_index).indexOf(',') + 1;
    next_param_index = next_param_index + offset;
  }
  func = com.func;
  command_refreshed = true;
  // clear the string:
  input_string = "";
}
