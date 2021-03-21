#!C:\Users\wheez\AppData\Local\Programs\Python\Python39\python.exe
# -*- coding: utf-8 -*-

"""
backup_computer.py
 
Reads in a file that contains backup commands. Each backup command contains 3 items.
    fromFolder      toBaseFolder    mode

fromFolder:
    This is the toplevel folder you wish to start you recursive backup operation from.

toBaseFolder:
    This is the destination toplevel folder to copy the files to.

mode:
    There are two modes of copying files, relative and substitute

    relative:
        Takes the fromFolder and appends that to the toBaseFolder path (minus the drive letter)

    substitute:
        Takes the paths under the specified fromFolder (not including the fromFolder itself)
        and appends that path to the toBaseFolder to build the new destination file path.

Author: James Laderoute
Last modified: March 2021
Website: softwarejim.com

"""

from tkinter import ttk
from tkinter import *
from tkinter import (DISABLED, NORMAL)
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
from multiprocessing import Process, Manager, Queue
from queue import Empty

import os
import Pmw
import re # to use regular expressions
import shutil
import hashlib
import time # so we can time how long it takes to process things
import filecmp

releaseTitle = "BackupComputer"
releaseVersion = "1.0"
DELAY1 = 80

# Queue must be global
q = Queue()

class myVar():
    def __init__(self, uname, uvalue):
        self.name = uname
        self.value = uvalue


class MyApp():
    def __init__(self):
        self.root = Tk()
        self.root.title( releaseTitle + " " + releaseVersion)
        self.root.option_add('*tearOff', False)  # don't allow tear-off menus
        self.root.bind('<KeyPress>', key_press)
        self.root.protocol("WM_DELETE_WINDOW", exitApplication)
        self.myVarList = [] # List of myVar objects; Variables defined/modified from the backup list file
        self.backupFileContents = [] # Every non-comment line inside of the backup list file
        self.skipFiles = [] # Filenames that we do not want to backup
        self.defaultBackupFile = "" # This is the backup list file last used by the user
        self.basePath = os.path.dirname(os.path.realpath(__file__))
        self.configFileName = os.path.join(self.basePath , 'config_file.txt')
        self.treeViewWidget = None
        self.balloon = None
        self.root.geometry("1200x400")
        self.widgets = {}
        self.p1 = None

def exitApplication():
    if Gapp.p1 and Gapp.p1.is_alive():
        messagebox.showwarning(title="Backround process is still running", message="Please wait for backround process to complete")
    else:
        Gapp.root.destroy()
        exit()

def onGetValue():
    if Gapp.p1.is_alive():
        Gapp.root.after(DELAY1, onGetValue)
        return
    else:
        try:
            Gapp.widgets["RunBackup"].config(state=NORMAL)
            Gapp.widgets["TestBackup"].config(state=NORMAL)
            Gapp.widgets["StopBackup"].config(state=DISABLED)
            print( q.get(0))
        except Empty:
            print("queue is empty")

