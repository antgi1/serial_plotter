import serial
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as Canvas, NavigationToolbar2QT as NavigationToolbar2)
#from matplotlib import rcParams,gridspec
import time
import re

import win32clipboard as clipboard
LengthSaved = 10000

class NavigationToolbar(NavigationToolbar2):
	def press_pan(self, event):
		"""the press mouse button in pan/zoom mode callback"""
		"""  event: 1,2,3=left,middle,right.  button_pressed: 1,3= normal drag, zoombehaviour,as defined on thhe library"""
		if event.button == 2:
			self._button_pressed = 3
		elif event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return

		x, y = event.x, event.y

		# push the current view to define home if stack is empty
		if self._views.empty():
			self.push_current()

		self._xypress = []
		for i, a in enumerate(self.canvas.figure.get_axes()):
			if (x is not None and y is not None and a.in_axes(event) and
					a.get_navigate() and a.can_pan()):
				a.start_pan(x, y, event.button)
				self._xypress.append((a, i))
				self.canvas.mpl_disconnect(self._idDrag)
				self._idDrag = self.canvas.mpl_connect('motion_notify_event',
													   self.drag_pan)

		self.press(event)	
		
	def press_zoom(self, event):
		"""the press mouse button in zoom to rect mode callback"""
		# If we're already in the middle of a zoom, pressing another
		# button works to "cancel"
		if self._ids_zoom != []:
			for zoom_id in self._ids_zoom:
				self.canvas.mpl_disconnect(zoom_id)
			self.release(event)
			self.draw()
			self._xypress = None
			self._button_pressed = None
			self._ids_zoom = []
			return

		if event.button == 2:
			self._button_pressed = 3
		elif event.button == 1:
			self._button_pressed = 1
		else:
			self._button_pressed = None
			return

		x, y = event.x, event.y

		# push the current view to define home if stack is empty
		if self._views.empty():
			self.push_current()

		self._xypress = []
		for i, a in enumerate(self.canvas.figure.get_axes()):
			if (x is not None and y is not None and a.in_axes(event) and
					a.get_navigate() and a.can_zoom()):
				self._xypress.append((x, y, a, i, a.viewLim.frozen(),
									  a.transData.frozen()))

		id1 = self.canvas.mpl_connect('motion_notify_event', self.drag_zoom)
		id2 = self.canvas.mpl_connect('key_press_event',
									  self._switch_on_zoom_mode)
		id3 = self.canvas.mpl_connect('key_release_event',
									  self._switch_off_zoom_mode)

		self._ids_zoom = id1, id2, id3
		self._zoom_mode = event.key

		self.press(event)		
		
def availableSerialPort():
	suffixes = "S", "USB", "ACM", "AMA"
	nameList = ["com"] + ["/dev/tty%s" % suffix for suffix in suffixes]
	portList = []	
	for name in nameList:
		for number in range(48):
			portName = "%s%s" % (name, number)
			try:
				serial.Serial(portName).close()
				portList.append(portName)
			except IOError:
				pass
	return portList

