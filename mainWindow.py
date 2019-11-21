# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 11:29:49 2019
@author: agross
"""
import random
from PyQt5 import QtGui,uic
from PyQt5.QtWidgets import  QGridLayout,QLabel, QAction, QTextEdit, QFontDialog, QColorDialog, QFileDialog, QTableWidget,QLCDNumber
from PyQt5.QtWidgets import QApplication,QLineEdit,QDialog,QScrollArea,QWidget,QStackedWidget, QMainWindow, QPlainTextEdit
import os
from PyQt5.QtGui import QIcon,QPixmap,QStaticText
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt5.Qt import QFileInfo,QProxyStyle,QStyle,QMessageBox
from PyQt5.QtCore import Qt,QRect,QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPdfWriter,QFontMetrics,QBrush
from xml_read import XML_Read
from PyQt5 import QtCore
from settingsWindows import SettingArtefactOrder,SettingTrial
import sys
import csv
from math import ceil
import sched, time
from threading import Timer,Thread
import _thread
from itertools import cycle
from parallelSend import ParallelSender
from helpers import TimeTable

PAUSETEXT = 'pause'
PAUSEBETWEENTRIALSTEXT = 'pause_between_trials'

class MainWindow(QMainWindow):
    def __init__(self):
        """
        Initializing function of main window.


        Parameters
        ----------
        None

        Returns
        -------
        None

        """

        super().__init__()
        self.loadXMLFile()
        self.resourcesFolder = os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','Resource_Folder']))
        self.initUI()
        self.pSender = ParallelSender()

    def loadXMLFile(self):
        if os.path.isfile('config.xml'):
            self.XML_Read = XML_Read()
        else:
            #QMessageBox.warning(self, "IOError", "Please make sure the file \'config.xml\' is inside the executable's folder.")
            self.close()
            sys.exit()

    def initUI(self):
        """
        Initialize layout and GUI


        Parameters
        ----------
        None

        Returns
        -------
        None

        """

        uic.loadUi(os.path.join(self.XML_Read.getValue(['Paths','Designer_File_Folder']),'mainWindow_circle.ui'),self)
        self.actionArtefact_Order.triggered.connect(self.openSettingArtefactOrder)
        self.actionStimulus_Order.triggered.connect(self.openSettingTrial)
        self.actionStart.triggered.connect(self.startPresentationClicked)
        self.actionStop.triggered.connect(self.stopPresentation)
        self.actionLoad_Stimulus_File.triggered.connect(self.openStimulusFile)
        self.actionSave_Stimulus_File.triggered.connect(self.openSettingArtefactOrder)
        self.actionQuit_Program.triggered.connect(self.close)
        self.pathArt = None
        self.pathTrial = None
        self.getSettingsPaths()
        
        self.lblCircle = QLabelCircle()
        self.vlDisplay.addWidget(self.lblCircle)
        self.lblCircle.addImageLabel()
        
        self.hideWidgets()
        self.show()
        
        

    def showWidgets(self):
        """
        Used for displaying all relevant labels.


        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        self.lblCircle.show()

    def hideWidgets(self):
        """
        Used for hiding all relevant labels.


        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        self.lblCircle.hide()

    def getSettingsPaths(self):
        """
        Gets pathes of the setting xml files which are currently used for
        generating a stimulus csv file.

        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        pathArt = self.XML_Read.getValue(['Paths','ArtifactOrder'])
        if pathArt:
            self.pathArt = pathArt
        pathTrial = self.XML_Read.getValue(['Paths','TrialSettings'])
        if pathTrial:
            self.pathTrial = pathTrial

    def openSettingArtefactOrder(self):
        self.settingArtefactOrder = SettingArtefactOrder(self.XML_Read,self.pathArt)

    def openStimulusFile(self):
        self.stimulusFilename,filetype = QFileDialog.getOpenFileName(None,"Stimulus file", os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','StimulusFilesDefault'])),
                                                        "CSV Files (*.csv)")

    def openSettingTrial(self):
        self.settingTrial = SettingTrial(self.XML_Read,self.pathTrial)

    def startPresentationClicked(self):
        """
        Logic of what happens if start is pressed.

        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        # Checks if a stimulusfile exists already and hence starts a stimulus
        # presentation based on that file.
        if hasattr(self,'stimulusFilename'):
            if self.stimulusFilename is not None:
                self.startPresentationFromFile()
                return
            
        if hasattr(self,'settingArtefactOrder'):
            if hasattr(self.settingArtefactOrder,'currentXMLfilepath'):
                self.pathArt = self.settingArtefactOrder.currentXMLfilepath
                if not self.settingArtefactOrder.currentXMLfilepath == 'temp_ordersettings.xml':
                    self.XML_Read.saveValue(['Paths','ArtifactOrder'],self.pathArt)

        if hasattr(self,'settingTrial'):
            if hasattr(self.settingTrial,'currentXMLfilepath'):
                self.pathTrial = self.settingTrial.currentXMLfilepath
                if not self.settingTrial.currentXMLfilepath == 'temp_trialsettings.xml':
                    self.XML_Read.saveValue(['Paths','TrialSettings'],self.pathTrial)
                    
        if self.pathArt is not None and self.pathTrial is not None:
            if os.path.isfile(self.pathArt) and os.path.isfile(self.pathTrial):
                self.makeTimeTable(self.pathArt,self.pathTrial)
            else:
                text = 'Artifact Order XML file path {} is not a file. \n'.format(self.pathArt) if not os.path.isfile(self.pathArt) else ''
                text2 = 'Trial Settings XML file path {} is not a file.'.format(self.pathTrial) if not os.path.isfile(self.pathTrial) else ''
                q = QMessageBox.warning(None,'Could not start the stimulus presentation.',text+text2)
        else:
            text = 'Artifact Order XML file path is empty. \n' if self.pathArt is None else ''
            text2 = 'Trial Settings XML file path is empty.' if self.pathTrial is None else ''
            q = QMessageBox.warning(None,'Could not start the stimulus presentation.',text+text2)
        #self.setStyleSheet("background-color: rgb(0, 0, 0);")


    def loadTimetable(self):
        self.showWidgets()
        self.experimenttype,self.stimuliList,self.artifact_types  = self.timeTable.loadSettingInformation()
        self.startPresentation()
        
    def startPresentation(self):
        self.timingThreads = []
        
        # Takes all entries of the list which describe an artifact
        self.artifact_list = list(filter(lambda x: x != PAUSEBETWEENTRIALSTEXT and x != PAUSETEXT,[row['type'] for row in self.stimuliList]))
        self.artifact_iter =iter(self.artifact_list)
        self.artifact_types_iter = iter(self.artifact_types)
        
        self.image_dic = {artifact_type:QPixmap(os.path.join(self.resourcesFolder,self.XML_Read.getValue(['ArtefactCategories',artifact_type,'SymbolFilename']))) for artifact_type in self.artifact_list}
        
        self.display_item_iter = iter(self.stimuliList)
        self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','Start']))
        self.runNextItem()

    def runNextItem(self):
        try:
            current_item = self.display_item_iter.__next__()
            
            if self.experimenttype == 'ERP':
                _thread.start_new_thread(self.displayInfoERP,(current_item['type'],float(current_item['end_time'])-float(current_item['start_time'])))
            elif self.experimenttype == 'Artifact':
                _thread.start_new_thread(self.displayInfoArtifact,(current_item['type'],float(current_item['end_time'])-float(current_item['start_time'])))
            
            t =Timer(float(current_item['end_time'])-float(current_item['start_time']),self.runNextItem)
            t.start()
            self.timingThreads.append(t)
        except StopIteration:
            self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','End']))
            self.hideWidgets()

    def startPresentationFromFile(self):
        self.showWidgets()
        
        # Extract all artifacts which are not pauses from csv file
        with open(self.stimulusFilename, mode='r',newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            firstrow = next(csv_reader)
            if len(firstrow) > 3:
                self.experimenttype = 'ERP'
                self.artifact_types = firstrow[3:]
            else:
                self.experimenttype = 'Artifact'
            
            self.stimuliList =[]
            while True:
                try:
                    row = csv_reader.__next__()
                    self.stimuliList.append({firstrow[0]:row[0],firstrow[1]:row[1],firstrow[2]:row[2]})
                except StopIteration:
                    break
            if self.experimenttype == 'Artifact':
                self.artifact_types = [row['type'] for row in self.stimuliList]
            self.startPresentation()

    def displayInfoERP(self,text,count):
        # distinguish between circular and numerical representation
        
        if text==PAUSETEXT:
            self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','Pause']))
            self.lblCircle.setImage(self.image_dic[self.artifact_iter.__next__()])
        elif text==PAUSEBETWEENTRIALSTEXT:
            self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','Pause']))
            self.currentTarget=self.artifact_types_iter.__next__()
            self.lblCircle.setImage(self.image_dic[self.currentTarget])
        else:
            if text == self.currentTarget:
                self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','Target']))
            else:
                self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','NonTarget']))
            
        self.circleAnimationThread = Thread(target=self.lblCircle.startAnimationThread,args=(count,text,self.experimenttype))
        self.circleAnimationThread.start()
        
    def displayInfoArtifact(self,text,count):
        # distinguish between circular and numerical representation
        
        if text==PAUSETEXT:
            self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','Pause']))
            self.lblCircle.setImage(self.image_dic[self.artifact_iter.__next__()])
        elif text==PAUSEBETWEENTRIALSTEXT:
            self.pSender.send_parallel(None,None,self.XML_Read.getValue(['TriggerID','Pause']))
        else:
            self.pSender.send_parallel(None,None,self.XML_Read.getValue(['ArtefactCategories',text,'ID']))
        
        self.circleAnimationThread = Thread(target=self.lblCircle.startAnimationThread,args=(count,text,self.experimenttype))
        self.circleAnimationThread.start()
        

    def makeTimeTable(self,settingOrderPath,settingTrialPath):
        self.timeTable = TimeTable(settingOrderPath,settingTrialPath,self.XML_Read)
        self.loadTimetable()

    def stopPresentation(self):
        if hasattr(self,'timingThreads'):
            for t in self.timingThreads:
                t.cancel()
        self.hideWidgets()

    def closeEvent(self,event):
        if hasattr(self,'settingArtefactOrder'):
            self.settingArtefactOrder.close()
        if hasattr(self,'settingTrial'):
            self.settingTrial.close()
        self.stopPresentation()
        self.close()


class QLabelCircle(QWidget):
    def __init__(self,width=10,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.setAngle(0)
        self.arcWidth = width
        self.arcColor = 'gray'
        self.addText = None
        
    
    def addImageLabel(self):
        self.lblImage = QLabelOpaque()
        self.lblImage.setScaledContents(True)
        self.lblImage.setParent(self)
        self.lblImage.setGeometry( QRect(75, 75, self.parentWidget().width()-160, self.parentWidget().height()-160))
        
    def paintEvent(self,e):
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(self.arcColor))
        pen.setWidth(self.arcWidth)
        painter.setPen(pen)
        painter.drawArc(self.arcWidth,self.arcWidth,self.width()-2*self.arcWidth,self.width()-2*self.arcWidth,0,16*self.angle)
        if self.addText:
            text = QStaticText('Target Symbol:')
            pen.setColor(QtGui.QColor('black'))
            painter.setPen(pen)
            painter.setFont(QFont("times",22))
            painter.drawStaticText(QPoint(90,40),text)
        
    def setAngle(self, angle):
        self.angle = angle
        self.update()
        
    def startAnimationThread(self,count,text,experimentType='standard'):
        self.addText=False
        if experimentType == 'ERP':
            self.lblImage.setOpacity(0)
            if text == PAUSETEXT:
                self.setAngle(0)
            elif text == PAUSEBETWEENTRIALSTEXT:
                self.arcColor = 'red'
                self.lblImage.setOpacity(1)
                self.addText=True
                self.runCircleAnimation(count)
                
            else:
                self.setAngle(0)
                self.lblImage.setOpacity(1)
                self.update()
        else:
            if text == PAUSETEXT :
                self.lblImage.setOpacity(0.3)
                self.arcColor = 'gray'
            elif text == PAUSEBETWEENTRIALSTEXT:
                self.lblImage.setOpacity(0)
                self.arcColor = 'gray'
            else:
                self.lblImage.setOpacity(1)
                self.arcColor = 'green'
            self.runCircleAnimation(count)

    def runCircleAnimation(self,count):
        startTime = time.time()
        n_ticks_per_second = 20
        wait_time = 1/(n_ticks_per_second)
        for i in range(int(count*n_ticks_per_second)):
            self.setAngle(360*i/(n_ticks_per_second*count))
            
            if time.time()-startTime < i/n_ticks_per_second:
                time.sleep(wait_time)
        pass
    
    def setImage(self,image):
        self.lblImage.setPixmap(image,)
        self.lblImage.update()
        self.update()

class QLabelOpaque(QLabel):
    def __init__(self,*args, **kwargs):
        super().__init__( *args, **kwargs)
        self.opacity=1
        
    def paintEvent(self,e):
        painter = QtGui.QPainter(self)
        painter.setOpacity(self.opacity)
        if self.pixmap() is not None:
            pixmap = self.pixmap().scaled(self.width(),self.height(),Qt.KeepAspectRatio)
            painter.drawPixmap((self.width()-pixmap.width())/2, (self.height()-pixmap.height())/2, pixmap)
    
    def setOpacity(self,opacity):
        self.opacity = opacity

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.aboutToQuit.connect(app.deleteLater)
    if len(sys.argv) > 1:
        ex = MainWindow(sys.argv[1])
    else:
        ex = MainWindow()
    sys.exit(app.exec_())
    app.quit