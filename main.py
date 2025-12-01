import ulab
from ulab import numpy as np
from pyb import ADC, Pin, Timer, Switch
from touch811 import Touch811
from lcd9341 import LCD9341, color565
from xfglcd_font import XglcdFont
from machine import Pin, SoftI2C, SPI
import time

LCD_SPI_BUS = 5
SPI5_BAUD_RATE = 10000000
FREQ_I2C = 1000000
STMPE811_I2C_ADDR = 65
DISCO1_SCL_PIN = "PA8"
DISCO1_SD_PIN = "PC9"
i2c = SoftI2C(scl=Pin(DISCO1_SCL_PIN), sda=Pin(DISCO1_SD_PIN), freq=FREQ_I2C)
tt = Touch811(i2c, STMPE811_I2C_ADDR, rotation=0)
spi = SPI(LCD_SPI_BUS, baudrate=SPI5_BAUD_RATE)
lcd = LCD9341(spi, dc=Pin("PD13"), cs=Pin("PC2"), rst=Pin("PC11"))
unispace = XglcdFont("fonts/Unispace12x24.c", 12, 24)
saved_notes = []
sw = Switch()
hold_time_threshold = 2000


def sample(pin, buff, sample_rate):
    adc = pyb.ADC(pin)
    adc.read_timed(buff, sample_rate)
    signal = np.frombuffer(buff, dtype=np.uint16)
    signal = signal // 16
    return signal


