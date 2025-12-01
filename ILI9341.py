_A=None
import numbers,time,numpy as np
from PIL import Image,ImageDraw
import Adafruit_GPIO as GPIO,Adafruit_GPIO.SPI as SPI
ILI9341_TFTWIDTH=240
ILI9341_TFTHEIGHT=320
ILI9341_NOP=0
ILI9341_SWRESET=1
ILI9341_RDDID=4
ILI9341_RDDST=9
ILI9341_SLPIN=16
ILI9341_SLPOUT=17
ILI9341_PTLON=18
ILI9341_NORON=19
ILI9341_RDMODE=10
ILI9341_RDMADCTL=11
ILI9341_RDPIXFMT=12
ILI9341_RDIMGFMT=10
ILI9341_RDSELFDIAG=15
ILI9341_INVOFF=32
ILI9341_INVON=33
ILI9341_GAMMASET=38
ILI9341_DISPOFF=40
ILI9341_DISPON=41
ILI9341_CASET=42
ILI9341_PASET=43
ILI9341_RAMWR=44
ILI9341_RAMRD=46
ILI9341_PTLAR=48
ILI9341_MADCTL=54
ILI9341_PIXFMT=58
ILI9341_FRMCTR1=177
ILI9341_FRMCTR2=178
ILI9341_FRMCTR3=179
ILI9341_INVCTR=180
ILI9341_DFUNCTR=182
ILI9341_PWCTR1=192
ILI9341_PWCTR2=193
ILI9341_PWCTR3=194
ILI9341_PWCTR4=195
ILI9341_PWCTR5=196
ILI9341_VMCTR1=197
ILI9341_VMCTR2=199
ILI9341_RDID1=218
ILI9341_RDID2=219
ILI9341_RDID3=220
ILI9341_RDID4=221
ILI9341_GMCTRP1=224
ILI9341_GMCTRN1=225
ILI9341_PWCTR6=252
ILI9341_BLACK=0
ILI9341_BLUE=31
ILI9341_RED=63488
ILI9341_GREEN=2016
ILI9341_CYAN=2047
ILI9341_MAGENTA=63519
ILI9341_YELLOW=65504
ILI9341_WHITE=65535
def color565(r,g,b):return(r&248)<<8|(g&252)<<3|b>>3
def image_to_data(image):pb=np.array(image.convert('RGB')).astype('uint16');color=(pb[:,:,0]&248)<<8|(pb[:,:,1]&252)<<3|pb[:,:,2]>>3;return np.dstack((color>>8&255,color&255)).flatten().tolist()
class ILI9341:
	def __init__(self,dc,spi,rst=_A,gpio=_A,width=ILI9341_TFTWIDTH,height=ILI9341_TFTHEIGHT):
		self._dc=dc;self._rst=rst;self._spi=spi;self._gpio=gpio;self.width=width;self.height=height
		if self._gpio is _A:self._gpio=GPIO.get_platform_gpio()
		self._gpio.setup(dc,GPIO.OUT)
		if rst is not _A:self._gpio.setup(rst,GPIO.OUT)
		spi.set_mode(0);spi.set_bit_order(SPI.MSBFIRST);spi.set_clock_hz(64000000);self.buffer=Image.new('RGB',(width,height))
	def send(self,data,is_data=True,chunk_size=4096):
		self._gpio.output(self._dc,is_data)
		if isinstance(data,numbers.Number):data=[data&255]
		for start in range(0,len(data),chunk_size):end=min(start+chunk_size,len(data));self._spi.write(data[start:end])
	def command(self,data):self.send(data,False)
	def data(self,data):self.send(data,True)
	def reset(self):
		if self._rst is not _A:self._gpio.set_high(self._rst);time.sleep(.005);self._gpio.set_low(self._rst);time.sleep(.02);self._gpio.set_high(self._rst);time.sleep(.15)
	def _init(self):self.command(239);self.data(3);self.data(128);self.data(2);self.command(207);self.data(0);self.data(193);self.data(48);self.command(237);self.data(100);self.data(3);self.data(18);self.data(129);self.command(232);self.data(133);self.data(0);self.data(120);self.command(203);self.data(57);self.data(44);self.data(0);self.data(52);self.data(2);self.command(247);self.data(32);self.command(234);self.data(0);self.data(0);self.command(ILI9341_PWCTR1);self.data(35);self.command(ILI9341_PWCTR2);self.data(16);self.command(ILI9341_VMCTR1);self.data(62);self.data(40);self.command(ILI9341_VMCTR2);self.data(134);self.command(ILI9341_MADCTL);self.data(72);self.command(ILI9341_PIXFMT);self.data(85);self.command(ILI9341_FRMCTR1);self.data(0);self.data(24);self.command(ILI9341_DFUNCTR);self.data(8);self.data(130);self.data(39);self.command(242);self.data(0);self.command(ILI9341_GAMMASET);self.data(1);self.command(ILI9341_GMCTRP1);self.data(15);self.data(49);self.data(43);self.data(12);self.data(14);self.data(8);self.data(78);self.data(241);self.data(55);self.data(7);self.data(16);self.data(3);self.data(14);self.data(9);self.data(0);self.command(ILI9341_GMCTRN1);self.data(0);self.data(14);self.data(20);self.data(3);self.data(17);self.data(7);self.data(49);self.data(193);self.data(72);self.data(8);self.data(15);self.data(12);self.data(49);self.data(54);self.data(15);self.command(ILI9341_SLPOUT);time.sleep(.12);self.command(ILI9341_DISPON)
	def begin(self):self.reset();self._init()
	def set_window(self,x0=0,y0=0,x1=_A,y1=_A):
		if x1 is _A:x1=self.width-1
		if y1 is _A:y1=self.height-1
		self.command(ILI9341_CASET);self.data(x0>>8);self.data(x0);self.data(x1>>8);self.data(x1);self.command(ILI9341_PASET);self.data(y0>>8);self.data(y0);self.data(y1>>8);self.data(y1);self.command(ILI9341_RAMWR)
	def display(self,image=_A):
		if image is _A:image=self.buffer
		self.set_window();pixelbytes=list(image_to_data(image));self.data(pixelbytes)
	def clear(self,color=(0,0,0)):width,height=self.buffer.size;self.buffer.putdata([color]*(width*height))
	def draw(self):return ImageDraw.Draw(self.buffer)