class ser(QThread):
	def __init__(self): 
		self.old=[]
		self.data=[]
		QThread.__init__(self)
		if str(ui.ComcomboBox.currentText())!="":
			self.current=None 
		#	self.current=serial.Serial(str(ui.ComcomboBox.currentText()),int(ui.BaudcomboBox.currentText()),8,"N",1,timeout=1)

		else:
			self.current=None 
	def changecom(self):
		try:
			self.current.close()
		except:
			# print("error closing the port")
			pass
		if str(ui.ComcomboBox.currentText())!="":
			self.current=serial.Serial(str(ui.ComcomboBox.currentText()),int(ui.BaudcomboBox.currentText()),8,"N",1,timeout=1)	
		else:
			pass
			
	def killit(self):
		try:
			self.current.close()		
		except:
			# print("error closing the port")
			pass
	def sendmsg(self, msg):

		try :#if ((str(ui.ComcomboBox.currentText())!="") & (self.current!=None)): 
			for element in msg:
				self.current.write(element)	
			self.start()
		except:#else:
			# print("error communicating to port")
			pass
			
	def makemsg(self, msg):
		self.endings={"NONE":"","NL":"\n","CR":"\r","NL & CR":"\n\r"}
		self.newmsg = msg + self.endings[str(ui.EndcomboBox.currentText())]
		self.sendmsg(str(self.newmsg))		
			
	def run(self): 
		global LengthSaved

		while  1:
			try:
				self.inmsg=self.current.readline() 
				self.raw=re.split("[\t]{1,}|[ ]{1,}|,",self.inmsg)
				self.new=[]
				for a in self.raw:
					if a=="":
						pass
					else:
						self.new.append(float(a))	

				if ((len(self.old)==len(self.new))&(len(self.data)!=0)):					
					self.data[-1].append(time.time()-self.beginning)
					for i in range(len(self.new)):	
						self.data[i].append(self.new[i])
					if len(self.data)>=LengthSaved:								
						for i in range(len(self.new)+1):
							self.data[i].pop(0)		
					self.old=self.new[:]
					self.emit(SIGNAL(("changeit()")))					
	
					
				elif (len(self.new)!=0)| (len(self.data)==0):
					self.beginning=time.time()
					self.data=[]
					for i in range(len(self.new)+1):
						self.data.append([])
					self.data[-1].append(0)
					for i in range(len(self.new)):	
						self.data[i].append(self.new[i])	
					self.old=self.new[:]						
					self.emit(SIGNAL(("drawit()")))
												

				
			except:
				break
  		
				
class MatplotlibWidget(Canvas):
	
	def __init__(self, parent=None, title='', xlabel='', ylabel='',
				 xlim=None, ylim=None, xscale='linear', yscale='linear',
				 width=4, height=3, dpi=100, hold=False):   
		self.figure = Figure(figsize=(width, height), dpi=dpi)
		Canvas.__init__(self, self.figure)
		self.setParent(parent)
		self.state= ''	
		Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
		Canvas.updateGeometry(self)		
		self.checkX=True
		self.checkY=True
		self.AutoY=None
		self.AutoX=None
		
	def changeit(self):	
		for i in range(len(ui.serial.old)):
			self.graph[i].set_ydata(ui.serial.data[i])
			self.graph[i].set_xdata(ui.serial.data[-1])
			
		if self.AutoX==None:
			try:
				self.flat = [item for sublist in ui.serial.data[0:-1] for item in sublist]
				self.axis.set_ylim(min(self.flat),max(self.flat))		
				self.axis.set_xlim(min(ui.serial.data[-1])-(max(ui.serial.data[-1])-min(ui.serial.data[-1]))*0.01,max(ui.serial.data[-1])+(max(ui.serial.data[-1])-min(ui.serial.data[-1]))*0.01)		
			except:
				pass
		else:
			if self.AutoY.isChecked():
				self.flat = [item for sublist in ui.serial.data[0:-1] for item in sublist]
				self.axis.set_ylim(min(self.flat)-(max(self.flat)-min(self.flat))*0.1,max(self.flat)+(max(self.flat)-min(self.flat))*0.1)		
			if self.AutoX.isChecked():
				self.axis.set_xlim(min(ui.serial.data[-1])-(max(ui.serial.data[-1])-min(ui.serial.data[-1]))*0.01,max(ui.serial.data[-1])+(max(ui.serial.data[-1])-min(ui.serial.data[-1]))*0.01)		

			
		self.figure.canvas.draw()
		self.figure.canvas.flush_events() 

		
	def drawit(self):	

