_A=False
from math import ceil,floor
class XglcdFont:
	BIT_POS={1:0,2:2,4:4,8:6,16:8,32:10,64:12,128:14,256:16}
	def __init__(self,path,width,height,start_letter=32,letter_count=96,is_freezable_font=_A):
		self.width=width;self.height=max(height,8);self.start_letter=start_letter;self.letter_count=letter_count;self.bytes_per_letter=(floor((self.height-1)/8)+1)*self.width+1
		if is_freezable_font==_A:self.__load_xglcd_font(path)
		else:self.letters=bytearray(self.bytes_per_letter*self.letter_count)
	def __load_xglcd_font(self,path):
		bytes_per_letter=self.bytes_per_letter;self.letters=bytearray(bytes_per_letter*self.letter_count);mv=memoryview(self.letters);offset=0
		with open(path,'r')as f:
			for line in f:
				line=line.strip()
				if len(line)==0 or line[0:2]!='0x':continue
				comment=line.find('//')
				if comment!=-1:line=line[0:comment].strip()
				if line.endswith(','):line=line[0:len(line)-1]
				mv[offset:offset+bytes_per_letter]=bytearray(int(b,16)for b in line.split(','));offset+=bytes_per_letter
	def lit_bits(self,n):
		while n:b=n&~n+1;yield self.BIT_POS[b];n^=b
	def get_letter(self,letter,color,background=0,landscape=_A):
		A='big';letter_ord=ord(letter)-self.start_letter
		if letter_ord>=self.letter_count:print('Font does not contain character: '+letter);return b'',0,0
		bytes_per_letter=self.bytes_per_letter;offset=letter_ord*bytes_per_letter;mv=memoryview(self.letters[offset:offset+bytes_per_letter]);letter_width=mv[0];letter_height=self.height;letter_size=letter_height*letter_width
		if background:buf=bytearray(background.to_bytes(2,A)*letter_size)
		else:buf=bytearray(letter_size*2)
		msb,lsb=color.to_bytes(2,A)
		if landscape:
			pos=letter_size*2-letter_height*2;lh=letter_height
			for b in mv[1:]:
				for bit in self.lit_bits(b):buf[bit+pos]=msb;buf[bit+pos+1]=lsb
				if lh>8:pos+=16;lh-=8
				else:pos-=letter_height*4-lh*2;lh=letter_height
		else:
			col=0;bytes_per_letter=ceil(letter_height/8);letter_byte=0
			for b in mv[1:]:
				segment_size=letter_byte*letter_width*16
				for bit in self.lit_bits(b):pos=bit*letter_width+col*2+segment_size;buf[pos]=msb;pos=bit*letter_width+col*2+1+segment_size;buf[pos]=lsb
				letter_byte+=1
				if letter_byte+1>bytes_per_letter:col+=1;letter_byte=0
		return buf,letter_width,letter_height
	def measure_text(self,text,spacing=1):
		length=0
		for letter in text:letter_ord=ord(letter)-self.start_letter;offset=letter_ord*self.bytes_per_letter;length+=self.letters[offset]+spacing
		return length