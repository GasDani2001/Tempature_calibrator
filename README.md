Ez egy hőszabályzó ESP32 mikrokontroller segítségével.
A fő célja, hogy a program képes legyen optimálisan vezérelni a léptetőmotort a vízhőfok függvényében, amit egy TB 6560 driver segítségével valósítok meg.

## Főbb funkciók
* **Automatikus szabályozás:** A léptetőmotor pozicionálása a mért vízhőmérséklet alapján.
* **Hálózatkezelés (folyamatban):** Wi-Fi kapcsolat előkészítése a távoli eléréshez/adatküldéshez.

## Felhasznált hardverek
* **Mikrokontroller:** ESP32 (MicroPython futtatásával)
* **Motorvezérlő:** TB6560 léptetőmotor driver
* **Aktuátor:** Léptetőmotor (a hőszabályzó szelep fizikai mozgatásához)
* **Szenzor:** NTC termisztor (vízhőmérséklet-mérő) – az analóg jelek beolvasása az ESP32 beépített ADC-jén keresztül, nyers értékekként történik.

## Hogyan működik?
1. A rendszer beolvassa a vízhőfokot.
2. A MicroPython kód kiszámítja a szükséges lépésszámot és irányt.
3. Az ESP32 jelet küld a TB6560 drivernek, ami elforgatja a motort a kívánt pozícióba.
