#!/usr/bin/env python
#

# MIT License
# 
# Copyright (c) 2021 ecki
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import asyncio
import sys
from kasa import Discover, SmartPlug
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer

class qasaplugqt:
    def __init__(self):
        self.plugwidgets = {}
        self.plugbuttons = {}
        self.plugs = {}
        self.updateview = []

        self.discover()
        self.updatetimer = QTimer()

        self.app = QApplication(sys.argv)
        self.windowsetup()
        self.windowshow()
            
    def sortdevices(self,devices):
        newdevices = {}
        sortediplist = sorted(devices)
        for addr in sortediplist:
            dev = devices.get(addr,"error")
            if dev != "error":
                newdevices.update({addr:dev})
        return newdevices
    
    def discover(self):
        devices = asyncio.run(Discover.discover())
        for addr,dev in devices.items():
            asyncio.run(dev.update())
            devices.update({addr:dev})
        devices = self.sortdevices(devices)
        for addr, dev in devices.items():
            if dev.is_plug:
                asyncio.run(dev.update())
                notexisting = False
                if not self.plugs.get(addr,False):
                    notexisting = True
                plug = self.plugs.get(addr,SmartPlug(addr))
                is_on = False
                powerupdate = False
                if not notexisting:
                    is_on = plug.is_on
                    if plug.model.startswith("HS110"):
                        powerupdate = True
                asyncio.run(plug.update())
                if notexisting or powerupdate or is_on != plug.is_on:
                    self.updateview.append(addr)
                self.plugs.update({addr:plug})
    
    def windowsetup(self):
        self.mainwindow = QWidget()
        self.mainwindow.setWindowTitle("QasaPlug")
        self.mainlayout = QVBoxLayout()
        self.mainwindow.setLayout(self.mainlayout)
        self.windowredraw()
    
    def windowredraw(self):
        for addr, dev in self.plugs.items():
            if addr in self.updateview:
                #print("update "+str(addr)+"  "+str(dev.alias))
                plugname = QLabel(str(dev.alias))
                powerlabel = ""
                if dev.model.startswith("HS110"):
                    powerlabel = str(dev.emeter_realtime.get("power",""))
                plugpower = QLabel(powerlabel)
                if dev.is_on:
                    plugtext = "switch off"
                else:
                    plugtext = "switch on"
                plugbutton = self.plugbuttons.get(addr,QPushButton(plugtext))
                plugbutton.setCheckable(True)
                plugbutton.setChecked(dev.is_on)
                if not addr in self.plugbuttons:
                    plugbutton.clicked.connect(lambda:self.buttonpushed())
                self.plugbuttons.update({addr:plugbutton})
                
                plugwidget = self.plugwidgets.get(addr,QWidget())
                if addr in self.plugwidgets:
                    widgetexists = True
                    self.cleanwidget(plugwidget)
                    pluglayout = plugwidget.layout()
                else:
                    widgetexists = False
                    pluglayout = QHBoxLayout()
                    plugwidget.setLayout(pluglayout)
                
                pluglayout.addWidget(plugname)
                pluglayout.addWidget(plugpower)
                pluglayout.addWidget(plugbutton)

                if not widgetexists:
                    self.plugwidgets.update({addr:plugwidget})
                    self.mainlayout.addWidget(plugwidget)
                self.updateview.remove(addr)
        
    def windowshow(self):
        self.mainwindow.show()

        self.updatetimer.setInterval(60000)
        self.updatetimer.timeout.connect(self.discover)
        self.updatetimer.start()

        sys.exit(self.app.exec_())
    
    def buttonpushed(self):
        for addr,plugbutton in self.plugbuttons.items():
            plug = self.plugs.get(addr,"error")
            is_on = "error"
            if plug != "error":
                is_on = plug.is_on
            if plugbutton.isChecked() != is_on: 
                #print("switch: " + str(plug.alias))
                if is_on:
                    asyncio.run(plug.turn_off())
                    plugbutton.setText("switch on")
                else:
                    asyncio.run(plug.turn_on())
                    plugbutton.setText("switch off")
                asyncio.run(plug.update())
                self.plugs.update({addr:plug})
                self.updateview.append(addr)
                self.windowredraw()
    
    def cleanwidget(self,widget):
        layout = widget.layout()
        self.deleteItemsOfLayout(layout) 

    def deleteItemsOfLayout(self,layout):
      if layout is not None:
         while layout.count():
             item = layout.takeAt(0)
             widget = item.widget()
             if widget is not None:
                 widget.setParent(None)
             else:
                 deleteItemsOfLayout(item.layout())

if __name__ == "__main__":
    MyGUI = qasaplugqt()