def main():

    Pmw.initialise()

    Gapp.balloon = Pmw.Balloon(Gapp.root)

    # --------- Create a standard MenuBar ----------------
    mb = createMenuBar(Gapp.root) 
    Gapp.root.columnconfigure(0, weight=1)
    Gapp.root.rowconfigure(0, weight=1)

    # ---------- Create Tree that display all the source backup files
    Gapp.treeViewWidget = ttk.Treeview(Gapp.root)
    vsb = ttk.Scrollbar(Gapp.root, orient="vertical", command=Gapp.treeViewWidget.yview)
    vsb.grid(row=0, column=1, sticky=N+S)
    Gapp.treeViewWidget.configure(yscrollcommand=vsb.set)
    columnNames = {'Target':40, 'Mode':12} # dictionary
    Gapp.treeViewWidget["columns"] = ("Target", "Mode")
    for name, colWidth in columnNames.items():
        Gapp.treeViewWidget.column(name, width=colWidth)
        Gapp.treeViewWidget.heading(name, text=name)
    Gapp.treeViewWidget.heading('#0', text="Source")
    Gapp.treeViewWidget.grid(row=0, column=0, sticky=N + E + W + S)
    # Setup a couple of tags so that we can use a striped style for the rows
    # listed in the tree listing.
    Gapp.treeViewWidget.tag_configure('oddrow', background="white")
    Gapp.treeViewWidget.tag_configure('evenrow', background="lightblue")
    #Gapp.treeViewWidget.config(selectmode = 'browse') # this allows only one item to be selected at a time

    # ---------- Create Widgets --------------------------
    fr2 = Frame(Gapp.root)
    fr2.columnconfigure(0, weight=1)
    fr2.columnconfigure(1, weight=1)
    fr2.columnconfigure(2, weight=1)
    fr2.grid(row=1, column=0, sticky=W+E)
    createButtonBalloonWidget(fr2, "RunBackup", "runBackup", "Begin the backup operation",     rowvalue=0, columnvalue=0)
    createButtonBalloonWidget(fr2, "TestBackup", "testBackup", "Do not really do the backups", rowvalue=0, columnvalue=1)
    createButtonBalloonWidget(fr2, "StopBackup", "stopBackup", "Stop current running backup job", rowvalue=0, columnvalue=2)

    # ---------- you can change sytle themes if you wish ----
    #
    # NOTE: you can only change the style of widgets created with the
    #       ttk.  prefix (eg. ttk.Button and not just Button)
    #
    style = ttk.Style(Gapp.root)             # get handle on the style object
    allThemes = style.theme_names()  # get list of all available themes
    currentTheme = style.theme_use() # find out what our current theme is set to
    style.theme_use('default')         # to change the theme (eg. "clam", "alt", "default", "classic")
    # exampleButton2.winfo_class()   # to find out class name eg. TButton; only seems to work interactively ; need focus?? 
    style.configure( 'TButton', foreground = 'blue' )  # to modify a themed widget
    style.configure( 'Treeview', background="#D3D3D3",
        foreground="black",
        rowheight=25,
        fieldbackground="#D3D3D3"
        )
    style.map('Treeview',
        background=[('selected', 'blue')])
                                                                  
    # Read the tool's configuration file. In there
    # it could mention the last backup input file to read.
    if os.path.exists(Gapp.configFileName):
        f = open(Gapp.configFileName, 'r')
        for line in f:
            line = line.rstrip()
            parts = line.split(" ")
            if parts[0]=="lastfile":
                Gapp.defaultBackupFile=parts[1]
        f.close()
    else:
        print("No config file located {}".format(Gapp.configFileName))

    if Gapp.defaultBackupFile:
        if not os.path.exists(Gapp.defaultBackupFile):
            Gapp.defaultBackupFile = os.path.join(Gapp.basePath , Gapp.defaultBackupFile)
        readBackupFile(Gapp.defaultBackupFile)

    print("Config File: {}".format(Gapp.configFileName))
    print("Default Backup File: {}".format(Gapp.defaultBackupFile)) 

    populateGuiList()

    # --------- go into main graphics loop now
    Gapp.root.mainloop()

def populateGuiList():
    # First thing we need to do is clear the current list contents.
    # We don't want to append to the list, we want to replace the list.
    for i in Gapp.treeViewWidget.get_children():
        Gapp.treeViewWidget.delete(i)

    isOdd=True
    mode = ""
    destination = ""
    for line in Gapp.backupFileContents:
        parts = line.replace('\t', ' ').split()
        if parts[0]=="skipFile":
            Gapp.skipFiles.append(parts[1].lower())
            continue
        if parts[0]=="set":
            setVarValue(parts[1], normalize(parts[2]))
            continue
        if parts[0]=="backup":
            source = normalize(parts[1])
            target = normalize(parts[2])
            mode = parts[3]
            item = addItemToTreeViewList(source=source, destination=target, mode=mode, flag=isOdd)
            isOdd = not isOdd
            Gapp.treeViewWidget.focus(item)

def addItemToTreeViewList(source="source", destination="destination", mode="mode", flag=True):
    global Gapp
    print("source={} destination={} mode={}".format(source, destination, mode))
    if flag==False:
        item = Gapp.treeViewWidget.insert("", 'end', text=source, values=(destination, mode), tags=('oddrow',))
    else:
        item = Gapp.treeViewWidget.insert("", 'end', text=source, values=(destination, mode), tags=('evenrow',))
    return item