#	everytime you connect you remake the whole plot
	
		self.figure.clear()		
		self.axis=self.figure.add_subplot(111)	 
		self.graph=[]
		for i in range(len(ui.serial.old)):

			self.graph.append([])
			self.graph[i], =self.axis.plot(ui.serial.data[-1],ui.serial.data[i])	
			
	#	self.axis.set_xlabel("Time [s]", fontsize = 10)
		self.axis.grid(b=True)
		self.figure.tight_layout( h_pad=0)	
	#	if (len(ui.serial.data[-1])>4):
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()
			
		
	def contextMenuEvent(self, event):
		try:
			menu = QMenu(self)
			copyAll = menu.addAction("Copy all")
			self.AutoX = menu.addAction("Autoscale X-axis")
			self.AutoY = menu.addAction("Autoscale Y-axis")
			self.AutoX.setCheckable(True)
			self.AutoY.setCheckable(True)
			self.AutoX.setChecked(self.checkX)
			self.AutoY.setChecked(self.checkY)
			action = menu.exec_(self.mapToGlobal(event.pos()))
			
			if action == self.AutoX:
				self.checkX = not self.checkX
			if action == self.AutoY:
				self.checkY = not self.checkY
			if action == copyAll:
				if len(ui.serial.data)!=0:
					self.toClipboard()
		except:
			print("context menu error")
			pass
			
	def toClipboard(self):
	# Create string from array
		line_strings = []
		for line in map(list,zip(*(ui.serial.data[-1:]+ui.serial.data[:-1]))):
			line_strings.append("\t".join([str(round(i,3)) for i in line]).replace("\n",""))
		array_string = "\r\n".join(line_strings)
	# Put string into clipboard (open, clear, set, close)
		clipboard.OpenClipboard()
		clipboard.EmptyClipboard()
		clipboard.SetClipboardText(array_string)
		clipboard.CloseClipboard()

	
