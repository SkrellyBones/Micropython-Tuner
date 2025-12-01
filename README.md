# Micropython-Tuner
A rudimentary tuner on the STM32F4DISC1 that detects a note through an analog microphone + preamp, processes the signal using the FFT from the ulab version of numpy, displays the detected note on the staff using the built-in screen, lets you save notes by pressing the button, lets you clear saved notes by holding down the button, and enables you to play saved notes by pressing the touchscreen.

lcd9341.py - bunch of classes for using the ILI9341 display, from rdagger https://github.com/rdagger/micropython-ili9341

touch811.py - bunch of classes for using the ILI9341 touchscreen, from rdagger. 

xfglcd_font.py - Font data in X-GLCD format. from rdagger https://github.com/rdagger/micropython-ili9341/blob/master/xglcd_font.py

main.py - main function for use on board.

STM32FFT.py - same as main function, but with comments and docstrings explaining how everything works!
