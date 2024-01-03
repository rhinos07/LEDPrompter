# coding=UTF8

from LedDisplay import LedDisplay
import sys
import time
import os
import readchar


def main():

    def connectDisplay(deviceName):
        try:
            ledz1 = LedDisplay(deviceName)
            ledz1.setDeviceId(1)
            ledz1.setRealtimeClock()
            return ledz1
        except:
            print("connect to device error " + deviceName)
        
    def reconnectDisplay(device, deviceName):
        try:
            device.close()
        except:
            print("problem deleting device " + deviceName)
        return connectDisplay(deviceName)

    def secureSend(display, deviceName, command):
        try:
            display.send(command)
            return display
        except:
            print("Unexpected error")
            display = reconnectDisplay(display, deviceName)
        return display



    devicePath1 = "/dev/ttyUSB0"
    devicePath2 = "/dev/ttyUSB1"

    ledz1 = connectDisplay(devicePath1)
    ledz2 = connectDisplay(devicePath2)

    ledz1 = secureSend(ledz1, devicePath1, "<L1><PA><FE><MA><WA><FE>Start")
    ledz2 = secureSend(ledz2, devicePath2, "<L1><PA><FE><MA><WA><FE>Start")
    #time.sleep(1)
    #ledz.send("<L1><PA><FA><MA><WA><FE>")
    #time.sleep(1)

    f = open('/home/pi/LEDPrompter/script.txt', 'r')
    lines = f.readlines()

    i = -2
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
                if i >= len(lines):
                    i = len(lines)-1
                command = lines[i]

        if key == readchar.key.ENTER or key == "j" or key == "J" or key == 'b':
            if i < 0:
                i = 0
            command = lines[i]

        if key == readchar.key.LEFT or key == readchar.key.PAGE_UP or key == "g" or key == "G":
            i = i-1
            if i < 0:
                i = 0
            command = lines[i]

        if command == "":
            continue

        try:
            if (command != "erase"):
                ledz1 = secureSend(ledz1, devicePath1, "<L1><PA><FE><MA><WD><FE>"+command)
                ledz2 = secureSend(ledz2, devicePath2, "<L1><PA><FE><MA><WD><FE>"+command)

                time.sleep(10)

            ledz1 = secureSend(ledz1, devicePath1, "<L1><PA><FA><MA><WA><FA>")
            ledz2 = secureSend(ledz2, devicePath2, "<L1><PA><FA><MA><WA><FA>")
        except:
            print("Unexpected error")
            ledz1 = reconnectDisplay(ledz1, "/dev/ttyUSB0")
            ledz2 = reconnectDisplay(ledz2, "/dev/ttyUSB1")


    ledz1 = secureSend(ledz1, devicePath1, "<L1><PA><FA><MA><WD><FE>Ende")
    ledz2 = secureSend(ledz2, devicePath2, "<L1><PA><FA><MA><WD><FE>Ende")
    time.sleep(1)
    ledz1.close()
    ledz2.close()

    del ledz1
    del ledz2


if __name__ == "__main__":
    main()