class Ui_SerialPlotter(object):
	def setupUi(self, SerialPlotter):
		self.pressed=False
		
		SerialPlotter.setObjectName(("SerialPlotter"))
		SerialPlotter.resize(629, 478)
		sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(SerialPlotter.sizePolicy().hasHeightForWidth())
		SerialPlotter.setSizePolicy(sizePolicy)
		SerialPlotter.setWindowOpacity(1.0)
		self.centralwidget = QWidget(SerialPlotter)
		self.centralwidget.setObjectName(("centralwidget"))
		self.verticalLayout = QVBoxLayout(self.centralwidget)
		self.verticalLayout.setObjectName(("verticalLayout"))
		self.horizontalLayout = QHBoxLayout()
		self.horizontalLayout.setObjectName(("horizontalLayout"))
		self.InputlineEdit = QLineEdit(self.centralwidget)
		sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		sizePolicy.setHorizontalStretch(0)
		sizePolicy.setVerticalStretch(0)
		sizePolicy.setHeightForWidth(self.InputlineEdit.sizePolicy().hasHeightForWidth())
		self.InputlineEdit.setSizePolicy(sizePolicy)
		self.InputlineEdit.setMinimumSize(QSize(0, 27))
		font = QFont()
		font.setPointSize(10)
		self.InputlineEdit.setFont(font)
		self.InputlineEdit.setObjectName(("InputlineEdit"))
		self.InputlineEdit.setFocusPolicy(Qt.ClickFocus)
		self.horizontalLayout.addWidget(self.InputlineEdit)
		self.SendButton = QPushButton(self.centralwidget)
		self.SendButton.setObjectName(("SendButton"))
		self.horizontalLayout.addWidget(self.SendButton)
		self.verticalLayout.addLayout(self.horizontalLayout)
		
		self.mplwidget = MatplotlibWidget(self.centralwidget)
		self.mplwidget.setObjectName(("mplwidget"))
		
		self.verticalLayout.addWidget(self.mplwidget)
		self.horizontalLayout_3 = QHBoxLayout()
		self.horizontalLayout_3.setContentsMargins(-1, -1, -1, 0)
		self.horizontalLayout_3.setObjectName(("horizontalLayout_3"))
		
		self.toolbar =NavigationToolbar(self.mplwidget, self.centralwidget)
		self.toolbar.setObjectName(("toolbar"))
		self.horizontalLayout_3.addWidget(self.toolbar)
		
		spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.horizontalLayout_3.addItem(spacerItem)
		
		self.ComcomboBox = QComboBox(self.centralwidget)
		self.ComcomboBox.setObjectName(("ComcomboBox"))
		self.ComcomboBox.addItem((""))
		self.horizontalLayout_3.addWidget(self.ComcomboBox)
		self.BaudcomboBox = QComboBox(self.centralwidget)
		self.BaudcomboBox.setObjectName(("BaudcomboBox"))
		self.BaudcomboBox.addItem((""))
		self.horizontalLayout_3.addWidget(self.BaudcomboBox)
		self.EndcomboBox = QComboBox(self.centralwidget)
		self.EndcomboBox.setObjectName(("EndcomboBox"))
		self.EndcomboBox.addItem((""))
		self.horizontalLayout_3.addWidget(self.EndcomboBox)
		self.ConnectButton = QPushButton(self.centralwidget)
		self.ConnectButton.setObjectName(("ConnectButton"))
		self.ConnectButton.setStyleSheet("background : green")
		self.horizontalLayout_3.addWidget(self.ConnectButton)
		self.verticalLayout.addLayout(self.horizontalLayout_3)
		SerialPlotter.setCentralWidget(self.centralwidget)

		self.retranslateUi(SerialPlotter)
		QMetaObject.connectSlotsByName(SerialPlotter)
								
		availableports=availableSerialPort()
		self.ComcomboBox.clear()	
		self.ComcomboBox.insertItems(0,availableports)	
		self.serial=ser()
		
		QObject.connect(self.serial, SIGNAL(("changeit()")), self.mplwidget.changeit)
		QObject.connect(self.serial, SIGNAL(("drawit()")), self.mplwidget.drawit)
		QObject.connect(self.ConnectButton, SIGNAL(("clicked()")), self.StatusSwitch)
		QObject.connect(self.SendButton, SIGNAL(("clicked()")), self.SendMsg)
		QObject.connect(self.InputlineEdit, SIGNAL(("returnPressed()")), self.SendMsg)		
		

	def retranslateUi(self, SerialPlotter):
	
		availableports=availableSerialPort()
		self.ComcomboBox.clear()	
		self.ComcomboBox.insertItems(0,availableports)	
	
		
		SerialPlotter.setWindowTitle("SerialPlotter")
		self.SendButton.setText( "Send")
		self.BaudcomboBox.setItemText(0,  "9600")
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.addItem((""))
		self.BaudcomboBox.setItemText(1,  "19200")
		self.BaudcomboBox.setItemText(2,  "38400")
		self.BaudcomboBox.setItemText(3,  "57600")
		self.BaudcomboBox.setItemText(4,  "74880")
		self.BaudcomboBox.setItemText(5,  "115200")
		self.BaudcomboBox.setItemText(6,  "230400")
		self.BaudcomboBox.setItemText(7,  "250000")

		self.EndcomboBox.addItem((""))
		self.EndcomboBox.addItem((""))
		self.EndcomboBox.addItem((""))
		self.EndcomboBox.setItemText(0,  "NONE") 
		self.EndcomboBox.setItemText(1,  "NL")
		self.EndcomboBox.setItemText(2,  "CR")
		self.EndcomboBox.setItemText(3,  "NL & CR")
		
		self.ConnectButton.setText( "Connect")

	def SendMsg(self):
		self.serial.makemsg(self.InputlineEdit.text())
		
	
	def StatusSwitch (self):
		if (( self.pressed==False )):
			try:
				self.serial.changecom() 
				self.serial.sendmsg("")
				self.ConnectButton.setText( "Kill")
				self.ConnectButton.setStyleSheet("background : red")
				self.pressed=True
			except:
				pass
		elif (self.pressed==True ):
			self.serial.killit()
			self.ConnectButton.setText( "Connect")
			self.ConnectButton.setStyleSheet("background : green")
			self.pressed=False
			
		

if __name__ == "__main__":
	import sys
	import atexit
	app = QApplication(sys.argv)
	app.setStyle(QStyleFactory.create("Cleanlooks"))
	SerialPlotter = QMainWindow()
	ui = Ui_SerialPlotter()
	ui.setupUi(SerialPlotter)
	SerialPlotter.show()
	try:
		atexit.register(serial.Serial(str(ui.comboports.currentText())).close())
	except:
		pass
	sys.exit(app.exec_())

