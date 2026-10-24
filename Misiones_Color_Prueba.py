from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Button, Color
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task

# CONFIGURACIÓN DEL ROBOT
hub = PrimeHub()

# Motores de las ruedas motrices
left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.B, Direction.CLOCKWISE)

# Motores de misión
motor_C = Motor(Port.C)
motor_D = Motor(Port.D)
motor_C.reset_angle(0)
motor_D.reset_angle(0)

sensor_izq = ColorSensor(Port.F)
sensor_der = ColorSensor(Port.E)

wheel_diameter = 62
axle_track = 150
robot = DriveBase(left_motor, right_motor, wheel_diameter, axle_track)
robot.use_gyro(True)

# FUNCIONES DE MOVIMIENTO DEL ROBOT
def avanzar(distancia_mm, velocidad, aceleracion):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    robot.straight(distancia_mm)

def retroceder(distancia_mm, velocidad, aceleracion):
    avanzar(-distancia_mm, velocidad, aceleracion)

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
        
    left_motor.stop()
    right_motor.stop()
    robot.use_gyro(True)

# FUNCIONES DE MOTORES DE MISIÓN
def mover_motor_C(velocidad, angulo): motor_C.run_angle(velocidad, angulo)
def mover_motor_D(velocidad, angulo): motor_D.run_angle(velocidad, angulo)
def mover_motor_C_a_angulo(velocidad, angulo): motor_C.run_target(velocidad, angulo)
def mover_motor_D_a_angulo(velocidad, angulo): motor_D.run_target(velocidad, angulo)

# VERSIONES ASÍNCRONAS OPTIMIZADAS (Sin bucles innecesarios)
async def async_avanzar(distancia_mm, velocidad, aceleracion):
    robot.settings(straight_speed=velocidad, straight_acceleration=aceleracion)
    await robot.straight(distancia_mm)

async def async_retroceder(distancia_mm, velocidad, aceleracion):
    await async_avanzar(-distancia_mm, velocidad, aceleracion)

async def async_mover_motor_C(velocidad, angulo):
    await motor_C.run_angle(velocidad, angulo) # Pybricks ya espera de forma nativa con await

async def async_mover_motor_D(velocidad, angulo):
    await motor_D.run_angle(velocidad, angulo)

async def con_delay(segundos, *corrutinas):
    await wait(segundos * 1000)
    await multitask(*corrutinas)

def correr_juntos(*corrutinas):
    run_task(multitask(*corrutinas))

# DEFINICIÓN DE MISIONES
def mision_1():
    avanzar(200, 1000, 700)
    correr_juntos(async_mover_motor_D(1000, 360), async_mover_motor_C(1000, 360))

def mision_2():
    correr_juntos(async_avanzar(200, 1000, 700), async_mover_motor_C(1000, 720))
    mover_motor_D(1000, 90)

def mision_3():
    mover_motor_C(1000, 360)
    mover_motor_C(-1000, 360)

def mision_4():
    girar_alrededor(0, 300, -90)

def mision_5():
    mover_motor_D(-800, 4000)
    wait(100)
    mover_motor_D(800, 3700)

def mision_detener():
    motor_C.stop()
    motor_D.stop()
    left_motor.stop()
    right_motor.stop()

# COMPROBACIÓN FILTRADA DE COLORES (Evita lecturas en falso y bucles infinitos)
def obtener_color_estable(sensor):
    lecturas = [sensor.color() for _ in range(3)]
    if lecturas[0] == lecturas[1] == lecturas[2]:
        return lecturas[0]
    return Color.NONE

# SELECTOR DE MISIÓN EFICIENTE
def elegir_y_correr_misiones():
    # Diccionario para mapear combinaciones de colores a sus respectivas misiones y números en pantalla
    misiones = {
        (Color.RED, Color.RED): (1, mision_1),
        (Color.GREEN, Color.RED): (2, mision_2),
        (Color.RED, Color.GREEN): (3, mision_3),
        (Color.BLUE, Color.GREEN): (4, mision_4),
        (Color.YELLOW, Color.YELLOW): (5, mision_5),
    }

    while True:
        pressed = hub.buttons.pressed()
        color_izq = obtener_color_estable(sensor_izq)
        color_der = obtener_color_estable(sensor_der)
        
        combinacion = (color_izq, color_der)
        
        if combinacion in misiones:
            num_pantalla, mision_a_ejecutar = misiones[combinacion]
            hub.display.number(num_pantalla)
            
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                mision_a_ejecutar()
                mision_detener()
                hub.display.number(0)
                wait(500) # Evita activaciones accidentales repetidas
        else:
            hub.display.number(0)
            mision_detener()
            
        wait(50) # Respiro para el procesador en el bucle principal

# Ejecución principal
elegir_y_correr_misiones()
