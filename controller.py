from machine import Pin, Timer, ADC
import time, utime
import asyncio

class Temp_calibration():
    
    def __init__(self):
        #ADC init
        self.adc = ADC(Pin(35))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        
        #engine init
        self.en = Pin(25, Pin.OUT)          # Lebegés = Engedélyezve (Közös anódnál)
        self.dir1 = Pin(26, Pin.OUT)
        self.step = Pin(27, Pin.OUT)
        
        #button init
        self.button = Pin(18, Pin.IN, Pin.PULL_UP)
        self.button.irq(trigger=Pin.IRQ_FALLING, handler=self.stop_signal)
        self.stop_event = asyncio.Event()
        self.button_pressed = False
        self.running = False
        self.last_interrupt_time = 0
        
        #Led init
        self.led = Pin(5, Pin.OUT)
        
        #main program init
        self.counter = 0
        self.max_engine_count = None
        self.min_engine_count = None
        self.wait_time = 0  #idő beállítása

    

    async def close_dir(self, val):               #kevesebb kakó
        self.dir1.value(1)
        await self.move_degree(val)
        
    async def start_dir(self):
        self.dir1.value(1)
        val = await self.move_degree(20)
        return val

    async def open_dir(self, val):                #több kakaó
        self.dir1.value(0)
        await self.move_degree(val)
        
    async def init_dir(self):
        self.dir1.value(0)
        val = await self.move_degree(57+360)
        return val


    async def move_degree(self, fok):
        # Kiszámoljuk a lépéseket (1/8 mikrostep és 1.8 fokos motor esetén)
        lepesek = int((fok / 360) * 1600)
        
        self.en.value(1) # Motor felébresztése
        await asyncio.sleep(0.01) # Rövid várakozás a feszültség stabilizálódásához
        
        for _ in range(lepesek):
            self.step.value(1)
            time.sleep_us(500)
            self.step.value(0)
            time.sleep_us(500)
        
        await asyncio.sleep(0.1)
        self.en.value(0) # Motor elaltatása (elernyed)
        print("Mozgás kész:", fok, "fok.")
        return fok
        

    async def first_step(self):
        self.led.toggle()
        self.counter = await self.init_dir()      # rendszer indítása
        
        await asyncio.sleep(15)  # adagoló folyamatban       
        start_counter = await self.start_dir()     # rendszer max benzin adagolása a hő emeléséhez
        
        await asyncio.sleep(0.05)
        self.counter -= start_counter
        
        await asyncio.sleep(5)    # ez majd 10 perc lesz, de tesztelés alatt pár másodperc marad.


    def max_limit(self):         # a motor max beállítását intézi
        if self.max_engine_count is None:
            self.max_engine_count = self.counter

    def min_limit(self):         # a motor min beállítását intézi
        if self.min_engine_count is None:
            self.min_engine_count = self.counter - 110

    def logic_limit(self):       # megnézi, hogy a motor logikai határain belül vagyunk-e
        return self.min_engine_count <= self.counter <= self.max_engine_count


    def counter_normalization(self, calibration):    # ha kimegyünk a mozgási határon kívül, azt korrigáljuk
        max_move = 0                                 # és megnézzük, hogy még mennyit mozoghatunk
        if self.counter < self.min_engine_count:
            self.counter += calibration
            max_move = self.counter - self.min_engine_count
            self.counter -= max_move
                        
        elif self.counter > self.max_engine_count:
            self.counter -= calibration
            max_move = self.max_engine_count - self.counter
            self.counter += max_move
            
        return max_move
    
    
    async def cooling_calibration(self, move_sum, diff):   #hűtésre szolgál
        if diff < 20:
            if move_sum <= 20:
                self.wait_time = 3
            else:
                self.wait_time = 1
            
            self.counter -= move_sum
            if self.logic_limit() is True:
                await self.close_dir(move_sum)
            else:
                max_move = self.counter_normalization(move_sum)
                if max_move > 0:
                    await self.close_dir(max_move)          
            
        
    async def heating_calibration(self, move_sum, diff):   #melegítésre szolgál
        if diff > -20:
            self.counter += move_sum
            if self.logic_limit() is True:
                await self.open_dir(move_sum)
            else:
                max_move = self.counter_normalization(move_sum)
                if max_move > 0:
                    await self.open_dir(max_move)
            self.wait_time = 3
    
    async def calibration(self):
        self.max_limit()
        self.min_limit()
        
        val_check = None                    # adc mérés különbség segégváltozója
        move_sum = 20                       # motor mozgatási segéd változója
        agressive_move_sum = move_sum * 2         # motor agresszívabb mozgási segéd változója
        
        val = self.adc.read()
        val_check = val
        
        self.running = True
        while self.running:

            val = self.adc.read()     # 0–4095
            diff = val - val_check       # a mérési különbséget számolja ki, így tudjuk, hogy melegedett-e a rendster vagy hűlt-e
            print()           
            self.wait_time = 1
            
            if val < 870:       # 90 °C 
                print("Túlmelegedés, leállás")
                break
            elif val < 1000:     # 85 °C (ha sűrün üti, akkor az előző értékeknél kalibráció szükséges, mert ez lényegében soft stop)
                print("motor minimuzmra állítása, túlmelegedés elkerülése.")
                await self.soft_stop()      # power = MIN

            elif val < 1180:     # 80 °C                              
                await self.cooling_calibration(agressive_move_sum, diff)    # ha tovább melegedik, állítok
                            
            elif val < 1350:     # 75 °C    
                await self.cooling_calibration(move_sum, diff)    # ha tovább melegedik, állít
        
            elif 1350 <= val <= 1700:   #első mozgási érték nyitása
                print("Nem kell szabályzás")
                pass
                 
            elif 1900 >= val >= 1700:     # 65 °C   
                await self.heating_calibration(move_sum, diff)    # ha hül, állít
                        
            elif 2200 >= val >= 1900:     # 60 °C      ha hül, állít      
                await self.heating_calibration(agressive_move_sum, diff)    # aresszívabb hőráadás
                
            else:                       # power = FULL                   
                await self.max_engine()
            
            val_check = val
            print(f"ADC: {val} | Diff: {diff} | Pos: {self.counter}/{self.max_engine_count}")           
            for _ in range(10*60*self.wait_time):
                if not self.running or self.stop_event.is_set():
                    break # Ha megnyomták a gombot, azonnal kilépünk a kis ciklusból
                
                await asyncio.sleep(0.1) # Átadjuk a vezérlést az ütemezőnek
                        
            # Ha a gombnyomás miatt léptünk ki a fenti for ciklusból:
            if not self.running or self.stop_event.is_set():
                print("Esemény: Azonnali leállás észlelve!")
                break # Kilépünk a fő while hurokból is
                
        print("Indul a leállási protokoll...")
        utime.sleep_ms(50)
        await self.emergency_mode()
    
    async def max_engine(self):    # Max motorállás
        max_val = self.max_engine_count - self.counter
        self.counter += max_val
        if max_val > 0:
            print("Max kraft, kell ide a hő!")
            await self.open_dir(max_val)
    
    
    async def soft_stop(self):         # soft stop, itt még nem áll le a rendszer
        min_val = self.counter - self.min_engine_count
        self.counter -= min_val
        await self.close_dir(min_val)
       
    async def emergency_mode(self):    # hard stop, nem engedjük, hogy a rendszer túl melegedjen
        await self.close_dir(self.counter)
        self.counter = 0
        self.en.value(0)
        self.led.toggle()
        
    def stop_signal(self, pin):
        # Várunk egy picit, hogy a "zaj" lecsengjen
        utime.sleep_ms(50)
        
        if pin.value() == 0:
            current_time = utime.ticks_ms()
            if utime.ticks_diff(current_time, self.last_interrupt_time) > 300:    # Gombnyomásra leállás
                if self.button_pressed == False:
                    self.running = False
                    self.stop_event.set()
                    self.last_interrupt_time = current_time
                    self.button_pressed = True
                    print("Validált leállítás!")
            else:
                #Szellemnyomás
                pass


if __name__ == "__main__":
    # Ez a rész CSAK akkor fut le, ha a controller.py-t indítod el közvetlenül.
    # Ha a main.py-ból importálod, ez a blokk láthatatlan marad.
    print("Önálló teszt üzemmód indítása...")
    
    engine = Temp_calibration()
    
    async def test_run():
        await engine.first_step()
        await engine.calibration()
        
    async def keayboard_stop():
        await engine.emergency_mode()

    try:
        asyncio.run(test_run())
    except KeyboardInterrupt:
        asyncio.run(keayboard_stop())
        print("Teszt megszakítva.")
        
