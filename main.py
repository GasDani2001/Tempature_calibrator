from controller import Temp_calibration
from machine import Pin, Timer, ADC
#import time
import asyncio


#import network
#import socket
#import gc


"""#internet
SSID = "Wifi_ssid"
PASSWORD = "network_password"

def connect():
    reconnect_count = 0

    if not wlan.active():
        wlan.active(True)

    while True:
        if wlan.isconnected():
            print('Already connected:', wlan.ipconfig('addr4'))
            return
            
        reconnect_count += 1
        print("Connect attempt:", reconnect_count)

        try:
            wlan.disconnect()
        except:
            pass

        time.sleep(2)

        try:
            wlan.connect(SSID, PASSWORD)
        except OSError as e:
            print("WiFi error:", e)

        # várakozás
        for _ in range(15):
            if wlan.isconnected():
                print("Connected!")
                return
            time.sleep(1)

        # backoff
        if reconnect_count < 5:
            wait = 10
        elif reconnect_count < 10:
            wait = 30
        elif reconnect_count < 15:
            wait = 60
        else:
            wlan.disconnect()
            wlan.active(False)
            wait = 1800
            time.sleep(2)
            wlan.active(True)
            reconnect_count = 0

        print("Wait", wait, "sec")
        time.sleep(wait)
        
        gc.collect()

wlan = network.WLAN(network.STA_IF)
def show_free_memory():
    free_memory = gc.mem_free() / 1000
    print("Szabad memória:", free_memory, "kbyte")
    gc.collect()
"""

engine = Temp_calibration()

async def main():
    await engine.first_step()
    await engine.calibration()

    #villog()
    
async def interrupt():
    print("\n[!] Ctrl+C észlelve - Biztonsági lezárás...")
    await engine.emergency_mode()
    print("[OK] Rendszer leállítva.")
    
try:
    asyncio.run(main())
except KeyboardInterrupt:
    #leállítás
    asyncio.run(interrupt())

"""
en = Pin(25, Pin.OUT)          # Lebegés = Engedélyezve (Közös anódnál)
dir1 = Pin(26, Pin.OUT)
step = Pin(27, Pin.OUT)"""

#en.value(0)