def key_press(event):
    print( 'type:{}'.format(event.type))
    print( 'widget:{}'.format(event.widget))
    print( 'char: {}'.format(event.char))
    print( 'keysym: {}'.format(event.keysym))
    print( 'keycode: {}'.format(event.keycode))    

# 
def stopBackupProcess():
    if Gapp.p1:
        Gapp.p1.terminate()
        Gapp.widgets["RunBackup"].config(state=NORMAL)
        Gapp.widgets["TestBackup"].config(state=NORMAL)
        Gapp.widgets["StopBackup"].config(state=DISABLED)

# This is a callback function for a PushButton object
#
def btnCallback(param):
    nCopied = 0
    backupList = []

    if param in ["runBackup", "testBackup"]:
        for rowItem in Gapp.treeViewWidget.get_children():
            sourceFolder = Gapp.treeViewWidget.item(rowItem)['text']
            targetFolder = Gapp.treeViewWidget.item(rowItem)['values'][0]
            mode = Gapp.treeViewWidget.item(rowItem)['values'][1]
            backupList.append( [sourceFolder, targetFolder, mode] )
    if param=="runBackup":
        Gapp.widgets["RunBackup"].config(state=DISABLED)
        Gapp.widgets["TestBackup"].config(state=DISABLED)
        Gapp.widgets["StopBackup"].config(state=NORMAL)

        Gapp.p1 = Process(target=runTheBackup, args=(q, backupList, False, Gapp.skipFiles))
        Gapp.p1.start()
        Gapp.root.after(DELAY1, onGetValue)
        print(f"Backup Done. Backed up {nCopied} files.")
    elif param=="testBackup":
        nCopied = runTheBackup(None, backupList, True, Gapp.skipFiles)
        print(f"Test Backup Done. This would have backed up {nCopied} files.")
    elif param=="stopBackup":
        stopBackupProcess()
        print(f"Terminated backup job by user!")
    elif param=="openBackupFile":
        if openBackupFile():
            populateGuiList()
    else:
        print(f"bntCallback: was passed param={param}")
    return

def createButtonBalloonWidget(widget, name, actionName, balloonText, rowvalue, columnvalue):
  b=Button(widget, text=name, command=lambda: btnCallback(actionName))
  b.grid(row=rowvalue, column=columnvalue) #, sticky=W)
  Gapp.balloon.bind(b, balloonText)
  Gapp.widgets[name] = b

# normalize will substitute $NAMES with a match in the
# environment variables or in our local variable space.
#
def normalize(line):
    joined = ""
    count=0
    for linePart in line.split('\\'):
        count += 1
        expand=""
        if re.match( r'\$.*', linePart, re.I):
            expand = os.getenv(linePart[1:])
            #print(f"normalize: linePart[1:] is {linePart[1:]} and expand getenv is {expand}")
            if expand==None:
                expand = getVarValue(linePart[1:])
                #print(f"normalize: linePart[1:] is {linePart[1:]} and expand getVarValue is {expand}")
        if expand:
            linePart = expand
        joined = os.path.join(joined,linePart)
    if count>1 and -1==joined.find(':\\'):
        joined = joined.replace(":", ":\\")

    return(joined)

# getVarValue will look in our local variable space
# and return the value if it's found, otherwise it
# returns None
def getVarValue(name):
    for v in Gapp.myVarList:
        if v.name==name:
            return v.value
    return(None)

# define or modify a variable in our local variable space
def setVarValue(name,value):
    v = myVar(name,value)
    Gapp.myVarList.append(v)

def runTheBackup(q, backupList, skipbackup, skipFiles):
    startTime = time.time()
    totalCopies=0
    # Work off of the list in the treeViewWidget and not the backupFileContents here
    for rowItem in backupList:
        sourceFolder = rowItem[0]
        targetFolder = rowItem[1]
        mode = rowItem[2]

        if skipbackup:
            appPrint(f"Testing backup of {sourceFolder} to {targetFolder}")
        if os.path.exists(sourceFolder):
            copyCount = copyFolder( sourceFolder, targetFolder, mode, skipbackup, skipFiles)
            totalCopies += copyCount
            appPrint("Copied {} files.".format(copyCount))
        else:
            appPrint("Error: Source Directory Missing: {}".format(sourceFolder))
    endTime = time.time()
    appPrint("runTheBackup took {} seconds or {} minutes".format(endTime-startTime,(endTime-startTime)/60))
    if q:
        q.put(totalCopies)
    else:
        return totalCopies

