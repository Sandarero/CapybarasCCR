from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Button, Color, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task

#   CONFIGURACIÓN DEL ROBOT
hub = PrimeHub()

left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.B, Direction.CLOCKWISE)

motor_C = Motor(Port.C)
motor_D = Motor(Port.D)
motor_C.reset_angle(0)
motor_D.reset_angle(0)

sensor_izq = ColorSensor(Port.E)
sensor_der = ColorSensor(Port.F)

# Limitar los colores que el sensor puede devolver = lectura MUCHO más estable
COLORES_TARJETA = [Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW, Color.NONE]
sensor_izq.detectable_colors(COLORES_TARJETA)
sensor_der.detectable_colors(COLORES_TARJETA)

wheel_diameter = 62
axle_track = 150
robot = DriveBase(left_motor, right_motor, wheel_diameter, axle_track)
robot.use_gyro(True)

#   MOVIMIENTO (ruedas A/B)
def avanzar(distancia_mm, velocidad, aceleracion, then=Stop.HOLD):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    robot.straight(distancia_mm, then)

def retroceder(distancia_mm, velocidad, aceleracion, then=Stop.HOLD):
    avanzar(-distancia_mm, velocidad, aceleracion, then)

def girar(angulo, velocidad_giro=250):
    robot.settings(turn_rate=velocidad_giro)
    robot.turn(angulo)

def girar_alrededor(velocidad_izq, velocidad_der, angulo_objetivo, margen_error=2):
    robot.use_gyro(False)
    hub.imu.reset_heading(0)
    left_motor.run(velocidad_izq)
    right_motor.run(velocidad_der)
    signo = 1 if angulo_objetivo > 0 else -1
    while signo * hub.imu.heading() < signo * angulo_objetivo - margen_error:
        wait(10)
    left_motor.brake()      # brake en vez de stop: menos inercia/overshoot
    right_motor.brake()
    robot.use_gyro(True)

#   MOTORES DE MISIÓN (C y D)
def mover_motor_C(velocidad, angulo):
    motor_C.run_angle(velocidad, angulo)

def mover_motor_D(velocidad, angulo):
    motor_D.run_angle(velocidad, angulo)

def mover_motor_C_a_angulo(velocidad, angulo):
    motor_C.run_target(velocidad, angulo)

def mover_motor_D_a_angulo(velocidad, angulo):
    motor_D.run_target(velocidad, angulo)

#   VERSIONES ASÍNCRONAS (multitarea)
async def async_avanzar(distancia_mm, velocidad, aceleracion):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    await robot.straight(distancia_mm)

async def async_retroceder(distancia_mm, velocidad, aceleracion):
    await async_avanzar(-distancia_mm, velocidad, aceleracion)

async def async_mover_motor_C(velocidad, angulo):
    await motor_C.run_angle(velocidad, angulo)

async def async_mover_motor_D(velocidad, angulo):
    await motor_D.run_angle(velocidad, angulo)

async def con_delay(segundos, *corrutinas):
    await wait(segundos * 1000)
    await multitask(*corrutinas)

def correr_juntos(*corrutinas):
    async def _juntos():
        await multitask(*corrutinas)
    run_task(_juntos())

#   MISIONES
def mision_1():
    correr_juntos(
        async_mover_motor_C(-250, 200),
        async_avanzar(720, 950, 950)
    )
    mover_motor_C(500, 150)
    retroceder(100, 100, 50)
    correr_juntos(
        async_mover_motor_C(-1000, 150),
        async_avanzar(50, 200, 200)
    )
    retroceder(50, 200, 200)
    girar(45)
    avanzar(50, 200, 200)
    girar(45)

def mision_2():
    correr_juntos(
        async_avanzar(200, 1000, 700),
        async_mover_motor_C(1000, 720)
    )
    mover_motor_D(1000, 90)

def mision_3():
    mover_motor_C(1000, 360)
    mover_motor_C(-1000, 360)

def mision_4():
    girar_alrededor(0, 300, -90)

def mision_5():
    correr_juntos(
        async_mover_motor_D(-800, 850),
        async_mover_motor_C(-400, 100),
        async_avanzar(385, 700, 500)
    )
    girar(45)
    avanzar(400, 700, 500)
    girar(45)
    avanzar(570, 700, 400)
    girar(45)
    retroceder(80, 200, 200)
    girar(45)
    retroceder(50, 100, 100)
    mover_motor_C(1000, 230)
    wait(1000)
    avanzar(120, 200, 300)
    correr_juntos(
        async_mover_motor_D(-900, 4500),
        con_delay(3, async_retroceder(15, 50, 50))
    )
    wait(100)
    mover_motor_D(800, 3200)

def detener_todo():
    motor_C.stop()
    motor_D.stop()
    left_motor.stop()
    right_motor.stop()

#   SELECTOR POR COLORES
def color_estable(sensor, lecturas=5):
    c = sensor.color()
    for _ in range(lecturas - 1):
        wait(5)
        if sensor.color() != c:
            return Color.NONE
    return c

# (color izq, color der, número en pantalla, misión)
MISIONES = [
    (Color.BLUE,   Color.RED,    1, mision_1),
    (Color.RED,    Color.RED,    2, mision_2),
    (Color.GREEN,  Color.RED,    3, mision_3),
    (Color.BLUE,   Color.GREEN,  4, mision_4),
    (Color.YELLOW, Color.YELLOW, 5, mision_5),
]

def buscar_mision(c_izq, c_der):
    for ci, cd, numero, funcion in MISIONES:
        if c_izq == ci and c_der == cd:
            return numero, funcion
    return 0, None

def elegir_y_correr_misiones():
    while True:
        c_izq = color_estable(sensor_izq)
        c_der = color_estable(sensor_der)
        numero, funcion = buscar_mision(c_izq, c_der)
        hub.display.number(numero)

        if funcion is not None:
            pressed = hub.buttons.pressed()   # se lee DESPUÉS de los sensores
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                funcion()
                detener_todo()
                # esperar a soltar el botón para no relanzar la misión
                while hub.buttons.pressed():
                    wait(10)
        wait(20)

hub.display.number(0)
elegir_y_correr_misiones()
