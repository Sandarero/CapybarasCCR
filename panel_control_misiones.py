from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task


#   CONFIGURACIÓN DEL ROBOT

hub = PrimeHub()

# Motores de las ruedas motrices (mueven el robot por la mesa)
left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.B, Direction.CLOCKWISE)

# Motores de misión (attachments) - los que hacen las acciones de las misiones
motor_C = Motor(Port.C)
motor_D = Motor(Port.D)

wheel_diameter = 62
axle_track = 150

robot = DriveBase(left_motor, right_motor, wheel_diameter, axle_track)
robot.use_gyro(True)


#   FUNCIONES DE MOVIMIENTO DEL ROBOT (ruedas A/B)

def avanzar(distancia_mm, velocidad, aceleracion):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    robot.straight(distancia_mm)

def retroceder(distancia_mm, velocidad, aceleracion):
    avanzar(-distancia_mm, velocidad, aceleracion)

def girar(angulo, velocidad_giro=250):
    robot.settings(turn_rate=velocidad_giro)
    robot.turn(angulo)

def girar_alrededor(velocidad_izq, velocidad_der, angulo_objetivo, margen_error=2):
    robot.use_gyro(False)               # soltar el gyro para uso manual
    hub.imu.reset_heading(0)
    left_motor.run(velocidad_izq)
    right_motor.run(velocidad_der)

    signo = 1 if angulo_objetivo > 0 else -1
    while True:
        angulo_actual = hub.imu.heading()
        if signo * angulo_actual >= signo * angulo_objetivo - margen_error:
            break
        wait(10)

    left_motor.stop()
    right_motor.stop()
    robot.use_gyro(True)                # devolverle el gyro al DriveBase


#   FUNCIONES DE MOTORES DE MISIÓN (C y D)

def mover_motor_C(velocidad, angulo):
    motor_C.run_angle(velocidad, angulo)

def mover_motor_D(velocidad, angulo):
    motor_D.run_angle(velocidad, angulo)

async def _mover_juntos(velocidad_C, angulo_C, velocidad_D, angulo_D):
    await multitask(
        motor_C.run_angle(velocidad_C, angulo_C),
        motor_D.run_angle(velocidad_D, angulo_D)
    )

# Correr este, el anterior es solo una definición
def mover_motores_juntos(velocidad_C, angulo_C, velocidad_D, angulo_D):
    run_task(_mover_juntos(velocidad_C, angulo_C, velocidad_D, angulo_D))


#   DEFINICIÓN DE MISIONES

def mision_1():
    mover_motores_juntos(1000, 200, 1000, -200)
    avanzar(350, 850, 600)
    girar(25, 300)
    retroceder(150, 850, 600)
    girar(45)
    avanzar(300, 850, 600)
    mover_motores_juntos(1000, -200, 1000, 200)
    girar(-28)
    avanzar(20, 150, 100)
    girar_alrededor(0, -150, 18)
    retroceder(500, 1000, 900)  

def mision_2():
    girar(90)

def mision_3():
    mover_motores_juntos(500, 360, -500, 360)

def mision_4():
    girar_alrededor(0, 300, -90)

def mision_5():

    pass


#   PANEL DE CONTROL
#   - Lista de misiones en orden (agregar/sacar acá si cambia el número)
#   - EJECUTAR: un True/False por misión, mismo orden que la lista

mision_funciones = [mision_1, mision_2, mision_3, mision_4, mision_5]
EJECUTAR = [True, False, False, False, False]

NUM_MISIONES = len(mision_funciones)


#   SELECTOR DE MISIÓN INICIAL — botones del Hub

def elegir_mision_inicial():
    indice = 0
    hub.display.number(indice + 1)  # mostrar "misión 1" (índice 0 = misión 1)

    while True:
        pressed = hub.buttons.pressed()  # qué botones están apretados AHORA

        if Button.RIGHT in pressed:
            indice = (indice + 1) % NUM_MISIONES
            hub.display.number(indice + 1)
            wait(250)

        elif Button.LEFT in pressed:
            wait(250)
            return indice  # confirmado: esta es la misión de arranque

        wait(10)  # pausa corta del loop para no saturar el procesador


#   EJECUCIÓN — arranca desde la misión elegida

mision_inicial = elegir_mision_inicial()

for i in range(mision_inicial, NUM_MISIONES):
    if EJECUTAR[i]:
        mision_funciones[i]()
        wait(500)
