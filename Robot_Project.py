import cv2
import time
from gpiozero import DigitalOutputDevice
from ultralytics import YOLO
from adafruit_servokit import ServoKit

# --- CONFIGURATION ---
MOSFET_PIN = 17
DEADZONE = 40          # Entry boundary
HYSTERESIS = 15        # Extra pixels needed to "lose" the lock
LOCK_TIME_REQ = 0.5    # Seconds target must stay in center before MOSFET starts
FIRE_DELAY = 1.0       # Seconds MOSFET must be on before motor spins
TIMEOUT_4S = 1.0       # Seconds before MOSFET turns off after losing target

# --- SETUP ---
mosfet = DigitalOutputDevice(MOSFET_PIN)
kit = ServoKit(channels=16)
PAN_CH, TILT_CH, FIRE_CH = 0, 1, 2

model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture(0)
FRAME_W, FRAME_H = 640, 480
CENTER_X, CENTER_Y = FRAME_W // 2, FRAME_H // 2
TRACK_SPEED = 0.15

# --- STATE TRACKING ---
mosfet_active = False
mosfet_start_time = 0
last_centered_time = 0
lock_start_time = 0    # When the target first entered the deadzone
is_locked = False      # True only after staying in deadzone for LOCK_TIME_REQ

def stop_all():
    for i in range(16):
        kit.continuous_servo[i].throttle = 0
    mosfet.off()
    mosfet.close()
    print("\n[SAFE] Systems Stopped.")

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        now = time.time()
        results = model.track(frame, imgsz=320, persist=True, classes=0, verbose=False)

        if results and results[0].boxes:
            box = results[0].boxes[0]
            x1, y1, x2, y2 = box.xyxy[0]
            p_x, p_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
            err_x, err_y = p_x - CENTER_X, p_y - CENTER_Y
            
            # --- Tracking (Always Active) ---
            kit.continuous_servo[PAN_CH].throttle = TRACK_SPEED if err_x > DEADZONE else (-TRACK_SPEED if err_x < -DEADZONE else 0)
            kit.continuous_servo[TILT_CH].throttle = -TRACK_SPEED if err_y > DEADZONE else (TRACK_SPEED if err_y < -DEADZONE else 0)

            # --- Lock-On Logic ---
            # Using Hysteresis: If already locked, boundary is wider (DEADZONE + HYSTERESIS)
            current_boundary = DEADZONE + HYSTERESIS if is_locked else DEADZONE
            
            if abs(err_x) < current_boundary and abs(err_y) < current_boundary:
                last_centered_time = now # Update timeout
                
                if lock_start_time == 0:
                    lock_start_time = now # Started entering center
                
                # Check if they've been in the center long enough to "Lock"
                if not is_locked and (now - lock_start_time >= LOCK_TIME_REQ):
                    is_locked = True
                    mosfet.on()
                    mosfet_start_time = now
                    mosfet_active = True
            else:
                # Target left the center
                lock_start_time = 0
                is_locked = False
                kit.continuous_servo[FIRE_CH].throttle = 0

            # --- Firing Logic ---
            if is_locked and mosfet_active:
                if now - mosfet_start_time >= FIRE_DELAY:
                    kit.continuous_servo[FIRE_CH].throttle = 0.1
                    cv2.putText(frame, "LOCKED & FIRING!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, "PRIMING...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
        else:
            # No detection
            lock_start_time = 0
            is_locked = False
            kit.continuous_servo[FIRE_CH].throttle = 0
            kit.continuous_servo[PAN_CH].throttle = 0
            kit.continuous_servo[TILT_CH].throttle = 0

        # --- Global MOSFET Timeout (4s) ---
        if mosfet_active and (now - last_centered_time > TIMEOUT_4S):
            mosfet.off()
            mosfet_active = False
            is_locked = False

        cv2.imshow("Secure Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

finally:
    stop_all()
    cap.release()
    cv2.destroyAllWindows()
