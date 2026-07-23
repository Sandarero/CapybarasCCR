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

#   VERSIONES ASÍNCRONAS PARA MULTITAREA (agrega "async_" al inicio)
async def async_avanzar(distancia_mm, velocidad, aceleracion):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    await robot.straight(distancia_mm)   # esto solo ya alcanza

async def async_retroceder(distancia_mm, velocidad, aceleracion):
    await async_avanzar(-distancia_mm, velocidad, aceleracion)

async def async_mover_motor_C(velocidad, angulo):
    # Al pasar wait=False, Pybricks no bloquea y nos permite usar await
    await motor_C.run_angle(velocidad, angulo)
    while not motor_C.done():
        await wait(10)

async def async_mover_motor_D(velocidad, angulo):
    await motor_D.run_angle(velocidad, angulo)
    while not motor_D.done():
        await wait(10)

async def con_delay(segundos, *corrutinas):
    await wait(segundos * 1000)
    await multitask(*corrutinas)

async def _correr_juntos(*corrutinas):
    # Desempaquetamos directamente las corrutinas dentro de multitask
    await multitask(*corrutinas)

def correr_juntos(*corrutinas):
    run_task(_correr_juntos(*corrutinas))

#   DEFINICIÓN DE MISIONES
def mision_1():
    correr_juntos(
        async_avanzar(350, 850, 600),
        async_mover_motor_C(1000, 200),
        async_mover_motor_D(1000, -200))
    girar(25, 300)
    retroceder(150, 850, 600)
    girar(45)
    correr_juntos(
        async_avanzar(300, 850, 600),
        async_mover_motor_C(1000, -200),
        async_mover_motor_D(1000, 200))
    girar(-28)
    avanzar(145, 850, 600)
    correr_juntos(
        async_mover_motor_C(100, 150),
        async_mover_motor_D(100, -150))
    avanzar(20, 150, 100)
    girar_alrededor(0, -150, 18)
    retroceder(500, 1000, 900)
    pass  

def mision_2():
    correr_juntos(
        async_avanzar(500, 100, 900),
        con_delay(3, async_mover_motor_C(1000, 150),
        async_mover_motor_D(1000, -150)))
pass

def mision_3():
    correr_juntos(
        async_mover_motor_C(500, 360),
        async_mover_motor_D(500, 360))

def mision_4():
    girar_alrededor(0, 300, -90)

def mision_5():

    pass

#   PANEL DE CONTROL
#   - Lista de misiones en orden (agregar/sacar acá si cambia el número)
#   - EJECUTAR: un True/False por misión, mismo orden que la lista
mision_funciones = [mision_1, mision_2, mision_3, mision_4, mision_5]
EJECUTAR = [True, True, False, False, False]
NUM_MISIONES = len(mision_funciones)

#   SELECTOR DE MISIÓN INICIAL — botones del Hub
def elegir_y_correr_misiones():
    indice = 0
    hub.display.number(indice + 1)

    while True:
        pressed = hub.buttons.pressed()
        if Button.RIGHT in pressed:
            indice = (indice + 1) % NUM_MISIONES
            hub.display.number(indice + 1)
            while Button.RIGHT in hub.buttons.pressed():
                wait(10)

        elif Button.LEFT in pressed:
            if EJECUTAR[indice]:
                mision_funciones[indice]()
            else:
                # Misión desactivada: avisar con una X antes de volver al número
                hub.display.char("X")
                wait(500)
                hub.display.number(indice + 1)   # volver a mostrar la selección actual
            while Button.LEFT in hub.buttons.pressed():
                wait(10)
        wait(10)

elegir_y_correr_misiones()
