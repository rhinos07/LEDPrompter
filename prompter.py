# coding=UTF8

from LedDisplay import LedDisplay
import sys
import time
import os
import readchar


def main():

    f = open('/home/pi/LEDPrompter/script.txt', 'r')
    x = f.readlines()


    device1 = "/dev/ttyUSB0"
    device2 = "/dev/ttyUSB1"

    for arg in sys.argv[1:]:
        if arg.startswith("--device="):
            device1 = arg[9:]

    ledz1 = LedDisplay(device1)
    ledz2 = LedDisplay(device2)
    ledz1.setDeviceId(1)
    ledz2.setDeviceId(1)
    ledz1.setRealtimeClock()
    ledz2.setRealtimeClock()
    ledz1.send("<L1><PA><FE><MA><WA><FE>Start")
    ledz2.send("<L1><PA><FE><MA><WA><FE>Start")
    #time.sleep(1)
    #ledz.send("<L1><PA><FA><MA><WA><FE>")
    #time.sleep(1)

    i = -2;
    while True:
        print("===========> wait for key (x=escape)  <=============")
        key = readchar.readkey()

        print(key)
        if key == 'x':
            break

        command = ""
        if key == readchar.key.RIGHT or key == readchar.key.PAGE_DOWN or key == "m" or key == "M":
            i = i+1
            if i < 0:
                command = "erase"
            else:
                if i >= len(x):
                    i = len(x)-1
                command = x[i]

        if key == readchar.key.ENTER or key == "j" or key == "J" or key == 'b':
            if i < 0:
                i = 0
            command = x[i]

        if key == readchar.key.LEFT or key == readchar.key.PAGE_UP or key == "g" or key == "G":
            i = i-1
            if i < 0:
                i = 0
            command = x[i]

        if command == "":
            continue

        try:
            if (command != "erase"):
                ledz1.send("<L1><PA><FE><MA><WD><FE>"+command)
                ledz2.send("<L1><PA><FE><MA><WD><FE>"+command)

                time.sleep(10)

            ledz1.send("<L1><PA><FA><MA><WA><FA>")
            ledz2.send("<L1><PA><FA><MA><WA><FA>")
        except:
            print("Unexpected error")

    ledz1.send("<L1><PA><FA><MA><WD><FE>Ende")
    ledz2.send("<L1><PA><FA><MA><WD><FE>Ende")
    time.sleep(1)
    ledz1.close()
    ledz2.close()

    del ledz


if __name__ == "__main__":
    main()
