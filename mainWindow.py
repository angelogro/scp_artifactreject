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
    """
    Main Window for displaying stimuli, displaying symbols which make the user 'perform'
    artificial artifacts.
    
    Attributes
    ----------
    psender : ParallelSender
        sends triggers to the parallel port of the device
    XML_Read : XML_Read
        contains paths and existing artifact names necessary for the program
    pathArtifactSettings : str
        path to currently loaded artifact settings, containing the order of artifacts
    pathTrialSettings : str
        path to currently loaded trail settings, containing timing information for stimuli
    resourcesFolder : str
        path to resources folder
    settingArtifactOrder : SettingArtifactOrder
        SettingArtifactOrder object (Qt MainWindow), for setting up artifact order
    settingTrial : SettingTrial
        SettingTrial object (Qt MainWindow), for setting up in-trial timing
    stimulusFilename : str
        path to .csv file containing timing information of a whole experiment
    experimenttype : str
        either 'ERP' or 'Artifact'
    artifact_types : list(str)
        in ERP experiment it is the order of target stimuli, in Artifact experiment
        it is the ordered list of all presented stimuli
    stimuliList : list(float,float,str)
        contains start time, end time and artifact types of all the experiments stimuli
    artifact_list : list(float,float,str)
        same as stimuliList but not containing PAUSE stimuli
    artifact_iter : iter
        iter object of artifact_list
    artifact_types_iter : iter
        iter object of artifact_types
    image_dic : dict(str,QPixmap)
        key - artifact name; value - QPixmap from resourcesFolder
    display_item_iter : iter
        iter object of stimuliList
    timingThreads : list(Thread)
        contains all timing threads of upcoming stimuli which still can be cancelled
    timeTable : TimeTable
        contains ordered stimulus information: start time, end time, arifact type       
    lblCircle : QLabelCircle
        QLabel displaying a filling up circle, representing elapsed time        
    circleAnimationThread : Thread
        Thread to star the circle animation
    currentTarget : str
        Artifact type in ERP experiment representing the current target stimulus
    

    Methods
    -------
    __init__() :
        Initializing function of main window.
    loadXMLFile() :
        Loading config.xml file.
    initUI() :
        Initialize layout and GUI
    showWidgets() :
        Used for displaying all relevant labels.
    hideWidgets() :
        Used for hiding all relevant labels.
    getSettingsPaths() :
        Gets paths of the setting xml files which are currently used for
        generating a stimulus csv file.
    openSettingArtifactOrder() :
        Opens a specific Artifact Setting file.
    openStimulusFile() :
        Opens a specific Stimulus file which was stored in .csv format.         
    openSettingTrial() :
        Opens a specific Trial Setting file. 
    startPresentationClicked() :
        Logic of what happens if Start (F5) is pressed.
    startPresentationFromFile() :
        Logic of what happens if Start From File (F6) is pressed.
    startPresentation() :
        Creating lists of stimuli which are to be presented.
    runNextItem() :
        Runs the next presented stimulus in the simuli list. 
    displayInfoERP(text,count) :
        Creating lists of stimuli which are to be presented in ERP experiment.
    displayInfoArtifact(text,count) :
        Creating lists of stimuli which are to be presented in Artifact experiment.
    loadTimetable() :
        Loads information from timeTable object and starts presentation. 
    makeTimeTable(settingOrderPath,settingTrialPath):
        Creates an experiment time plan according to setting files. 
    stopPresentation() :
        Stops presentation and cancel all timed threads. 
    closeEvent(event):
        Destroys setting windows if open and stops the presentation. 
    """
    def __init__(self):
        """ Initializing function of main window. """

        super().__init__()
        self.loadXMLFile()
        self.resourcesFolder = os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','Resource_Folder']))
        self.initUI()
        self.pSender = ParallelSender()

    def loadXMLFile(self):
        """ Loading config.xml file. """
        
        if os.path.isfile('config.xml'):
            self.XML_Read = XML_Read()
        else:
            #QMessageBox.warning(self, "IOError", "Please make sure the file \'config.xml\' is inside the executable's folder.")
            self.close()
            sys.exit()

    def initUI(self):
        """ Initialize layout and GUI
        
        Connects button click events to different functions.
        """
        uic.loadUi(os.path.join(self.XML_Read.getValue(['Paths','Designer_File_Folder']),'mainWindow_circle.ui'),self)
        self.actionArtifact_Order.triggered.connect(self.openSettingArtefactOrder)
        self.actionStimulus_Order.triggered.connect(self.openSettingTrial)
        self.actionStart.triggered.connect(self.startPresentationClicked)
        self.actionStart_from_file.triggered.connect(self.startPresentationFromFile)
        self.actionStop.triggered.connect(self.stopPresentation)
        self.actionLoad_Stimulus_File.triggered.connect(self.openStimulusFile)
        self.actionSave_Stimulus_File.triggered.connect(self.openSettingArtefactOrder)
        self.actionQuit_Program.triggered.connect(self.close)
        self.pathArtefactSettings = None
        self.pathTrialSettings = None
        self.getSettingsPaths()
        
        self.lblCircle = QLabelCircle()
        self.vlDisplay.addWidget(self.lblCircle)
        self.lblCircle.addImageLabel()
        
        self.hideWidgets()
        self.show()

    def showWidgets(self):
        """ Used for displaying all relevant labels. """
        self.lblCircle.show()

    def hideWidgets(self):
        """ Used for hiding all relevant labels. """
        self.lblCircle.hide()

    def getSettingsPaths(self):
        """ Gets paths of the setting xml files which are currently used for
        generating a stimulus csv file.
        """
        pathArt = self.XML_Read.getValue(['Paths','ArtifactOrder'])
        if pathArt:
            self.pathArtefactSettings = pathArt
        pathTrial = self.XML_Read.getValue(['Paths','TrialSettings'])
        if pathTrial:
            self.pathTrialSettings = pathTrial

    def openSettingArtefactOrder(self):
        """ Opens a specific Artefact Setting file. 
        
        The path stored in pathArtefactSettings will be loaded.
        """
        self.settingArtefactOrder = SettingArtefactOrder(self.XML_Read,self.pathArtefactSettings)

    def openStimulusFile(self):
        """ Opens a specific Stimulus file which was stored in .csv format. """
        self.stimulusFilename,filetype = QFileDialog.getOpenFileName(None,
                                                                     "Stimulus file", 
                                                                     os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','StimulusFilesDefault'])),
                                                                     "CSV Files (*.csv)")

    def openSettingTrial(self):
        """ Opens a specific Trial Setting file. 
        
        The path stored in pathTrialSettings will be loaded.
        """
        self.settingTrial = SettingTrial(self.XML_Read,self.pathTrialSettings)

    def startPresentationClicked(self):
        """ Logic of what happens if Start (F5) is pressed.

        Checks if a settingArtefactOrder and settingTrial have their
        currentXMLfilepath set and try to load the corresponding settings.
        If currentXMLfilepath is not set the current settings are saved to
        temporary xml files.
        Using these settings a stimulus file is created and the experiment is 
        started.
        """
        if hasattr(self,'settingArtefactOrder'):
            if hasattr(self.settingArtefactOrder,'currentXMLfilepath'):
                self.pathArtefactSettings = self.settingArtefactOrder.currentXMLfilepath
                if not self.settingArtefactOrder.currentXMLfilepath == 'temp_ordersettings.xml':
                    self.XML_Read.saveValue(['Paths','ArtifactOrder'],self.pathArtefactSettings)

        if hasattr(self,'settingTrial'):
            if hasattr(self.settingTrial,'currentXMLfilepath'):
                self.pathTrialSettings = self.settingTrial.currentXMLfilepath
                if not self.settingTrial.currentXMLfilepath == 'temp_trialsettings.xml':
                    self.XML_Read.saveValue(['Paths','TrialSettings'],self.pathTrialSettings)
                    
        if self.pathArtefactSettings is not None and self.pathTrialSettings is not None:
            if os.path.isfile(self.pathArtefactSettings) and os.path.isfile(self.pathTrialSettings):
                self.makeTimeTable(self.pathArtefactSettings,self.pathTrialSettings)
            else:
                text = 'Artifact Order XML file path {} is not a file. \n'.format(self.pathArtefactSettings) if not os.path.isfile(self.pathArtefactSettings) else ''
                text2 = 'Trial Settings XML file path {} is not a file.'.format(self.pathTrialSettings) if not os.path.isfile(self.pathTrialSettings) else ''
                QMessageBox.warning(None,'Could not start the stimulus presentation.',text+text2)
        else:
            text = 'Artifact Order XML file path is empty. \n' if self.pathArtefactSettings is None else ''
            text2 = 'Trial Settings XML file path is empty.' if self.pathTrialSettings is None else ''
            QMessageBox.warning(None,'Could not start the stimulus presentation.',text+text2)
            
    def startPresentationFromFile(self):
        """ Logic of what happens if Start From File (F6) is pressed.

        Checks if a the instance has a valid stimulus file loaded already.
        If so the stimulus file (.csv) is read and the experiment is started
        according to it.
        """
        if hasattr(self,'stimulusFilename'):
            if self.stimulusFilename is None:
                QMessageBox.warning(None,'Could not start the stimulus presentation.','No file has been loaded.')
                return
        else:
            QMessageBox.warning(None,'Could not start the stimulus presentation.','No file has been loaded.')
            return
        
        self.showWidgets()
        
        with open(self.stimulusFilename, mode='r',newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            # Identify the type of experiment from csv file
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
            
    def startPresentation(self):
        """ Creating lists of stimuli which are to be presented.

        Iterables for all artifacts as well as the artifac types are created.
        These are step-wise iterated through in the course of the experiment.
        The first step of the experiment is initiated.
        """
        self.timingThreads = []
        self.artifact_list = list(filter(lambda x: x != PAUSEBETWEENTRIALSTEXT and x != PAUSETEXT,[row['type'] for row in self.stimuliList]))
        self.artifact_iter =iter(self.artifact_list)
        self.artifact_types_iter = iter(self.artifact_types)
        
        # Loads the artifact symbols into RAM
        self.image_dic = {artifact_type:QPixmap(os.path.join(self.resourcesFolder,self.XML_Read.getValue(['ArtefactCategories',artifact_type,'SymbolFilename']))) for artifact_type in self.artifact_list}
        
        self.display_item_iter = iter(self.stimuliList)
        if self.experimenttype == 'ERP':
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','StartOddball'])))
            time.sleep(0.1)
        elif self.experimenttype == 'Artifact':
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','StartArtifact'])))
            time.sleep(0.1)
        
        
        self.runNextItem()

    def runNextItem(self):
        """ Runs the next presented stimulus in the simuli list. """
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
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','End'])))
            self.hideWidgets()

    

    def displayInfoERP(self,text,count):
        """ Creating lists of stimuli which are to be presented in ERP experiment.
        
        The image corresponding to the 'text' is set visible on the
        screen for 'count' seconds. The function also sends out triggers via
        the parallel port.

        Keyword arguments:
        text -- the text of the item to be displayed
        count -- the amount of seconds (float) the item is displayed
        """
        
        if text==PAUSETEXT:
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','Pause'])))
            self.lblCircle.setImage(self.image_dic[self.artifact_iter.__next__()])
        elif text==PAUSEBETWEENTRIALSTEXT:
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','Pause'])))
            self.currentTarget=self.artifact_types_iter.__next__()
            self.lblCircle.setImage(self.image_dic[self.currentTarget])
        else:
            if text == self.currentTarget:
                self.pSender.send_parallel(int(self.XML_Read.getValue(['ArtefactCategories',text,'ID'])))
            else:
                #add up 100 to the trigger to point out it is a non-target
                self.pSender.send_parallel(100+int(self.XML_Read.getValue(['ArtefactCategories',text,'ID'])))
            
        self.circleAnimationThread = Thread(target=self.lblCircle.startAnimationThread,args=(count,text,self.experimenttype))
        self.circleAnimationThread.start()
        
    def displayInfoArtifact(self,text,count):
        """ Creating lists of stimuli which are to be presented in Artifact experiment.
        
        The image corresponding to the 'text' is set visible on the
        screen for 'count' seconds. The function also sends out triggers via
        the parallel port.

        Keyword arguments:
        text -- the text of the item to be displayed
        count -- the amount of seconds (float) the item is displayed
        """
        
        if text==PAUSETEXT:
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','Pause'])))
            self.lblCircle.setImage(self.image_dic[self.artifact_iter.__next__()])
        elif text==PAUSEBETWEENTRIALSTEXT:
            self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','Pause'])))
        else:
            self.pSender.send_parallel(int(self.XML_Read.getValue(['ArtefactCategories',text,'ID'])))
        
        self.circleAnimationThread = Thread(target=self.lblCircle.startAnimationThread,args=(count,text,self.experimenttype))
        self.circleAnimationThread.start()

    def loadTimetable(self):
        """ Loads information from timeTable object and starts presentation. """
        self.showWidgets()
        self.experimenttype,self.stimuliList,self.artifact_types  = self.timeTable.loadSettingInformation()
        self.startPresentation()
        
    def makeTimeTable(self,settingOrderPath,settingTrialPath):
        """ Creates an experiment time plan according to setting files. 
        
        Keyword arguments:
        settingOrderPath -- path to settings file containing artifact order
        settingTrialPath -- path to settings file containing stimulus timings
        """
        self.timeTable = TimeTable(settingOrderPath,settingTrialPath,self.XML_Read)
        self.loadTimetable()

    def stopPresentation(self):
        """ Stops presentation and cancel all timed threads. """
        self.pSender.send_parallel(int(self.XML_Read.getValue(['TriggerID','End'])))
        if hasattr(self,'timingThreads'):
            for t in self.timingThreads:
                t.cancel()
        self.hideWidgets()

    def closeEvent(self,event):
        """ Destroys setting windows if open and stops the presentation. """
        if hasattr(self,'settingArtefactOrder'):
            self.settingArtefactOrder.close()
        if hasattr(self,'settingTrial'):
            self.settingTrial.close()
        self.stopPresentation()
        self.close()


class QLabelCircle(QWidget):
    """
    QWidget consisting of a centered image surrounded by a circle
    
    Attributes
    ----------
    arcWidth : int
        width of the arc/circle in pixels
    arcColor : QColor
        color of the arc/circle
    addText : boolean
        whether text is displayed additionally to the displayed symbol
    hidden : boolean
        whether this widget is hidden
    lblImage : QLabelOpaque
        label with variable opacity where image is displayed
    angle : float
        angle of the displayed arc/circle
        
    Methods
    -------
    __init__(width=10) :
        Initializing function of main window.
    addImageLabel() :
        Adding QLableOpaque to the widget.
    paintEvent(e) :
        Overwritten paintEvent method. 
    setAngle(angle) :
        Sets the current angle of the arc/circle. 
    startAnimationThread(count,text,experimentType='standard') :
        Starts the filling up circle animation.
    runCircleAnimation(count) :
        Runs the circle animation. 
    hideEvent(e) :
        Overwritten hide event method.        
    showEvent(e) :
        Overwritten show event method.
    setImage(image) :
        Sets an image to the image widget.
    """
    def __init__(self,width=10,*args, **kwargs):
        """ Initializing the widget
        
        Keyword arguments:
        width -- width of the arc/circle
        """
        super().__init__( *args, **kwargs)
        self.setAngle(0)
        self.arcWidth = width
        self.arcColor = 'gray'
        self.addText = None
        self.hidden = False
        
    
    def addImageLabel(self):
        """ Adding QLableOpaque to the widget. """
        self.lblImage = QLabelOpaque()
        self.lblImage.setScaledContents(True)
        self.lblImage.setParent(self)
        self.lblImage.setGeometry( QRect(75, 75, self.parentWidget().width()-160, self.parentWidget().height()-160))
        
    def paintEvent(self,e):
        """ Overwritten paintEvent method. 
        
        Sets current arc color and width and adds text if necessary.
        
        Keyword arguments:
        e -- sender which triggered the event
        """
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
        """ Sets the current angle of the arc/circle. 
        
        Keyword arguments:
        angle -- angle of the arc/circle
        """
        self.angle = angle
        self.update()
        
    def startAnimationThread(self,count,text,experimentType='standard'):
        """ Starts the filling up circle animation. 
        
        Adapts the color and angle of the circle and the opacity of the image
        depending on the experiment type and wether it is an artifact or pause
        stimulus.
        
        Keyword arguments:
        count -- time in seconds which needs to elapse before circle is filled
        text -- text displayed in the widget
        experimentType -- either ERP or Artifact
        """
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
        """ Runs the circle animation. 
        
        Keyword arguments:
        count -- time in seconds which needs to elapse before circle is filled
        """
        startTime = time.time()
        n_ticks_per_second = 20
        wait_time = 1/(n_ticks_per_second)
        for i in range(int(count*n_ticks_per_second)):
            if self.hidden == True:
                self.setAngle(0)
                return
            
            self.setAngle(360*i/(n_ticks_per_second*count))
            
            if time.time()-startTime < i/n_ticks_per_second:
                time.sleep(wait_time)
        pass
    
    def hideEvent(self,e):
        """ Overwritten hide event method. """
        self.hidden = True
        
    def showEvent(self,e):
        """ Overwritten show event method. """
        self.hidden = False
    
    def setImage(self,image):
        """ Sets an image to the image widget. 
        
        Keyword arguments:
        image -- QPixmap object to be displayed on the label.        
        """
        self.lblImage.setPixmap(image,)
        self.lblImage.update()
        self.update()

class QLabelOpaque(QLabel):
    """
    QLabel for displaying an image with variable opacity
    
    Attributes
    ----------
    opacity : float (0 ... 1)
        opacity of the image.    
        
    Methods
    -------
    __init__() :
        Initializing the widget. 
    setOpacity(opacity) :
        Sets the opacity of the image.
    paintEvent(e) :
        Overwritten paintEvent method.
    """
    def __init__(self,*args, **kwargs):
        """ Initializing the widget. """
        super().__init__( *args, **kwargs)
        self.opacity=1
        
    def paintEvent(self,e):
        """ Overwritten paintEvent method. 
        
        Sets and scales and sets opacity of the image.
        
        Keyword arguments:
        e -- sender which triggered the event
        """
        painter = QtGui.QPainter(self)
        painter.setOpacity(self.opacity)
        if self.pixmap() is not None:
            pixmap = self.pixmap().scaled(self.width(),self.height(),Qt.KeepAspectRatio)
            painter.drawPixmap((self.width()-pixmap.width())/2, (self.height()-pixmap.height())/2, pixmap)
    
    def setOpacity(self,opacity):
        """ Sets the opacity of the image. """
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