def appPrint( someString ):
    print(someString)

# copyFolder - function that will copy a folder (and all it's files and 
#               sub-folders and files) to a target base-folder.
#
# Arguments:
#  
# srcFolderPath: Name of the source folder to be copied. These are the
#   files that you want to backup.
#
# targetBaseFolder:
#   This is the base folder of the target disk to copy the files to.
#
# copyMode:
#   There are two different copy modes that can be choosen. 
#
#   'relative'   :  Takes srcPath and appends that to destination path (minus the Drive letter of course)
#   'substitute' :  Takes the paths under the specified sourceRoot that it finds and appends that path
#                   minus the original sourceRoot to the destination root path.
#  
def copyFolder( srcFolderPath, targetBaseFolder, copyMode, skipbackup, skipFiles ):
    copiedCount = 0
    srcFolderPath = srcFolderPath.replace("//", '\\')
    appPrint(f"copyFolder( srcFolderPath={srcFolderPath} targetBaseFolder={targetBaseFolder} copyMode={copyMode})")
    # this is a recursive copy operation
    for srcRoot, dirs, files in os.walk(srcFolderPath):
        nFiles = len(files)
        nthFile = 0
        for f in files:
            if f.lower() in skipFiles:
                nFiles -= 1
                continue
            else:
                nthFile += 1
                srcFile = os.path.join(srcRoot, f)
                if copyMode=="relative":
                    srcRootPath = srcRoot.replace(":","__")
                    targetFile = os.path.join(targetBaseFolder, srcRootPath, f)
                elif copyMode=="substitute":
                    # srcFolderPath     => D:\JamesLaderoute\Pictures\2021\2021-03-13-doves
                    # targetBaseFolder  => F:\backups\scotty\C__\Users\Kirk\Pictures\2021\2021-03-13-doves
                    #
                    # srcRoot           => D:\JamesLaderoute\Pictures\2021\2021-03-13-doves 
                    # f                 => IMG_1297.CR2
                    # goal              => F:\backups\scotty\C__\Users\Kirk\Pictures\2021\2021-03-13-doves\IMG_1297.CR2
                    #
                    # srcRoot           => D:\JamesLaderoute\Pictures\2021\2021-03-13-doves\jpg
                    # f                 => 20210313-IMG-1298.jpg
                    # goal              => F:\backups\scotty\C__\Users\Kirk\Pictures\2021\2021-03-13-doves\jpg\20210313-IMG-1298.jpg
                    #
                    
                    srcRoot_Minus_srcFolderPath_Eq_DestFilePath = srcRoot.replace(srcFolderPath,'')  # \jpg
                    # NOTE: for join to work as we want we have to ensure our first char in the path is not the slash
                    if srcRoot_Minus_srcFolderPath_Eq_DestFilePath and srcRoot_Minus_srcFolderPath_Eq_DestFilePath[0] in ['/', '\\']:
                        srcRoot_Minus_srcFolderPath_Eq_DestFilePath = srcRoot_Minus_srcFolderPath_Eq_DestFilePath.replace('/', '', 1)
                        srcRoot_Minus_srcFolderPath_Eq_DestFilePath = srcRoot_Minus_srcFolderPath_Eq_DestFilePath.replace('\\', '', 1)
                    targetDestFolderPath = os.path.join(targetBaseFolder, srcRoot_Minus_srcFolderPath_Eq_DestFilePath) # F:\backups\scotty\C__\Users\Kirk\Pictures\2021\2021-03-13-doves\jpg
                    targetFile = os.path.join(targetDestFolderPath, f)
                else:
                    print("Error: wrong copyMode specified {}".format(copyMode))
                    continue

                if skipbackup:
                    print(f"\t {nthFile}/{nFiles} Testing backup for {srcFile} to {targetFile}")

                if True==filesAreDifferent(srcFile, targetFile):
                    if skipbackup:
                        copiedCount += 1
                    else:
                        if myCopyFile(srcFile, targetFile):
                            copiedCount += 1
    return copiedCount