class FrequencyFinder:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate

    def find_frequency(self, signal):
        signal = np.array(signal)
        signal = signal - np.mean(signal)
        n = len(signal)
        i = np.arange(n)
        window = np.array(0.5 - 0.5 * np.cos(2 * np.pi * i / n))
        signal *= window
        spectrum = np.fft.fft(signal)
        real = np.real(spectrum)
        imaginary = np.imag(spectrum)
        magnitude = np.sqrt(real**2 + imaginary**2)
        peak = np.argmax(magnitude[: n // 2])
        beta = magnitude[peak]
        alpha = magnitude[peak - 1]
        gamma = magnitude[peak + 1]
        p = 1 / 2 * (alpha - gamma) / (alpha - 2 * beta + gamma)
        peakindex = peak + p
        resolution = self.sample_rate / n
        frequency = peakindex * resolution
        return frequency


class NoteNamer:
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self):
        0

    def frequency_to_note(self, frequency):
        if frequency < 55:
            return "A0"
        midi_number = int(round(69 + 12 * np.log2(frequency / 440)))
        note_index = midi_number % 12
        octave = midi_number // 12 - 2
        return self.note_names[note_index] + str(octave)


class AudioAnalyzer(FrequencyFinder, NoteNamer):
    def __init__(self, sample_rate):
        super().__init__(sample_rate)

    def analyze(self, signal):
        f = self.find_frequency(signal)
        n = self.frequency_to_note(f)
        return f, n


x = 120


class DrawStaff:
    def __init__(self, top_line, line_spacing):
        self.top_line = top_line
        self.line_spacing = line_spacing

    def draw_lines(self, top_line, line_spacing):
        lcd.fill_rectangle(1, 1, 239, 319, color565(255, 255, 255))
        r = (line_spacing) // 2
        j = 0
        bottom_line = top_line + line_spacing * 10
        lcd.draw_text(
            10,
            top_line + line_spacing,
            "&",
            unispace,
            color565(0, 0, 0),
            color565(255, 255, 255),
        )
        lcd.draw_text(
            10,
            bottom_line - line_spacing * 2,
            "):",
            unispace,
            color565(0, 0, 0),
            color565(255, 255, 255),
        )
        for i in range(top_line, bottom_line + 2, line_spacing):
            if j == 5:
                middle_c = i
                j += 1
                continue
            else:
                j += 1
                lcd.draw_hline(1, i, 239, color565(0, 0, 0))
                lcd.draw_hline(1, i + 1, 239, color565(0, 0, 0))
        return top_line, line_spacing, middle_c, bottom_line, r


note = [
    "C8",
    "B7",
    "A7",
    "G7",
    "F7",
    "E7",
    "D7",
    "C7",
    "B6",
    "A6",
    "G6",
    "F6",
    "E6",
    "D6",
    "C6",
    "B5",
    "A5",
    "G5",
    "F5",
    "E5",
    "D5",
    "C5",
    "B4",
    "A4",
    "G4",
    "F4",
    "E4",
    "D4",
    "C4",
    "B3",
    "A3",
    "G3",
    "F3",
    "E3",
    "D3",
    "C3",
    "B2",
    "A2",
    "G2",
    "F2",
    "E2",
    "D2",
    "C2",
    "B1",
    "A1",
    "G1",
    "F1",
    "E1",
    "D1",
    "C1",
    "B0",
    "A0",
]


def y_position(note_name, line_spacing):
    index_C4 = note.index("C4")
    note_index = note.index(note_name)
    y_position = middle_c_y + ((note_index - index_C4) * line_spacing // 2)
    y_position = max(0, min(y_position, 300))
    return y_position


def draw_ledger(begin, y, width):
    lcd.draw_hline(begin, y, width, color565(0, 0, 0))
    lcd.draw_hline(begin, y + 1, width, color565(0, 0, 0))


def sharp(note_name):
    if "#" in note_name:
        is_sharp = True
        original = note_name
        note_name = original.replace("#", "")
    else:
        is_sharp = False
        note_name = note_name
        original = note_name
    return note_name, is_sharp, original


def place_note(
    radius, y, line_spacing, bottom_line, top, is_sharp, new_name, note_name, x=120
):
    radius = (line_spacing - 1) // 2
    ledger_width = radius * 4
    ledger_begin = x - (radius * 2)
    lcd.fill_circle(x, y, radius, color565(0, 0, 0))
    if y > middle_c_y:
        text_y = 250
    else:
        text_y = 10
    lcd.draw_text(
        50, text_y, new_name, unispace, color565(0, 0, 0), color565(255, 255, 255)
    )
    if is_sharp is True:
        sharp_x = x + radius * 2
        sharp_y = y - radius * 2
        lcd.fill_hrect(sharp_x, sharp_y, 20, 20, color565(255, 255, 255))
        lcd.draw_text(
            sharp_x, sharp_y, "#", unispace, color565(0, 0, 0), color565(255, 255, 255)
        )
    if y == middle_c_y:
        draw_ledger(ledger_begin, y, ledger_width)
    if y <= top:
        for i in range(top, y - 2, -line_spacing):
            draw_ledger(ledger_begin, i, ledger_width)
    elif y >= bottom_line:
        for i in range(bottom_line, y + 2, line_spacing):
            draw_ledger(ledger_begin, i, ledger_width)


pin1 = Pin("PA5")
timer = Timer(2, freq=440)
speaker = timer.channel(1, Timer.PWM, pin=pin1)


def play_note(speaker, timer, freq, duration, duty=50):
    if freq == 0:
        speaker.pulse_width_percent(0)
    else:
        timer.freq(int(freq / 2))
        speaker.pulse_width_percent(duty)
        time.sleep_ms(duration)
        speaker.pulse_width_percent(0)


def check_touchscreen():
    t = tt.get_xyz_unique()
    if len(t) > 0 and t[0][2] > 0.1:
        print("Touch detected! Playing saved notes...")
        for f, n in saved_notes:
            play_note(speaker, timer, f, 500, 75)
            time.sleep_ms(50)
        time.sleep_ms(900)


Analyzer = AudioAnalyzer(16000)
buffer = bytearray(4096)
TOP_LINE = 90
LINE_SPACING = 14
draw_staff = DrawStaff(TOP_LINE, LINE_SPACING)
while True:
    x = sample("PC3", buffer, 16000)
    freq, note1 = Analyzer.analyze(x)
    top, line_spacing, middle_c_y, bottom_line, r = draw_staff.draw_lines(
        TOP_LINE, LINE_SPACING
    )
    print(note1, " ", freq)
    notename, is_sharp, original = sharp(note1)
    y = y_position(notename, line_spacing)
    place_note(r, y, line_spacing, bottom_line, top, is_sharp, original, notename)
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < 2000:
        if sw():
            press_start = pyb.millis()
            while sw():
                pyb.delay(50)
                press_duration = pyb.millis() - press_start
            if press_duration >= hold_time_threshold:
                saved_notes.clear()
                print("Saved Notes Cleared")
            else:
                saved_notes.append((freq, note1))
                print("Saved:", note1)
        check_touchscreen()
        time.sleep_ms(20)
