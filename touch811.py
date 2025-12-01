_B='Tracking window must be in [0, 7]'
_A=None
from machine import Pin,SoftI2C
class Touch811:
	CHIP_ID=const(0);ID_VER=const(2);SYS_CTRL1=const(3);SYS_CTRL2=const(4);SPI_CFG=const(8);INT_CTL=const(9);INT_EN=const(10);INT_STA=const(11);GPIO_INT_EN=const(12);GPIO_INT_STA=const(13);ADC_INT_EN=const(10);ADC_INT_STA=const(15);TSC_CTRL=const(64);TSC_CFG=const(65);WDW_TR_X=const(66);WDW_TR_Y=const(68);WDW_BL_X=const(70);WDW_BL_Y=const(72);FIFO_TH=const(74);FIFO_STA=const(75);FIFO_SIZE=const(76);TSC_DATA_X=const(77);TSC_DATA_Y=const(79);TSC_DATA_Z=const(81);TSC_DATA_XYZ=const(87);TSC_I_DRIVE=const(88);TSC_SHIELD=const(89);TSC_FRACTION_Z=const(86);SW_RESET=const(2);CLEAR_FIFO=const(1);STMPE811_ID=const(2065);EN_TSC=const(1);CONFIG_TSC=const(228);TS_on_GPIO_off_TSC_on_ADC_on=const(4);ROTATE=0,90,180,270;SLOPE_X=const(1.13);SLOPE_Y=const(1.145);OFFSET_X=const(-15);OFFSET_Y=const(-13)
	def __init__(self,i2c_obj,i2c_address=65,x_pixels=240,y_pixels=320,rotation=0,tracking_window=6):
		self._i2c=i2c_obj;self._address=i2c_address;self._x_pix=x_pixels;self._y_pix=y_pixels;self._m_x=SLOPE_X;self._m_y=SLOPE_Y;self._b_x=OFFSET_X;self._b_y=OFFSET_Y
		if rotation in self.ROTATE:self._rotation=rotation
		else:raise ValueError('Rotation must be 0, 90, 180, or 270 degrees')
		if tracking_window in range(8):track_window=tracking_window<<4
		else:raise ValueError(_B)
		chip_id=self.i2c_read(CHIP_ID,2)
		if chip_id!=STMPE811_ID:raise RuntimeError('STMPE811 I2C Error.  Could not validate the Chip ID')
		self.i2c_write(SYS_CTRL1,SW_RESET);self.i2c_write(SYS_CTRL2,TS_on_GPIO_off_TSC_on_ADC_on);self.i2c_write(FIFO_TH,1);self.i2c_write(TSC_CFG,CONFIG_TSC);self.i2c_write(TSC_CTRL,track_window+EN_TSC)
	def is_touched(self):
		num_touches=self.i2c_read(FIFO_SIZE)
		if num_touches==0:return False
		else:return True
	def set_tsc_config(self,op_mode=0,window=_A,average=_A,touch_delay=_A,settle=_A):
		B='TSC_ctrl =';A='TSC_CFG =';tsc_cfg_val=self.i2c_read(TSC_CFG);print(A,hex(tsc_cfg_val));tsc_ctrl_val=self.i2c_read(TSC_CTRL);print(B,hex(tsc_ctrl_val))
		if op_mode in range(5):touch_mode=op_mode<<1
		else:raise ValueError('Operating Mode must be in [0, 4]')
		if window==_A:track_window=tsc_ctrl_val&112
		elif window in range(8):track_window=window<<4
		else:raise ValueError(_B)
		if average==_A:avg=tsc_cfg_val&192
		elif average in range(4):avg=average<<6
		else:raise ValueError('Average must be in [0, 3]')
		if touch_delay==_A:tch_delay=tsc_cfg_val&56
		elif touch_delay in range(8):tch_delay=touch_delay<<3
		else:raise ValueError('Touch Delay must be in [0, 7]')
		if settle==_A:settle_time=tsc_cfg_val&7
		elif settle in range(8):settle_time=settle
		else:raise ValueError('Settle Time must be in [0, 7]')
		self.i2c_write(TSC_CTRL,0);self.i2c_write(FIFO_STA,CLEAR_FIFO);self.i2c_write(TSC_CFG,avg+tch_delay+settle_time);self.i2c_write(TSC_CTRL,track_window+touch_mode+EN_TSC);tsc_cfg_val=self.i2c_read(TSC_CFG);print(A,hex(tsc_cfg_val));tsc_ctrl_val=self.i2c_read(TSC_CTRL);print(B,hex(tsc_ctrl_val))
	def get_num_touches(self):num_touches=self.i2c_read(FIFO_SIZE);return num_touches
	def get_xyz_touch_points(self):
		num_touches=self.i2c_read(FIFO_SIZE);touches=[]
		while num_touches>0:
			x_raw=self.i2c_read(TSC_DATA_X,2);y_raw=self.i2c_read(TSC_DATA_Y,2);pressure_raw=self.i2c_read(TSC_DATA_Z,2)
			if self._rotation==0:touches.append([self._x_pix-int(x_raw/4095*self._x_pix*self._m_x+self._b_x),self._y_pix-int(y_raw/4095*self._y_pix*self._m_y+self._b_y),pressure_raw/255])
			elif self._rotation==90:touches.append([self._y_pix-int(y_raw/4095*self._y_pix*self._m_y+self._b_y),int(x_raw/4095*self._x_pix*self._m_x+self._b_x),pressure_raw/255])
			elif self._rotation==180:touches.append([int(x_raw/4095*self._x_pix*self._m_x+self._b_x),int(y_raw/4095*self._y_pix*self._m_y+self._b_y),pressure_raw/255])
			else:touches.append([int(y_raw/4095*self._y_pix*self._m_y+self._b_y),self._x_pix-int(x_raw/4095*self._x_pix*self._m_x+self._b_x),pressure_raw/255])
			num_touches=self.i2c_read(FIFO_SIZE)
		return touches
	def get_xyz_unique(self,deviation=5):
		all_touches=self.get_xyz_touch_points()
		if len(all_touches)!=0:return self.check_xy_match(all_touches,deviation)
		else:return all_touches
	def check_xy_match(self,list_touch_points,delta_xy=5):
		all_unique=[];unique_xyz=list_touch_points[0][:];all_unique.append(unique_xyz[:])
		for ii in range(1,len(list_touch_points)):
			next_xyz=list_touch_points[ii][:]
			if abs(unique_xyz[0]-next_xyz[0])>delta_xy or abs(unique_xyz[1]-next_xyz[1])>delta_xy:all_unique.append(next_xyz);unique_xyz=next_xyz[:]
		return all_unique
	def i2c_read(self,reg,bytes=1):
		if bytes in[1,2,3,4]:
			_=self._i2c.writeto(self._address,bytearray([reg]));data=self._i2c.readfrom(self._address,bytes)
			if bytes==1:value=data[0]
			elif bytes==2:value=data[0]<<8|data[1]
			elif bytes==3:value=data[0]<<16|data[1]<<8|data[2]
			else:value=data[0]<<24|data[1]<<16|data[2]<<8|data[3]
		else:raise ValueError('Byte Error');value=-1
		return value
	def i2c_write(self,reg,value):return_value=self._i2c.writeto(self._address,bytearray([reg,value]))