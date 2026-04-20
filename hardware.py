from gpiozero import DigitalOutputDevice
from adafruit_servokit import ServoKit
import config
import time

class TurretHardware:
    def __init__(self):
        self.mosfet = DigitalOutputDevice(config.MOSFET_PIN)
        self.kit = ServoKit(channels = 16)
        self.mosfet_active = False
        self.manual_mode = False
        
    def move_aim(self, err_x, err_y, boundary):
        if self.manual_mode:
            return

        def get_scaled_speed(error):
            if abs(error) <= boundary:
                return 0
            speed = (abs(error) / 320) * config.TRACK_SPEED_TILT
            return -max(0.3, min(speed, config.TRACK_SPEED_TILT)) if error > 0 else max(0.3, min(speed, config.TRACK_SPEED_TILT))
        
        self.kit.continuous_servo[config.PAN_CH].throttle = 0

        current_tilt_speed = get_scaled_speed(err_y)
        current_pan_speed = get_scaled_speed(err_x)


        self.kit.continuous_servo[config.TILT_CH].throttle = current_tilt_speed
        self.kit.continuous_servo[config.PAN_CH].throttle = -current_pan_speed
            
    def fire(self, throttle):
        self.kit.continuous_servo[config.FIRE_CH].throttle = throttle
        
    def patrol(self):
        if int(time.time() / 5) % 2 == 0:
            self.kit.continuous_servo[config.PAN_CH].throttle = 0.4
        else:
            self.kit.continuous_servo[config.PAN_CH].throttle = -0.4
        
        self.kit.continuous_servo[config.TILT_CH].throttle = 0
        
    def set_mosfet(self, state, is_manual=False):
        
        if self.manual_mode and state and not is_manual:
            print("AI Fire Blocked: Manual Mode is Active")
            return
            
        if state:
            self.mosfet.on()
            self.mosfet_active = True
        else:
            self.mosfet.off()
            self.mosfet_active = False
            
    def stop_all(self):
        for i in range (16):
            self.kit.continuous_servo[i].throttle = 0
        self.mosfet.off()
        self.mosfet.close()
        print("\n[SAFE] Systems Stopped.")
    
        