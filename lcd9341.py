_C='big'
_B=False
_A=True
from time import sleep
from math import cos,sin,pi,radians
from sys import implementation
from framebuf import FrameBuffer,RGB565
import ustruct
def color565(r,g,b):return(r&248)<<8|(g&252)<<3|b>>3
class LCD9341:
	NOP=const(0);SWRESET=const(1);RDDID=const(4);RDDST=const(9);SLPIN=const(16);SLPOUT=const(17);PTLON=const(18);NORON=const(19);RDMODE=const(10);RDMADCTL=const(11);RDPIXFMT=const(12);RDIMGFMT=const(13);RDSELFDIAG=const(15);INVOFF=const(32);INVON=const(33);GAMMASET=const(38);DISPLAY_OFF=const(40);DISPLAY_ON=const(41);SET_COLUMN=const(42);SET_PAGE=const(43);WRITE_RAM=const(44);READ_RAM=const(46);PTLAR=const(48);VSCRDEF=const(51);MADCTL=const(54);VSCRSADD=const(55);PIXFMT=const(58);WRITE_DISPLAY_BRIGHTNESS=const(81);READ_DISPLAY_BRIGHTNESS=const(82);WRITE_CTRL_DISPLAY=const(83);READ_CTRL_DISPLAY=const(84);WRITE_CABC=const(85);READ_CABC=const(86);WRITE_CABC_MINIMUM=const(94);READ_CABC_MINIMUM=const(95);FRMCTR1=const(177);FRMCTR2=const(178);FRMCTR3=const(179);INVCTR=const(180);DFUNCTR=const(182);PWCTR1=const(192);PWCTR2=const(193);PWCTRA=const(203);PWCTRB=const(207);VMCTR1=const(197);VMCTR2=const(199);RDID1=const(218);RDID2=const(219);RDID3=const(220);RDID4=const(221);GMCTRP1=const(224);GMCTRN1=const(225);DTCA=const(232);DTCB=const(234);POSC=const(237);ENABLE3G=const(242);PUMPRC=const(247);ROTATE={0:136,90:232,180:72,270:40}
	def __init__(self,spi,cs,dc,rst,width=240,height=320,rotation=0):
		self.spi=spi;self.cs=cs;self.dc=dc;self.rst=rst;self.width=width;self.height=height
		if rotation not in self.ROTATE.keys():raise RuntimeError('Rotation must be 0, 90, 180 or 270.')
		else:self.rotation=self.ROTATE[rotation]
		self.ba_SET_COLUMN=bytearray([SET_COLUMN]);self.ba_SET_PAGE=bytearray([SET_PAGE]);self.ba_WRITE_RAM=bytearray([WRITE_RAM]);self.cas=bytearray(4);self.pas=bytearray(4)
		if implementation.name=='circuitpython':self.cs.switch_to_output(value=_A);self.dc.switch_to_output(value=_B);self.rst.switch_to_output(value=_A);self.reset=self.reset_cpy;self.write_cmd=self.write_cmd_cpy;self.write_data=self.write_data_cpy
		else:self.cs.init(self.cs.OUT,value=1);self.dc.init(self.dc.OUT,value=0);self.rst.init(self.rst.OUT,value=1);self.reset=self.reset_mpy;self.write_cmd=self.write_cmd_mpy;self.write_data=self.write_data_mpy
		self.reset();self.write_cmd(self.SWRESET);sleep(.1);self.write_cmd(self.PWCTRB,0,193,48);self.write_cmd(self.POSC,100,3,18,129);self.write_cmd(self.DTCA,133,0,120);self.write_cmd(self.PWCTRA,57,44,0,52,2);self.write_cmd(self.PUMPRC,32);self.write_cmd(self.DTCB,0,0);self.write_cmd(self.PWCTR1,35);self.write_cmd(self.PWCTR2,16);self.write_cmd(self.VMCTR1,62,40);self.write_cmd(self.VMCTR2,134);self.write_cmd(self.MADCTL,self.rotation);self.write_cmd(self.VSCRSADD,0);self.write_cmd(self.PIXFMT,85);self.write_cmd(self.FRMCTR1,0,24);self.write_cmd(self.DFUNCTR,8,130,39);self.write_cmd(self.ENABLE3G,0);self.write_cmd(self.GAMMASET,1);self.write_cmd(self.GMCTRP1,15,49,43,12,14,8,78,241,55,7,16,3,14,9,0);self.write_cmd(self.GMCTRN1,0,14,20,3,17,7,49,193,72,8,15,12,49,54,15);self.write_cmd(self.SLPOUT);sleep(.1);self.write_cmd(self.DISPLAY_ON);sleep(.1);self.clear()
	def block(self,x0,y0,x1,y1,data):self.cas[0]=x0>>8;self.cas[1]=x0&255;self.cas[2]=x1>>8;self.cas[3]=x1&255;self.pas[0]=y0>>8;self.pas[1]=y0&255;self.pas[2]=y1>>8;self.pas[3]=y1&255;self.cs(1);self.dc(0);self.cs(0);self.spi.write(self.ba_SET_COLUMN);self.cs(1);self.dc(1);self.cs(0);self.spi.write(self.cas);self.cs(1);self.dc(0);self.cs(0);self.spi.write(self.ba_SET_PAGE);self.cs(1);self.dc(1);self.cs(0);self.spi.write(self.pas);self.cs(1);self.dc(0);self.cs(0);self.spi.write(self.ba_WRITE_RAM);self.cs(1);self.dc(1);self.cs(0);self.spi.write(data)
	def cleanup(self):self.clear();self.display_off();self.spi.deinit();print('display off')
	def clear(self,color=0,hlines=4):
		w=self.width;h=self.height
		if color:line=color.to_bytes(2,_C)*(w*hlines)
		else:line=bytearray(w*2*hlines)
		for y in range(0,h,hlines):self.block(0,y,w-1,y+hlines-1,line)
	def display_off(self):self.write_cmd(self.DISPLAY_OFF)
	def display_on(self):self.write_cmd(self.DISPLAY_ON)
	def draw_circle(self,x0,y0,r,color):
		f=1-r;dx=1;dy=-r-r;x=0;y=r;self.draw_pixel(x0,y0+r,color);self.draw_pixel(x0,y0-r,color);self.draw_pixel(x0+r,y0,color);self.draw_pixel(x0-r,y0,color)
		while x<y:
			if f>=0:y-=1;dy+=2;f+=dy
			x+=1;dx+=2;f+=dx;self.draw_pixel(x0+x,y0+y,color);self.draw_pixel(x0-x,y0+y,color);self.draw_pixel(x0+x,y0-y,color);self.draw_pixel(x0-x,y0-y,color);self.draw_pixel(x0+y,y0+x,color);self.draw_pixel(x0-y,y0+x,color);self.draw_pixel(x0+y,y0-x,color);self.draw_pixel(x0-y,y0-x,color)
	def draw_ellipse(self,x0,y0,a,b,color):
		a2=a*a;b2=b*b;twoa2=a2+a2;twob2=b2+b2;x=0;y=b;px=0;py=twoa2*y;self.draw_pixel(x0+x,y0+y,color);self.draw_pixel(x0-x,y0+y,color);self.draw_pixel(x0+x,y0-y,color);self.draw_pixel(x0-x,y0-y,color);p=round(b2-a2*b+.25*a2)
		while px<py:
			x+=1;px+=twob2
			if p<0:p+=b2+px
			else:y-=1;py-=twoa2;p+=b2+px-py
			self.draw_pixel(x0+x,y0+y,color);self.draw_pixel(x0-x,y0+y,color);self.draw_pixel(x0+x,y0-y,color);self.draw_pixel(x0-x,y0-y,color)
		p=round(b2*(x+.5)*(x+.5)+a2*(y-1)*(y-1)-a2*b2)
		while y>0:
			y-=1;py-=twoa2
			if p>0:p+=a2-py
			else:x+=1;px+=twob2;p+=a2-py+px
			self.draw_pixel(x0+x,y0+y,color);self.draw_pixel(x0-x,y0+y,color);self.draw_pixel(x0+x,y0-y,color);self.draw_pixel(x0-x,y0-y,color)
	def draw_hline(self,x,y,w,color):
		if self.is_off_grid(x,y,x+w-1,y):return
		line=color.to_bytes(2,_C)*w;self.block(x,y,x+w-1,y,line)
	def draw_image(self,path,x=0,y=0,w=320,h=240):
		x2=x+w-1;y2=y+h-1
		if self.is_off_grid(x,y,x2,y2):return
		with open(path,'rb')as f:
			chunk_height=1024//w;chunk_count,remainder=divmod(h,chunk_height);chunk_size=chunk_height*w*2;chunk_y=y
			if chunk_count:
				for c in range(0,chunk_count):buf=f.read(chunk_size);self.block(x,chunk_y,x2,chunk_y+chunk_height-1,buf);chunk_y+=chunk_height
			if remainder:buf=f.read(remainder*w*2);self.block(x,chunk_y,x2,chunk_y+remainder-1,buf)
	def draw_letter(self,x,y,letter,font,color,background=0,landscape=_B):
		buf,w,h=font.get_letter(letter,color,background,landscape)
		if w==0:return w,h
		if landscape:
			y-=w
			if self.is_off_grid(x,y,x+h-1,y+w-1):return 0,0
			self.block(x,y,x+h-1,y+w-1,buf)
		else:
			if self.is_off_grid(x,y,x+w-1,y+h-1):return 0,0
			self.block(x,y,x+w-1,y+h-1,buf)
		return w,h
	def draw_line(self,x1,y1,x2,y2,color):
		if y1==y2:
			if x1>x2:x1,x2=x2,x1
			self.draw_hline(x1,y1,x2-x1+1,color);return
		if x1==x2:
			if y1>y2:y1,y2=y2,y1
			self.draw_vline(x1,y1,y2-y1+1,color);return
		if self.is_off_grid(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)):return
		dx=x2-x1;dy=y2-y1;is_steep=abs(dy)>abs(dx)
		if is_steep:x1,y1=y1,x1;x2,y2=y2,x2
		if x1>x2:x1,x2=x2,x1;y1,y2=y2,y1
		dx=x2-x1;dy=y2-y1;error=dx>>1;ystep=1 if y1<y2 else-1;y=y1
		for x in range(x1,x2+1):
			if not is_steep:self.draw_pixel(x,y,color)
			else:self.draw_pixel(y,x,color)
			error-=abs(dy)
			if error<0:y+=ystep;error+=dx
	def draw_lines(self,coords,color):
		x1,y1=coords[0]
		for i in range(1,len(coords)):x2,y2=coords[i];self.draw_line(x1,y1,x2,y2,color);x1,y1=x2,y2
	def draw_pixel(self,x,y,color):
		if self.is_off_grid(x,y,x,y):return
		self.block(x,y,x,y,color.to_bytes(2,_C))
	def draw_polygon(self,sides,x0,y0,r,color,rotate=0):
		coords=[];theta=radians(rotate);n=sides+1
		for s in range(n):t=2.*pi*s/sides+theta;coords.append([int(r*cos(t)+x0),int(r*sin(t)+y0)])
		self.draw_lines(coords,color=color)
	def draw_rectangle(self,x,y,w,h,color):x2=x+w-1;y2=y+h-1;self.draw_hline(x,y,w,color);self.draw_hline(x,y2,w,color);self.draw_vline(x,y,h,color);self.draw_vline(x2,y,h,color)
	def draw_sprite(self,buf,x,y,w,h):
		x2=x+w-1;y2=y+h-1
		if self.is_off_grid(x,y,x2,y2):return
		self.block(x,y,x2,y2,buf)
	def draw_text(self,x,y,text,font,color,background=0,landscape=_B,spacing=1):
		for letter in text:
			w,h=self.draw_letter(x,y,letter,font,color,background,landscape)
			if w==0 or h==0:print('Invalid width {0} or height {1}'.format(w,h));return
			if landscape:
				if spacing:self.fill_hrect(x,y-w-spacing,h,spacing,background)
				y-=w+spacing
			else:
				if spacing:self.fill_hrect(x+w,y,spacing,h,background)
				x+=w+spacing
	def draw_text8x8(self,x,y,text,color,background=0,rotate=0):
		w=len(text)*8;h=8
		if self.is_off_grid(x,y,x+7,y+7):return
		r=(color&63488)>>8;g=(color&2016)>>3;b=(color&31)<<3;buf=bytearray(w*16);fbuf=FrameBuffer(buf,w,h,RGB565)
		if background!=0:bg_r=(background&63488)>>8;bg_g=(background&2016)>>3;bg_b=(background&31)<<3;fbuf.fill(color565(bg_b,bg_r,bg_g))
		fbuf.text(text,0,0,color565(b,r,g))
		if rotate==0:self.block(x,y,x+w-1,y+(h-1),buf)
		elif rotate==90:
			buf2=bytearray(w*16);fbuf2=FrameBuffer(buf2,h,w,RGB565)
			for y1 in range(h):
				for x1 in range(w):fbuf2.pixel(y1,x1,fbuf.pixel(x1,h-1-y1))
			self.block(x,y,x+(h-1),y+w-1,buf2)
		elif rotate==180:
			buf2=bytearray(w*16);fbuf2=FrameBuffer(buf2,w,h,RGB565)
			for y1 in range(h):
				for x1 in range(w):fbuf2.pixel(x1,y1,fbuf.pixel(w-1-x1,h-1-y1))
			self.block(x,y,x+w-1,y+(h-1),buf2)
		elif rotate==270:
			buf2=bytearray(w*16);fbuf2=FrameBuffer(buf2,h,w,RGB565)
			for y1 in range(h):
				for x1 in range(w):fbuf2.pixel(y1,x1,fbuf.pixel(w-1-x1,y1))
			self.block(x,y,x+(h-1),y+w-1,buf2)
	def draw_vline(self,x,y,h,color):
		if self.is_off_grid(x,y,x,y+h-1):return
		line=color.to_bytes(2,_C)*h;self.block(x,y,x,y+h-1,line)
	def fill_circle(self,x0,y0,r,color):
		f=1-r;dx=1;dy=-r-r;x=0;y=r;self.draw_vline(x0,y0-r,2*r+1,color)
		while x<y:
			if f>=0:y-=1;dy+=2;f+=dy
			x+=1;dx+=2;f+=dx;self.draw_vline(x0+x,y0-y,2*y+1,color);self.draw_vline(x0-x,y0-y,2*y+1,color);self.draw_vline(x0-y,y0-x,2*x+1,color);self.draw_vline(x0+y,y0-x,2*x+1,color)
	def fill_ellipse(self,x0,y0,a,b,color):
		a2=a*a;b2=b*b;twoa2=a2+a2;twob2=b2+b2;x=0;y=b;px=0;py=twoa2*y;self.draw_line(x0,y0-y,x0,y0+y,color);p=round(b2-a2*b+.25*a2)
		while px<py:
			x+=1;px+=twob2
			if p<0:p+=b2+px
			else:y-=1;py-=twoa2;p+=b2+px-py
			self.draw_line(x0+x,y0-y,x0+x,y0+y,color);self.draw_line(x0-x,y0-y,x0-x,y0+y,color)
		p=round(b2*(x+.5)*(x+.5)+a2*(y-1)*(y-1)-a2*b2)
		while y>0:
			y-=1;py-=twoa2
			if p>0:p+=a2-py
			else:x+=1;px+=twob2;p+=a2-py+px
			self.draw_line(x0+x,y0-y,x0+x,y0+y,color);self.draw_line(x0-x,y0-y,x0-x,y0+y,color)
	def fill_hrect(self,x,y,w,h,color):
		if self.is_off_grid(x,y,x+w-1,y+h-1):return
		chunk_height=1024//w;chunk_count,remainder=divmod(h,chunk_height);chunk_size=chunk_height*w;chunk_y=y
		if chunk_count:
			buf=color.to_bytes(2,_C)*chunk_size
			for c in range(0,chunk_count):self.block(x,chunk_y,x+w-1,chunk_y+chunk_height-1,buf);chunk_y+=chunk_height
		if remainder:buf=color.to_bytes(2,_C)*remainder*w;self.block(x,chunk_y,x+w-1,chunk_y+remainder-1,buf)
	def fill_rectangle(self,x,y,w,h,color):
		if self.is_off_grid(x,y,x+w-1,y+h-1):return
		if w>h:self.fill_hrect(x,y,w,h,color)
		else:self.fill_vrect(x,y,w,h,color)
	def fill_polygon(self,sides,x0,y0,r,color,rotate=0):
		coords=[];theta=radians(rotate);n=sides+1
		for s in range(n):t=2.*pi*s/sides+theta;coords.append([int(r*cos(t)+x0),int(r*sin(t)+y0)])
		x1,y1=coords[0];xdict={y1:[x1,x1]}
		for row in coords[1:]:
			x2,y2=row;xprev,yprev=x2,y2
			if y1==y2:
				if x1>x2:x1,x2=x2,x1
				if y1 in xdict:xdict[y1]=[min(x1,xdict[y1][0]),max(x2,xdict[y1][1])]
				else:xdict[y1]=[x1,x2]
				x1,y1=xprev,yprev;continue
			dx=x2-x1;dy=y2-y1;is_steep=abs(dy)>abs(dx)
			if is_steep:x1,y1=y1,x1;x2,y2=y2,x2
			if x1>x2:x1,x2=x2,x1;y1,y2=y2,y1
			dx=x2-x1;dy=y2-y1;error=dx>>1;ystep=1 if y1<y2 else-1;y=y1
			for x in range(x1,x2+1):
				if is_steep:
					if x in xdict:xdict[x]=[min(y,xdict[x][0]),max(y,xdict[x][1])]
					else:xdict[x]=[y,y]
				elif y in xdict:xdict[y]=[min(x,xdict[y][0]),max(x,xdict[y][1])]
				else:xdict[y]=[x,x]
				error-=abs(dy)
				if error<0:y+=ystep;error+=dx
			x1,y1=xprev,yprev
		for(y,x)in xdict.items():self.draw_hline(x[0],y,x[1]-x[0]+2,color)
	def fill_vrect(self,x,y,w,h,color):
		if self.is_off_grid(x,y,x+w-1,y+h-1):return
		chunk_width=1024//h;chunk_count,remainder=divmod(w,chunk_width);chunk_size=chunk_width*h;chunk_x=x
		if chunk_count:
			buf=color.to_bytes(2,_C)*chunk_size
			for c in range(0,chunk_count):self.block(chunk_x,y,chunk_x+chunk_width-1,y+h-1,buf);chunk_x+=chunk_width
		if remainder:buf=color.to_bytes(2,_C)*remainder*h;self.block(chunk_x,y,chunk_x+remainder-1,y+h-1,buf)
	def is_off_grid(self,xmin,ymin,xmax,ymax):
		if xmin<0:print('x-coordinate: {0} below minimum of 0.'.format(xmin));return _A
		if ymin<0:print('y-coordinate: {0} below minimum of 0.'.format(ymin));return _A
		if xmax>=self.width:print('x-coordinate: {0} above maximum of {1}.'.format(xmax,self.width-1));return _A
		if ymax>=self.height:print('y-coordinate: {0} above maximum of {1}.'.format(ymax,self.height-1));return _A
		return _B
	def load_sprite(self,path,w,h):
		buf_size=w*h*2
		with open(path,'rb')as f:return f.read(buf_size)
	def reset_cpy(self):self.rst.value=_B;sleep(.05);self.rst.value=_A;sleep(.05)
	def reset_mpy(self):self.rst(0);sleep(.05);self.rst(1);sleep(.05)
	def scroll(self,y):self.write_cmd(self.VSCRSADD,y>>8,y&255)
	def set_scroll(self,top,bottom):
		if top+bottom<=self.height:middle=self.height-(top+bottom);print(top,middle,bottom);self.write_cmd(self.VSCRDEF,top>>8,top&255,middle>>8,middle&255,bottom>>8,bottom&255)
	def sleep(self,enable=_A):
		if enable:self.write_cmd(self.SLPIN)
		else:self.write_cmd(self.SLPOUT)
	def write_cmd_mpy(self,command,*args):
		self.dc(0);self.cs(0);self.spi.write(bytearray([command]));self.cs(1)
		if len(args)>0:self.write_data(bytearray(args))
	def write_cmd_cpy(self,command,*args):
		self.dc.value=_B;self.cs.value=_B
		while not self.spi.try_lock():0
		self.spi.write(bytearray([command]));self.spi.unlock();self.cs.value=_A
		if len(args)>0:self.write_data(bytearray(args))
	def write_data_mpy(self,data):self.dc(1);self.cs(0);self.spi.write(data);self.cs(1)
	def write_data_cpy(self,data):
		self.dc.value=_A;self.cs.value=_B
		while not self.spi.try_lock():0
		self.spi.write(data);self.spi.unlock();self.cs.value=_A