import cv2
import time
import threading
import config
from hardware import TurretHardware
from voice_control import VoiceProcessor
from ultralytics import YOLO

turret = TurretHardware()
voice = VoiceProcessor("model")
voice_thread = threading.Thread(target =voice.listen, args=(turret,), daemon=True)
voice_thread.start()


model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture(0)

last_centered_time = 0
lock_start_time = 0
mosfet_start_time = 0
is_locked = False

try:
    while True:
        ret, frame = cap.read()
        if not ret: break
        now = time.time()
        results = model.track(frame, imgsz=160, persist=True, classes=0,verbose=False)
        
        if not turret.manual_mode:
            if results and results[0].boxes:
                box = results[0].boxes[0]
                x1, y1, x2, y2 = box.xyxy[0]
                height = y2 - y1
                p_x = int((x1 + x2) / 2)
                p_y = int (y1 + (height * .2))
                err_x, err_y = p_x - config.CENTER_X, p_y - config.CENTER_Y
                
                current_boundary = config.DEADZONE + config.HYSTERESIS if is_locked else config.DEADZONE
                
                turret.move_aim(err_x, err_y, current_boundary)
                
                if abs(err_x) < current_boundary and abs(err_y) < current_boundary:
                    last_centered_time = now
                    if lock_start_time == 0: locked_start_time = now
                    
                    if not is_locked and (now - lock_start_time >= config.LOCK_TIME_REQ):
                        is_locked = True
                        turret.set_mosfet(True)
                        mosfet_start_time = now
                        
                else:
                    lock_start_time = 0
                    is_locked = False
                    turret.fire(0)
                
                if is_locked and turret.mosfet_active:
                    if now - mosfet_start_time >= config.FIRE_DELAY:
                        turret.fire(-.5)
                        cv2.putText(frame, "LOCKED & FIRING!", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                         cv2.putText(frame, "PRIMING...", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                         
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2) ,int(y2)), (255, 0, 0), 2)
                
            else:
                lock_start_time = 0
                is_locked = False
                turret.fire(0)
                turret.move_aim(0, 0, 0)
                
            if turret.mosfet_active and (now - last_centered_time > config.TIMEOUT_4S):
                    turret.set_mosfet(False)
                    is_locked = False
                    
        if turret.manual_mode:
            if voice.patrol_mode:
                turret.patrol()
                cv2.putText(frame, "PATROL MODE", (200, 450), 1, 2, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "VOICE OVERRIDE", (200, 450), 1, 2, (0, 255, 255), 2)
                
        cv2.imshow("Secure Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
finally:
    print("shutting down...")
    turret.stop_all()
    cap.release()
    voice.stop()
    cv2.destroyAllWindows()
    print("All systems safe")
