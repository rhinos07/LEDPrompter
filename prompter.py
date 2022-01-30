# coding=UTF8

from LedDisplay import LedDisplay
import sys
import time
import os
import readchar


def main():

    f = open('script.txt', 'r')
    x = f.readlines()


    device = "/dev/ttyUSB1"

    for arg in sys.argv[1:]:
        if arg.startswith("--device="):
            device = arg[9:]

    ledz = LedDisplay(device)
    ledz.setDeviceId(1)
    ledz.setRealtimeClock()
    ledz.send("<L1><PA><FA><MA><WD><FE>Start")
    time.sleep(1)
    ledz.send("<L1><PA><FA><MA><WD><FE>.")
    time.sleep(1)

    i = -1;
    while True:
        print "wait for key"
        key = readchar.readkey()

        if key == 'x':
            break

        command = ""
        if key == readchar.key.RIGHT or key == readchar.key.PAGE_DOWN or key == "m" or key == "M":
            i = i+1
            if i >= len(x):
                i = len(x)-1
            command = x[i]
            print 'next'

        if key == readchar.key.ENTER or key == "j" or key == "J" or key == "b":
            if i < 0:
                i = 0
            command = x[i]
            print 'repeat'

        if key == readchar.key.LEFT  or key == readchar.key.PAGE_UP or key == "g" or key == "G":
            i = i-1
            if i < 0:
                i = 0
            command = x[i]
            print 'prev'

        if command == "":
            continue

        try:
            ledz.send("<L1><PA><FE><MA><WD><FE>"+command)
            #print command

            time.sleep(10)

            ledz.send("<L1><PA><FA><MA><WD><FE>.")
        except:
            print("Unexpected error")

    ledz.send("<L1><PA><FA><MA><WD><FE>Ende")
    time.sleep(1)
    ledz.close()

    del ledz


if __name__ == "__main__":
    main()
