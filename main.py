#!/usr/bin/env python
# Display a runtext and a static text with double-buffering.

import sys
sys.path.append("/home/pi/ledmatrix/work/rpi-rgb-led-matrix/bindings/python/rgbmatrix/")

from rgbmatrix import RGBMatrix, RGBMatrixOptions
import graphics
import time
import requests
from bs4 import BeautifulSoup
import re
import threading
import datetime
from PIL import Image
import io

atcl_arr = []
temp = ""
weather = ""
weather_img = {}

def getNews():
    global atcl_arr
    atcl_arr_new = []
    
    # 接続
    print(str(datetime.datetime.now())+": getting NEWS...")
    #URL = "https://www.japantimes.co.jp/" # JT
    URL = "https://www.nikkei.com/news/category/" # 日経
    rest = requests.get(URL)
    soup = BeautifulSoup(rest.text, "html.parser")
    
    # HTMLパース
    #atcl_list = soup.find_all(attrs={"class" : "article-title"}) #JT
    atcl_list = soup.select('#CONTENTS_MAIN')[0].find_all(class_=re.compile("_titleL")) # 日経
    
    # 格納
    for atcl in atcl_list:
        print(atcl.string)
        atcl_arr_new.append(atcl.string)
    atcl_arr = atcl_arr_new
    
    return atcl_arr

def getTemperatureAndWeatherIcon():
    global temp
    global weather
    global weather_img
    
    print(str(datetime.datetime.now())+": getting weather information...")
    URL = "https://tenki.jp/forecast/3/17/4610/14117/" # 青葉区のアメダス
    rest = requests.get(URL)
    soup = BeautifulSoup(rest.text, "html.parser")
    
    temp_tag = soup.select('#rain-temp-btn')[0]
    temp_tag.select('.diff')[0].decompose()
    temp = temp_tag.text
    print(temp)
    
    weather_tag = soup.select('.today-weather')[0].select('p.weather-telop')[0]
    weather_icon_url = soup.select('.today-weather')[0].select('img')[0].get('src')
    weather = weather_tag.text
    print(weather)
    
    # 美咲フォントに☀がないので記号置換はNGだった
    # 画像を8x8に縮小しメモリに置く
    #if (weather == "晴"):
        #weather_img = Image.open(io.BytesIO(requests.get(weather_icon_url).content))
        #weather_img = Image.open("/home/pi/ledmatrix/shiny.png")
    #weather_img.thumbnail((round(weather_img.width*8/weather_img.height), 8), Image.ANTIALIAS) # 縦横比を維持して縮小
    
    return weather_img

class createLED():
    # パネル設定用関数
    def __init__(self):
        self.font = []             # フォント
        self.textColor = []        # テキストカラー
        self.flagPreparedToDisplay = False # メイン関数を表示する準備ができたかどうかのフラグ
        
        # LEDマトリクス設定
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.gpio_slowdown = 0
        self.matrix = RGBMatrix(options = options)
        
        # キャンバス作成
        self.offscreen_canvas = self.matrix.CreateFrameCanvas()
        
        # 最低限のフォントだけ読み込み、WAITINGを表示させておく
        self.f = threading.Thread(target=self.displayLEDTemp)
        self.f.start()
        
        # 文字設定
        print("setting LED matrix options...")
        self.font.append(graphics.Font())
        self.font[0].LoadFont("/home/pi/ledmatrix/src/font/sazanami-20040629/sazanami-gothic_14.bdf") # 上の行と分割しないとセグフォ
        self.font.append(graphics.Font())
        self.font[1].LoadFont("/home/pi/ledmatrix/src/font/misaki_bdf_2021-05-05/misaki_gothic_2nd.bdf")
        self.textColor.append(graphics.Color(255, 255, 0))
        
        # 画像設定
        #self.image = Image.open("/home/pi/ledmatrix/twitter_dot.png")

    # パネル点灯する関数（一時的）
    def displayLEDTemp(self):
        print('display "WAITING..."')
        font_simple = graphics.Font()
        font_simple.LoadFont("/home/pi/ledmatrix/work/rpi-rgb-led-matrix/fonts/5x8.bdf")
        textColor_simple = graphics.Color(255, 255, 0)
        #while (self.flagPreparedToDisplay == False):
        timeout_start = time.time()
        while time.time() < timeout_start + 10: # 10秒経過後にWAITING表示を消すはずだが機能しない。ただ上のwhileより処理が早いのでこちらを使ってる…
            graphics.DrawText(self.offscreen_canvas, font_simple, 0, 31, textColor_simple, "WAITING...") # 静止文字
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    # パネル点灯する関数（メイン）
    def displayLEDMain(self):
        global atcl_arr
        global temp
        global weather
        global weather_img
        
        # Start loop
        i = 0
        pos = self.offscreen_canvas.width
        self.flagPreparedToDisplay = True
        print("display LED, Press CTRL-C to stop")
        while True:
            self.offscreen_canvas.Clear()
            graphics.DrawText(self.offscreen_canvas, self.font[1], 0, 7, self.textColor[0], "外気温"+temp) # 静止文字
            graphics.DrawText(self.offscreen_canvas, self.font[1], 0, 15, self.textColor[0], "天気: "+weather) # 静止文字
            #self.matrix.SetImage(weather_img.convert('RGB'), 40, 8, False) # 画像
            length = graphics.DrawText(self.offscreen_canvas, self.font[0], pos, 29, self.textColor[0], atcl_arr[i]) # 動く文字
            
            # 動く文字の位置をずらす
            pos = pos - 1
            if (pos + length < 0): # 文字が左まで行って消えたら、posをリセット
                pos = self.offscreen_canvas.width
                # iをインクリメント、iがMAXなら0にする
                if (i == len(atcl_arr)-1):
                    i = 0
                else:
                    i += 1
            
            time.sleep(0.05)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
    
def worker():
    getNews()
    getTemperatureAndWeatherIcon()

def mainloop(time_interval, f, another):
    f() # 最初に情報取得の完了まで待たないと描画時にoutofindex
    
    now = time.time()
    t0 = threading.Thread(target=another, daemon=True) # argsの,は必要。ないとエラー
    t0.start() # 描画
    while True: # 5分後、以後5分ごとに実行
        wait_time = time_interval - ( (time.time() - now) % time_interval )
        time.sleep(wait_time)
        t = threading.Thread(target=f, daemon=True)
        t.start() # 情報取得を実行
    
if __name__ == "__main__":
    LED = createLED()
    mainloop(300, worker, LED.displayLEDMain)
