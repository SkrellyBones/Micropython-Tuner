import time
import ulab
from ulab import numpy as np
from pyb import ADC, Pin, Timer, Switch
from touch811 import Touch811
from lcd9341 import LCD9341, color565
from xfglcd_font import XglcdFont
from machine import Pin, SoftI2C, SPI


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
saved_notes = []  # empty list to store saved notes from button press
sw = Switch()  # USR button
HOLD_TIME_THRESHOLD = 2000  # threshold in ms for long press on button



def sample(pin, buff, sample_rate):
    """
    real time buffer based sampling of microphone on STM32, reads until buffer is full and
    then continues executing the rest of the program
    :param pin: the pin for ADC
    :param buff: buffer to be fed data, please be at least 1024 for 2048 bit buffer,
    bigger is better
    :param sample_rate: sample rate in Hz
    :return: signal as a sin wave
    """
    adc = pyb.ADC(pin)
    adc.read_timed(buff, sample_rate)
    signal = np.frombuffer(buff, dtype=np.uint16)
    signal = signal // 16
    return signal



class FrequencyFinder:
    """
    A class for detecting the dominant frequency of an audio signal
    using FFT on an ADC pin
    Attributes:
    -----------
        sample_rate : int
          Sampling rate of the ADC in Hz.
     Methods:
     ----------
     find_frequency(signal)
         Use the fast fourier transform to find the frequency of a signal buffer
    """

    def __init__(self, sample_rate):
        """
        Initialize the FrequencyFinder with a given sample rate.
        :param: samplerate (int): Sampling rate in Hz.
        """
        self.sample_rate = sample_rate

  
    def find_frequency(self, signal):
        """
        Takes a signal and returns the frequency of the signal.
        :param signal: array of values (hopefully sinusodial)
        :return: frequency of the signal in Hz (int)
        """
        signal = np.array(signal)
        signal = signal - np.mean(signal)  # remove Dc offset for increased accuracy
        n = len(signal)
        i = np.arange(n)
        window = np.array(
            0.5 - 0.5 * np.cos(2 * np.pi * i / n)
        )  # create window around signal to
        # prevent spectral leakage from discontinuity
        signal *= window  # apply hanning window
        spectrum = np.fft.fft(signal)  # preform fft
        real = np.real(spectrum)  # split off real and imaginary parts
        imaginary = np.imag(spectrum)
        magnitude = np.sqrt(real**2 + imaginary**2)  # pythagorean theorem
        peak = np.argmax(magnitude[: n // 2])  # take only positive side
        # parabolic interpolation for further increased accuracy
        beta = magnitude[peak]  # center bin
        alpha = magnitude[peak - 1]  # left neighbor
        gamma = magnitude[peak + 1]  # right neighbor
        p = (
            1 / 2 * (alpha - gamma) / (alpha - 2 * beta + gamma)
        )  # formula for interpolating
        peakindex = peak + p
        resolution = self.sample_rate / n  # by definition
        frequency = peakindex * resolution
        return frequency


class NoteNamer:
    """
    A class for finding the name of a note based on the frequency
    Attributes:
    -----------
        None
     Methods:
     ----------
     frequency_to_note(frequency)
         Use the midi number formula to determine the name of a note based on frequency
    """

    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def __init__(self):
        """
        No required initialization parameters
        """

    def frequency_to_note(self, frequency):
        """
        Uses the midi number formula to convert a frequency to a note name and octave
        :param frequency: int : any > 300
        :return: note name and octave number as two element string
        """
        if frequency < 55:
            return "A0"
        midi_number = int(round(69 + 12 * np.log2(frequency / 440)))
        note_index = midi_number % 12
        octave = midi_number // 12 - 2
        return self.note_names[note_index] + str(octave)


class AudioAnalyzer(FrequencyFinder, NoteNamer):
    """
    Shoehorned in inheritance, combines FrequencyFinder and NoteNamer into a single class
    """

    def __init__(self, sample_rate):
        super().__init__(sample_rate)  # for FrequencyFinder

    def analyze(self, signal):
        """
        at this point we already know what this does
        """
        f = self.find_frequency(signal)
        n = self.frequency_to_note(f)
        return f, n


X = 120  # set x for middle of screen


class DrawStaff:
    """Draws staff and places note on staff
    attributes: y of top line
                line_spacing between lines"""

    def __init__(self, top_line, line_spacing):  # initiate the class
        self.top_line = top_line
        self.line_spacing = line_spacing

    def draw_lines(self, top_line, line_spacing):
        """This function will draw the 10 bar lines of the staff.
        It will initialize where middle C is on the y axis
        It will return top_line, line_spacing, and middle_c as variables if
        assigned"""
        lcd.fill_rectangle(1, 1, 239, 319, color565(255, 255, 255))  # wh background
        r = (line_spacing) // 2
        j = 0  # line being drawn
        bottom_line = top_line + line_spacing * 10
        lcd.draw_text(
            10,
            top_line + line_spacing,
            "&",
            unispace,
            color565(0, 0, 0),
            color565(255, 255, 255),
        )  # Draw Treble
        lcd.draw_text(
            10,
            bottom_line - line_spacing * 2,
            "):",
            unispace,
            color565(0, 0, 0),
            color565(255, 255, 255),
        )  # Draw Bass
        for i in range(top_line, bottom_line + 2, line_spacing):
            if j == 5:  # Skip the line middle c
                middle_c = i  # Capture line position of middle C
                j += 1
                continue
            j += 1
            lcd.draw_hline(1, i, 239, color565(0, 0, 0))
            lcd.draw_hline(1, i + 1, 239, color565(0, 0, 0))
        return top_line, line_spacing, middle_c, bottom_line, r
        # Return the values of top_line and line_spacing


# array of note names A0 to C8
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
    """Function to find y position of a given note in relation to middle c"""

    index_C4 = note.index("C4")  # assign index of C4

    note_index = note.index(note_name)  # Get the index of the note

    y_position = middle_c_y + ((note_index - index_C4) * line_spacing // 2)
    y_position = max(0, min(y_position, 300))
    return y_position  # Calculate mid c y position


def draw_ledger(begin, y, width):
    """draw two short lines"""

    lcd.draw_hline(begin, y, width, color565(0, 0, 0))

    lcd.draw_hline(begin, y + 1, width, color565(0, 0, 0))


def sharp(note_name):
    """
    if there is a sharp in the note_name, return sharp bool and remove,

    retain original note_name, make note_name unsharp"""

    if "#" in note_name:

        is_sharp = True  # check sharp
        original = note_name  # retain original name for text

        note_name = original.replace("#", "")  # remove sharp

    else:

        is_sharp = False

        note_name = note_name  # retain note name

        original = note_name

    return note_name, is_sharp, original  # these will be used in place_note



def place_note(
    radius, y, line_spacing, bottom_line, top, is_sharp, new_name, note_name, X=120
):
    """This function will place note, sharp, and ledger lines"""
    radius = (line_spacing - 1) // 2  # radius for note
    ledger_width = radius * 4  # width for ledger line
    ledger_begin = X - (radius * 2)  # ledger line starts 2 r before  note center
    lcd.fill_circle(X, y, radius, color565(0, 0, 0))  # place note
    if y > middle_c_y:  # text below  bass clef
        text_y = 250
    else:
        text_y = 10  # above treble clef
    lcd.draw_text(
        50, text_y, new_name, unispace, color565(0, 0, 0), color565(255, 255, 255)
    )
    # Draw note name
    if is_sharp is True:  # if note sharp, place sharp symbol on white background
        sharp_x = X + radius * 2
        sharp_y = y - radius * 2
        lcd.fill_hrect(sharp_x, sharp_y, 20, 20, color565(255, 255, 255))  # w box
        lcd.draw_text(
            sharp_x, sharp_y, "#", unispace, color565(0, 0, 0), color565(255, 255, 255)
        )  # sharp symbol on top
    if y == middle_c_y:  # middle c is the only note with a ledger line
        draw_ledger(ledger_begin, y, ledger_width)
    if y <= top:  # y pixel less than or equal top line
        for i in range(top, y - 2, -line_spacing):
            draw_ledger(ledger_begin, i, ledger_width)
    elif y >= bottom_line:
        for i in range(bottom_line, y + 2, line_spacing):
            draw_ledger(ledger_begin, i, ledger_width)


pin1 = Pin("PA5")  # set output pin to PA5 which has PWM capabilities
timer = Timer(2, freq=440)  # timer has two channels available, use 2,
# set frequency(freq=key word) to 440, this establishes reference frequency

speaker = timer.channel(
    1, Timer.PWM, pin=pin1
)  # Configure channel 1 for PWM on pin1('PA5')  with 50% duty cycle


def play_note(speaker, timer, freq, duration, duty=50):
    """This will play the proper pitch of the note that has been input"""
    if freq == 0:
        speaker.pulse_width_percent(0)

    else:
        timer.freq(
            int(freq / 2)
        )  # set pitch, divided by 2 because PWM doubles frequency inputs
        speaker.pulse_width_percent(duty)  # start PWM
        time.sleep_ms(duration)  # play note this long
        speaker.pulse_width_percent(0)  # change PWM to 0


def check_touchscreen():
    """
    Check if the user touched the screen and if so play all the saved notes
    """
    t = tt.get_xyz_unique()
    if len(t) > 0 and t[0][2] > 0.1:  # pressure threshold
        print("Touch detected! Playing saved notes...")
        for f, n in saved_notes:
            play_note(speaker, timer, f, 500, 75)
            time.sleep_ms(50)
        time.sleep_ms(600)  # debounce


Analyzer = AudioAnalyzer(16000)
buffer = bytearray(4096)
TOP_LINE = 90 
LINE_SPACING = 14
draw_staff = DrawStaff(TOP_LINE, LINE_SPACING)
while True:
    x = sample("PC3", buffer, 16000)
    freq, note1 = Analyzer.analyze(x)  # do a lot of math at once
    top, line_spacing, middle_c_y, bottom_line, r = (
        draw_staff.draw_lines(  # set up and redraw staff each cycle
            TOP_LINE, LINE_SPACING
        )
    )
    print(note1, " ", freq)
    notename, is_sharp, original = sharp(note1)
    y = y_position(notename, line_spacing)
    place_note(
        r, y, line_spacing, bottom_line, top, is_sharp, original, notename
    )  # we gotta calculate the y position for each new note
    start = time.ticks_ms()  
    while time.ticks_diff(time.ticks_ms(), start) < 2000:  # check the timer every cycle
        if sw():  # user pressed USER button
            press_start = pyb.millis()  # record start time
            while sw():  # while held down
                pyb.delay(50)
                press_duration = pyb.millis() - press_start
            if (
                press_duration >= HOLD_TIME_THRESHOLD
            ):  
                saved_notes.clear()
                print("Saved Notes Cleared")
            else:
                saved_notes.append((freq, note1)) 
                print("Saved:", note1)
        check_touchscreen()  # blocking interrupt for playback, makes sense to pause here
        time.sleep_ms(20)  # give the poor cpu a break

