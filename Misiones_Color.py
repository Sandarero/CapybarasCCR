from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Button, Color
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

motor_C.reset_angle(0)
motor_D.reset_angle(0)

sensor_izq = ColorSensor(Port.F)
sensor_der = ColorSensor(Port.E)

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

def mover_motor_C_a_angulo(velocidad, angulo):
    motor_C.run_target(velocidad, angulo)

def mover_motor_D_a_angulo(velocidad, angulo):
    motor_D.run_target(velocidad, angulo)

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
    avanzar(200, 1000, 700)
    correr_juntos(
        async_mover_motor_D(1000, 360),
        async_mover_motor_C(1000, 360)
        )
    pass  

def mision_2():
    correr_juntos(
        async_avanzar(200, 1000, 700),
        async_mover_motor_C(1000, 720)
    )
    mover_motor_D(1000, 90)
    pass

def mision_3():
    mover_motor_C(1000, 360)
    mover_motor_C(-1000, 360)
    #correr_juntos(
     #   async_mover_motor_C(500, 360),
      #  async_mover_motor_D(500, 360))
    pass

def mision_4():
    girar_alrededor(0, 300, -90)
    pass

def mision_5():
    mover_motor_D(-800, 4000)
    wait(100)
    mover_motor_D(800, 3700)
    pass

def mision_detener():
    motor_C.stop()
    motor_D.stop()
    left_motor.stop()
    right_motor.stop()
    
    

def comprobar_colores_der(finalizado = 0, state_1_der = Color.NONE, state_2_der = Color.NONE, state_3_der = Color.NONE):
    while finalizado == 0:
        state_new_der = sensor_der.color()

        state_1_der = state_2_der
        state_2_der = state_3_der
        state_3_der = state_new_der

        if state_3_der == state_2_der and state_2_der == state_1_der:
            if state_3_der == Color.NONE:
                i = 0
            else:
                #print('Todos son iguales:', state_new_der)
                return state_new_der
                finalizado = 1
    pass

def comprobar_colores_izq(finalizado = 0, state_1_izq = Color.NONE, state_2_izq = Color.NONE, state_3_izq = Color.NONE):
    while finalizado == 0:
        state_new_izq = sensor_izq.color()

        state_1_izq = state_2_izq
        state_2_izq = state_3_izq
        state_3_izq = state_new_izq
        if state_3_izq == state_2_izq and state_2_izq == state_1_izq:
            if state_3_izq == Color.NONE:
                i = 0
            else:
                #print('Todos son iguales:', state_new_izq)
                return state_new_izq
                finalizado = 1
    pass


#   SELECTOR DE MISIÓN INICIAL CON SUS COLORES - INICIAR CON CUALQUIER BOTON DEL HUB (IZQ / DER)

def elegir_y_correr_misiones():
    while True:
        pressed = hub.buttons.pressed()
        #color_der = sensor_der.color()
        #color_izq = sensor_izq.color()

        color_der = comprobar_colores_der()
        color_izq = comprobar_colores_izq()
        
        if color_izq == Color.RED and color_der == Color.RED:
            hub.display.number(1)
            
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                mision_1()
                mision_detener()
        elif color_izq == Color.GREEN and color_der == Color.RED:
            hub.display.number(2)
            
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                mision_2()
                mision_detener()
        elif color_izq == Color.RED and color_der == Color.GREEN:
            hub.display.number(3)
            
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                mision_3()
                mision_detener()
        elif color_izq == Color.BLUE and color_der == Color.GREEN:
            hub.display.number(4)
            
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                mision_4()
                mision_detener()
        elif color_izq == Color.YELLOW and color_der == Color.YELLOW:
            hub.display.number(5)
            
            if Button.LEFT in pressed or Button.RIGHT in pressed:
                mision_5()
                mision_detener()
        
        else:
            hub.display.number(0)
            mision_detener()
        
hub.display.number(0)        
elegir_y_correr_misiones()


