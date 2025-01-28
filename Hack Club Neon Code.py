import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
import time
import datetime
import requests
import base64

Toggl_API_Token = ""


days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

API_String = Toggl_API_Token+":api_token"
base64encoded = base64.b64encode(API_String.encode("ascii")).decode("ascii")
headers = {"Authorization":f"Basic {base64encoded}"}

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=64, height=32, bit_depth=1,
    rgb_pins=[board.D6, board.D5, board.D9, board.D11, board.D10, board.D12],
    addr_pins=[board.A5, board.A4, board.A3, board.A2],
    clock_pin=board.D13, latch_pin=board.D0, output_enable_pin=board.D1)

display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

def calculate_percentage():
    hr = datetime.datetime.now().hour + 11
    if hr > 23:
        hr = hr - 24
    min = datetime.datetime.now().minute    
    min = min + (hr * 60)
    percent = (min / 1440) * 100
    percent = 100 - percent
    return round(percent, 1)

def fill_display(percent):
    bitmap = displayio.Bitmap(64, 32, 2)
    skipped = 0
    toSkip = 2048 - (2048 * (percent / 100))
    for y in range(32):
        for x in range(64):
            if skipped < toSkip:
                bitmap[x, y] = 0
                skipped += 1
            else:
                bitmap[x, y] = 1
    return bitmap

def clock():
    percent = calculate_percentage()
    
    line1 = adafruit_display_text.label.Label(
        font=terminalio.FONT,
        color= 0xFFFFFF,
        label_direction="LTR",
        scale=2,
        anchor_point=(0.5,0.5),
        anchored_position=(32,16),
        text=str(percent)+"%",
    )
    
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = 0x3b3b3b

    tile_grid = displayio.TileGrid(fill_display(percent), pixel_shader=palette)
  
    g = displayio.Group()
    g.append(tile_grid)
    g.append(line1)
    display.root_group = g

def pomodoro(toggl):
    start_time = datetime.datetime.strptime(toggl.json()['start'], "%Y-%m-%dT%H:%M:%S%z")
    now = datetime.datetime.now(datetime.timezone.utc)
    duration = now - start_time
    durationMin = duration.seconds // 60
    durationSec = duration.seconds % 60

    for _ in range(25):
        if durationSec > 59:
            durationSec = 0
            durationMin += 1

        remainingMin = 25 - durationMin - 1
        remainingSec = 60 - durationSec
        if remainingSec == 60:
            remainingSec = 0
            remainingMin += 1

        line1 = adafruit_display_text.label.Label(
            font=terminalio.FONT,
            color=0xFFFFFF,
            label_direction="LTR",
            scale=2,
            anchor_point=(0.5, 0.5),
            anchored_position=(32, 16),
            text=f"{remainingMin:02}:{remainingSec:02}",
        )

        percent = 100 - (durationMin / 25) * 100

        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = 0x3b3b3b

        tile_grid = displayio.TileGrid(fill_display(percent), pixel_shader=palette)

        g = displayio.Group()
        g.append(tile_grid)
        g.append(line1)
        display.root_group = g

        display.refresh(minimum_frames_per_second=0)
        time.sleep(1)
        durationSec += 1

while True:
    toggl = requests.get('https://api.track.toggl.com/api/v9/me/time_entries/current', headers=headers)
    print(toggl.json())

    if toggl.json() is not None:
        pomodoro(toggl)
    else:
        clock()

    display.refresh(minimum_frames_per_second=0)
    time.sleep(15)
