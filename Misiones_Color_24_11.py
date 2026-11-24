from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Button, Color, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task

# CONFIGURACIÓN DEL ROBOT
hub = PrimeHub()
left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.B, Direction.CLOCKWISE)
motor_C = Motor(Port.C)
motor_D = Motor(Port.D)

motor_C.reset_angle(0)
motor_D.reset_angle(0)

sensor_izq = ColorSensor(Port.E)
sensor_der = ColorSensor(Port.F)

COLORES_TARJETA = [Color.RED, Color.GREEN, Color.BLUE, Color.YELLOW, Color.NONE]
sensor_izq.detectable_colors(COLORES_TARJETA)
sensor_der.detectable_colors(COLORES_TARJETA)

robot = DriveBase(left_motor, right_motor, wheel_diameter=62, axle_track=150)
robot.use_gyro(True)

# FUNCIONES DE MOVIMIENTO (Síncronas y Asíncronas)
def mover_recto(distancia_mm, velocidad, aceleracion, then=Stop.HOLD):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    robot.straight(distancia_mm, then)

async def async_mover_recto(distancia_mm, velocidad, aceleracion, then=Stop.HOLD):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    await robot.straight(distancia_mm, then)

def girar(angulo, velocidad_giro=250, aceleracion_giro=400):
    robot.settings(turn_rate=velocidad_giro, turn_acceleration=aceleracion_giro)
    robot.turn(angulo)

async def async_girar(angulo, velocidad_giro=250, aceleracion_giro=400):
    robot.settings(turn_rate=velocidad_giro, turn_acceleration=aceleracion_giro)
    await robot.turn(angulo)

def girar_alrededor(velocidad_izq, velocidad_der, angulo_objetivo, margen_error=2):
    robot.use_gyro(False)
    hub.imu.reset_heading(0)
    left_motor.run(velocidad_izq)
    right_motor.run(velocidad_der)
    
    signo = 1 if angulo_objetivo > 0 else -1
    while signo * hub.imu.heading() < signo * angulo_objetivo - margen_error:
        wait(10)
        
    left_motor.brake()
    right_motor.brake()
    robot.use_gyro(True)

def mover_motor(motor, velocidad, angulo):
    motor.run_angle(velocidad, angulo)

async def async_mover_motor(motor, velocidad, angulo):
    await motor.run_angle(velocidad, angulo)

async def con_delay(segundos, *corrutinas):
    await wait(segundos * 1000)
    await multitask(*corrutinas)

def correr_juntos(*corrutinas):
    async def _juntos():
        await multitask(*corrutinas)
    run_task(_juntos())

def detener_todo():
    motor_C.stop()
    motor_D.stop()
    robot.stop()

# MISIONES
def mision_1():
    correr_juntos(
        async_mover_recto(880, 1000, 500),
        async_mover_motor(motor_C, 100, 140),
        async_mover_motor(motor_D, 300, -120)
    )
    correr_juntos(
        async_mover_motor(motor_C, 50, -170),
        async_mover_motor(motor_D, 1000, 720)
    )
    wait(2000)
    mover_motor(motor_C, 300, 180)
    mover_recto(-900, 1000, 700)

def mision_2():
    correr_juntos(
        async_mover_recto(480, 500, 400),
        async_mover_motor(motor_C, 500, 140)
    )
    correr_juntos(
        async_mover_recto(-400, 1000, 700),
        async_mover_motor(motor_C, 200, -90)
    )
    while Button.BLUETOOTH not in hub.buttons.pressed():
        wait(20)
    mover_recto(740, 1000, 600)
    girar(-30, 150)
    mover_recto(60, 500, 300)
    mover_motor(motor_C, 300, 120)
    mover_recto(-70, 1000, 700)
    girar(30)
    mover_recto(-750, 1000, 700)

def mision_3():
    mover_motor(motor_C, 1000, 360)
    mover_motor(motor_C, -1000, 360)

def mision_4():
    girar_alrededor(0, 300, -90)

def mision_5():
    correr_juntos(
        async_mover_motor(motor_D, -800, 850),
        async_mover_motor(motor_C, -400, 100),
        async_mover_recto(385, 700, 500)
    )
    girar(45)
    mover_recto(400, 700, 500)
    girar(45)
    mover_recto(570, 700, 400)
    girar(45)
    mover_recto(-80, 200, 200)
    girar(45)
    mover_recto(-50, 100, 100)
    mover_motor(motor_C, 1000, 230)
    wait(1000)
    mover_recto(120, 200, 300)
    correr_juntos(
        async_mover_motor(motor_D, -900, 4500),
        con_delay(3, async_mover_recto(-15, 50, 50))
    )
    wait(100)
    mover_motor(motor_D, 800, 3200)

# SELECTOR POR COLORES Y BUCLE PRINCIPAL
MISIONES = {
    (Color.RED, Color.RED): (1, mision_1),
    (Color.BLUE, Color.RED): (2, mision_2),
    (Color.GREEN, Color.RED): (3, mision_3),
    (Color.BLUE, Color.GREEN): (4, mision_4),
    (Color.YELLOW, Color.YELLOW): (5, mision_5),
}

def color_estable(sensor, lecturas=5):
    c = sensor.color()
    if c == Color.NONE: # Salida rápida si no detecta nada
        return Color.NONE
    for _ in range(lecturas - 1):
        wait(5)
        if sensor.color() != c:
            return Color.NONE
    return c

def elegir_y_correr_misiones():
    ultimo_numero = -1
    while True:
        c_izq = color_estable(sensor_izq)
        c_der = color_estable(sensor_der)
        
        numero, funcion = MISIONES.get((c_izq, c_der), (0, None))
        
        if numero != ultimo_numero:
            hub.display.number(numero)
            ultimo_numero = numero
            
        if funcion is not None:
            pressed = hub.buttons.pressed()
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                funcion()
                detener_todo()
                ultimo_numero = -1 # Fuerza refresco de pantalla al terminar
                while hub.buttons.pressed():
                    wait(10)
        wait(20)

elegir_y_correr_misiones()
