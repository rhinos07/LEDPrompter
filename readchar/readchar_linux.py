# -*- coding: utf-8 -*-
# Initially taken from:
# http://code.activestate.com/recipes/134892/
# Thanks to Danny Yoo
import sys
import os
import select
import tty
import termios


def readchar(wait_for_char=True):
    #old_settings = termios.tcgetattr(sys.stdin)
    #tty.setcbreak(sys.stdin.fileno())
    #try:
    #    if wait_for_char or select.select([sys.stdin, ], [], [], 0.0)[0]:
    #        char = os.read(sys.stdin.fileno(), 1)
    #        return char if type(char) is str else char.decode()
    #finally:
    #    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch