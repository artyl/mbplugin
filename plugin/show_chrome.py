#!/usr/bin/python3
# -*- coding: utf8 -*-
import asyncio, time, subprocess, logging, shutil, os
import win32gui, win32process, psutil
import pyppeteer
from pyppeteer import launch  # PYthon puPPETEER
import pprint; pp = pprint.PrettyPrinter(indent=4).pprint

logging.getLogger().setLevel(logging.INFO)
user_data_dir = './clean_profile'
profile_directory = 'Profile 1'



def hide_chrome(hide=True):
    def enumWindowFunc(hwnd, windowList):
        """ win32gui.EnumWindows() callback """
        text = win32gui.GetWindowText(hwnd)
        className = win32gui.GetClassName(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if text.find("Chrome")>=0 and 'remote-debugging-port' in ''.join(psutil.Process(pid).cmdline()):
            windowList.append((hwnd, text, className))
    myWindows = []
    # enumerate thru all top windows and get windows which are ours
    win32gui.EnumWindows(enumWindowFunc, myWindows)
    for hwnd, text, className in myWindows:
        win32gui.ShowWindow(hwnd, not hide)  # True-Show, False-Hide
        win32gui.MoveWindow(hwnd, 0, 0, 1000, 1000, True)

hide_chrome(False)