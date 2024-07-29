"""
Author: Rashi Sinha
Date Created: 28 July 2024
Versio: 1.0

Description: This is an interactive Qt UI for running the tweenMachine.py plugin command
This script checks if the plugin is loaded, loads the plugin if it is not already loaded,
displays the interactive UI for the user to apply tween to selected objects

The plugin script name should not be changed from "tweenMachine.py".
The plugin script should be available in the user's local Maya/<version>/plug-ins folder.

Execution:
Open the script in script editor in Maya
    1. Run from script Editor
    2. (Recommended) Save script to custom shelf, save shelf and click on the custom shelf icon
"""

from maya import OpenMayaUI as omui 
import maya.cmds as cmds
try:
    from PySide2.QtCore import * 
    from PySide2.QtGui import * 
    from PySide2.QtWidgets import *
    from PySide2 import __version__
    from shiboken2 import wrapInstance 
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QApplication, QPushButton
except ImportError:
    from PySide.QtCore import * 
    from PySide.QtGui import * 
    from PySide import __version__
    from shiboken import wrapInstance 

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)

class TweenMainWindow(QMainWindow):
    
    def __init__(self, parent=maya_main_window()):
        super(TweenMainWindow, self).__init__(parent,Qt.WindowStaysOnTopHint)

        self.setWindowFlags(Qt.Window)

        self.sliderPressedBool = False
        self.sliderReleasedBool = True
        
        # add UI Elements
        self.setWindowTitle("Tween Machine - v1.0")
        self.setFixedSize(400,100)

        self.pWidget = QWidget(self)
        self.setCentralWidget(self.pWidget)

        self.pMainLayout = QHBoxLayout()
        self.pWidget.setLayout(self.pMainLayout)

        # tween label in main horzontal layout
        self.pLabel = QLabel("Tween:", self)
        self.pLabel.setStyleSheet("padding :10px, 5px, 0px, 0px; font-size: 14px")
        self.pMainLayout.addWidget(self.pLabel, alignment=Qt.AlignTop)


        self.pSliderLayout = QVBoxLayout()
        self.pMainLayout.addLayout(self.pSliderLayout)
        
        # slider in vertical layout inside the horizontal layout
        self.tweenSlider = QSlider(Qt.Horizontal)
        self.tweenSlider.setMinimum(0)
        self.tweenSlider.setMaximum(100)
        self.tweenSlider.setValue(50)
        self.tweenSlider.setStyleSheet("padding: 25px, 0px, 0px, 0px")
        self.pSliderLayout.addWidget(self.tweenSlider)

        self.pLabel2 = QLabel("50", self)
        self.pLabel2.setStyleSheet("border-radius: 4px; padding :1px; font-size: 12px; background-color: #272729")
        self.pSliderLayout.addWidget(self.pLabel2, alignment=Qt.AlignCenter)
        
        self.tweenSlider.valueChanged.connect(self.valueChanged)  
        self.tweenSlider.sliderPressed.connect(lambda: self.sliderPressed())
        self.tweenSlider.sliderReleased.connect(lambda: self.sliderReleased())


    def valueChanged(self):
        weightVal = self.tweenSlider.value()
        if self.sliderPressedBool and not self.sliderReleasedBool:
            self.pLabel2.setText(str(weightVal))
            cmds.tweenMachine(weight = weightVal)


    def sliderPressed(self):
        self.sliderPressedBool = True
        self.sliderReleasedBool = False


    def sliderReleased(self):
        self.sliderPressedBool = False
        self.sliderReleasedBool = True


def showTweenWindow():
    try:
        window.close()
        window.deleteLater()
    except:
        pass
    window = TweenMainWindow()
    window.show()


def main():
    
    if not cmds.pluginInfo("tweenMachine.py", query=True, loaded=True):
        if "tweenMachine" in cmds.loadPlugin("tweenMachine.py"):
            # if plugin was successfully loaded, show UI
            showTweenWindow()
        else:
            cmds.error("Unable to load tweenMachine.py Plugin")
    else:
        # if plugin is already loaded, show UI
        showTweenWindow()


if __name__=="__main__": 
    main() 

