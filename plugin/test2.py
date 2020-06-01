# -*- coding: utf8 -*- 
import sys;sys.dont_write_bytecode = True
import os, sys, re, io, logging
from PIL import Image, ImageTk
import tkinter.tix as Tix
import urllib.parse as urlparse
import requests, bs4
import store

def get_human_captcha(buffer):
    get_human_captcha.res=''
    def callback(ev):
        get_human_captcha.res = inp.get()
        window.destroy()
    window = Tix.Tk()
    im = Image.open(io.BytesIO(buffer))
    img = ImageTk.PhotoImage(im)
    lbl = Tix.Label(window, image = img).pack()
    window.bind("<Return>", callback)
    inp = Tix.Entry(window);inp.pack()
    inp.focus_set()
    window.mainloop()
    return get_human_captcha.res

def get_balance(login, password, storename=None):
    ''' На вход логин и пароль, на выходе словарь с результатами '''
    ## Demo captcha
    session = requests.Session()
    data = {}
    captcha_text = ''
    response1_text = '<img class="captcha-img" src="/api/captcha/next?form=login&x1485735388" title="CAPTCHA" alt="CAPTCHA"/>'
    url = 'https://lk.megafon.ru/login/'
    cap_urls = [i for i in bs4.BeautifulSoup(response1_text).findAll('img') if i['alt']=='CAPTCHA']
    if len(cap_urls)>0:
        captcha_url = urlparse.urljoin(url,cap_urls[0]['src'])
        buffer = session.get(captcha_url).content
        captcha_text = get_human_captcha(buffer)
        data['captcha'] = captcha_text
        print(captcha_text)
    #response2 = session.post('https://lk.megafon.ru/dologin/', data=data)    
    
    return {'Balance':666.45, 'SMS': 43, 'AnyString':f'Captcha={captcha_text}'}

if __name__ == '__main__':
    print('This is module test2')