def myCopyFile(srcFile, targetFile):
    try:
        os.makedirs(os.path.dirname(targetFile), exist_ok=True)
        shutil.copyfile( srcFile, targetFile)
    except OSError as err:
        print(f"Failed to copy {srcFile} to {targetFile} error is {err}.")
        return False
    return True


def checksum(filename, hash_factory=hashlib.md5, chunk_num_blocks=128):
    h = hash_factory()
    with open(filename,'rb') as f: 
        while chunk := f.read(chunk_num_blocks*h.block_size): 
            h.update(chunk)
    return h.digest()

def fileHashAreDifferent(srcFile, targetFile):
    isSame = filecmp.cmp(srcFile, targetFile)
    return not isSame

def fileSizesAreDifferent(srcFile, targetFile):
    srcSize = os.stat(srcFile).st_size
    targetSize = os.stat(targetFile).st_size 
    return not (srcSize == targetSize)

def filesAreDifferent(srcFile, targetFile):
    if not os.path.exists(targetFile):
        return True # no target file so we need to copy the src to dest
    if fileSizesAreDifferent(srcFile, targetFile):
        return True # if the file sizes differ, then means something is different
    if fileHashAreDifferent(srcFile, targetFile):
        return True # something different in the file contents, so copy src to dest
    return False

def openBackupFile():
    filevar = filedialog.askopenfile(title="Pick a Backup Listing File",
        filetypes=[('Backup Files', ['blist'])])
    if filevar == None:
        return False
    print("filevar is {}".format(filevar))
    readBackupFile(filevar.name)
    # update the last backup filename now
    writeConfigFile("lastfile", filevar.name)
    return True

def writeConfigFile(name,value):
    all_of_it = []
    found = False
    if os.path.exists(Gapp.configFileName):
        f = open(Gapp.configFileName,'r')
        for line in f:
            all_of_it.append(line)
        f.close()
    f = open(Gapp.configFileName, 'w')
    for line in all_of_it:
        parts = line.split(' ')
        if parts[0] == name:
            found = True
            line = "{} {}".format(name,value)
        f.write(line)
    if not found:
        f.write("{} {}".format(name,value))
    f.close()

# The backup text file contains all the folders on your computer that you wish
# to be backed up to your destination folder.
def readBackupFile(filename):
    if not os.path.exists(filename):
        return

    Gapp.backupFileContents.clear()
    f = open(filename, 'r')
    for line in f:
        # chomp line to remove trailing whitespace
        line = line.rstrip()
        if re.match(r'^\s*#', line , re.I):
            continue 
        if re.match(r'^\s*$', line, re.I):
            continue
        Gapp.backupFileContents.append(line)
    f.close()

# Create the main menubar for the application. This holds all of the category
# menus for the application and subsequent buttons that will preform the actions.
def createMenuBar(root):
    menubar = Menu(root)
    root.config(menu = menubar)
    mfile = Menu(menubar)
    medit = Menu(menubar)
    mhelp_ = Menu(menubar)
    menubar.add_cascade( menu = mfile, label = "File")
    menubar.add_cascade( menu = medit, label = "Edit")
    menubar.add_cascade( menu = mhelp_, label = "Help")
    mfile.add_command(label = 'New', command = lambda: print('TODO: New File'))
    mfile.add_separator()
    mfile.add_command(label = 'Open...', command = lambda: btnCallback("openBackupFile"))
    mfile.add_command(label = 'Save', command = lambda: btnCallback("save"))
    mfile.add_command(label = 'Exit', command = lambda: exitApplication())

    mfile.entryconfig('New', accelerator = 'Ctrl + N') # does not setup event, only puts text in btn
    mfile.entryconfig('Open...', accelerator = 'Ctrl + O')
    mfile.entryconfig('Save', accelerator = 'Ctrl + S')
    mfile.entryconfig('Exit', accelerator = 'Ctrl + Z')
    return(menubar)

if __name__ == "__main__":
    Gapp = MyApp()
    main()

