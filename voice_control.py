import json
import threading
import queue
import config
import sounddevice as sd
from vosk import Model, KaldiRecognizer

audio_queue = queue.Queue()

def callback(indata, frames, time, status):
    audio_queue.put(bytes(indata))

class VoiceProcessor:
    def __init__(self, model_path="model"):
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.running = True
        self.patrol_mode = False

    def listen(self, turret):
        try:
            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                   channels=1, device='hw:2,0', callback=callback):
                print("🎤 Listening for commands...")
                while self.running:
                    try:
                        data = audio_queue.get(timeout=0.5)
                        if self.rec.AcceptWaveform(data):
                            result = json.loads(self.rec.Result())
                            text = result.get("text", "").lower()
                            if text:
                    
                                print(f"DEBUG: Vosk heard -> '{text}'") 
                                self.execute(text, turret)
                        else:
                            
                            partial = json.loads(self.rec.PartialResult())
                            p_text = partial.get("partial", "").lower()
                            if p_text:
                                
                                pass
                    except queue.Empty:
                        continue
        except Exception as e:
            print(f"Mic Error: {e}")

    def execute(self, cmd, turret):
        
        if "fire" in cmd or "boom" in cmd or "blast" in cmd or "eject" in cmd:
            print("!!! VOICE ACTION: FIRING !!!")
            turret.manual_mode = True
            turret.set_mosfet(True)
            turret.fire(-.5)
            time.sleep(2)
            turret.set_mosfet(False)
            turret.fire(0)
            cmd = ""
            
        
        elif "stop" in cmd or "cease" in cmd or "wait" in cmd or "hold" in cmd:
            print("!!! VOICE ACTION: STOPPING !!!")
            turret.set_mosfet(False)
            turret.fire(0)
            turret.manual_mode = True
            self.patrol_mode = False
            turret.kit.continuous_servo[config.PAN_CH].throttle = 0
            turret.kit.continuous_servo[config.TILT_CH].throttle = 0

            
            
        elif "patrol" in cmd or "scan" in cmd or "secure" in cmd:
            self.patrol_mode = True
            turret.manual_mode = True
            
        elif "resume" in cmd or "auto" in cmd or "track" in cmd or "aggression" in cmd:
            print("!!! VOICE ACTION: AI RESUMED !!!")
            turret.manual_mode = False
            
    def stop(self):
        self.running = False
        
    def _auto_stop_fire(self, turret):
        """Helper method to ensure firing stops safely"""
        print("!!! ACTION: TURRET STOPPED !!!")
        turret.fire(0)
        turret.set_mosfet(False)
        turret.manual_mode = True
        