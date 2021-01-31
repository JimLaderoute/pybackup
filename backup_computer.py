#!C:\Users\wheez\AppData\Local\Programs\Python\Python39\python.exe
# 
# Reads in a file of directories/files that we want to be backed up.
#
# This app will prompt you for the destination area you wish to backup to.
# The default area is in a config file.
#

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
import re # to use regular expressions

releaseTitle = "BackupComputer"
releaseVersion = "1.0"

class myVar():
    def __init__(self, uname, uvalue):
        self.name = uname
        self.value = uvalue

myVarList = []
commandList = []
defaultBackupFile=""
basePath = os.path.dirname(os.path.realpath(__file__))
configFileName = 'config_file.txt'

def main():
    global defaultBackupFile
    global basePath
    global configFileName

    basePath = os.path.dirname(os.path.realpath(__file__))
    configFileName = basePath + '\\' + configFileName 

    root = Tk()
    root.title( releaseTitle + " " + releaseVersion)
    root.option_add('*tearOff', False)  # don't allow tear-off menus
    root.bind('<KeyPress>', key_press)
    
    # --------- Create a standard MenuBar ----------------
    mb = createMenuBar(root)  

    # ---------- Create Widgets --------------------------

    #exampleLabel   = ttk.Label(root, text="Example Label").pack()
    exampleButton1 = ttk.Button(root, text="Run Backup", command = lambda: btnCallback("runBackup") ).pack()
  
    # ---------- you can change sytle themes if you wish ----
    #
    # NOTE: you can only change the style of widgets created with the
    #       ttk.  prefix (eg. ttk.Button and not just Button)
    #

    style = ttk.Style()             # get handle on the style object
    allThemes = style.theme_names()  # get list of all available themes
    currentTheme = style.theme_use() # find out what our current theme is set to
    style.theme_use('vista')         # to change the theme
    # exampleButton2.winfo_class()   # to find out class name eg. TButton; only seems to work interactively ; need focus?? 
    style.configure( 'TButton', foreground = 'blue' )  # to modify a themed widget
                                                                  
    # Read the tool's configuration file. In there
    # it could mention the last backup input file to read.
    if os.path.exists(configFileName):
        f = open(configFileName, 'r')
        for line in f:
            line = line.rstrip()
            parts = line.split(" ")
            if parts[0]=="lastfile":
                defaultBackupFile=parts[1]
        f.close()

    if defaultBackupFile:
        if not os.path.exists(defaultBackupFile):
            defaultBackupFile = basePath + "\\" + defaultBackupFile
        readBackupFile(defaultBackupFile)

    print("Config File: {}".format(configFileName))
    print("Default Backup File: {}".format(defaultBackupFile)) 
    # --------- go into main graphics loop now
    root.mainloop()

def key_press(event):
    print( 'type:{}'.format(event.type))
    print( 'widget:{}'.format(event.widget))
    print( 'char: {}'.format(event.char))
    print( 'keysym: {}'.format(event.keysym))
    print( 'keycode: {}'.format(event.keycode))    
# This is a callback function for a PushButton object
#
def btnCallback(param):
    print("Clicked Me ",param)
    if param=="runBackup":
        runTheBackup()
    if param=="open":
        openFile()

def normalize(line):
    result = line
    expand=""
    if re.match( r'\$.*', line, re.I):
        expand = os.getenv(line[1:])
        if expand==None:
            expand = getVarValue(line[1:])
    if expand:
        result = expand
    return(result)

def getVarValue(name):
    global myVarList
    for v in myVarList:
        if v.name==name:
            return v.value
    return(None)

def setVarValue(name,value):
    global myVarList
    v = myVar(name,value)
    myVarList.append(v)

def runTheBackup():
    global commandList
    mode = ""
    destination = ""
    for line in commandList:
        parts = line.split(" ")
        if parts[0]=="destination":
            destination = normalize(parts[1])
            continue
        if parts[0]=="mode":
            mode = normalize(parts[1])
            continue
        if parts[0]=="set":
            setVarValue(parts[1], normalize(parts[2]))
            continue
        if len(parts)==1:
            dirparts = line.split("/")
            dirparts[0] = normalize(dirparts[0])
            line = '/'.join(dirparts)
        print("cp {} to {} using mode {}".format(line,destination,mode))
        

def openFile():
    filevar = filedialog.askopenfile()
    if filevar == None:
        return
    readBackupFile(filevar.name)
    # update the last backup filename now
    writeConfigFile("lastfile", filevar.name)

def writeConfigFile(name,value):
    global configFileName
    all_of_it = []
    found = False
    f = open(configFileName,'r')
    for line in f:
        all_of_it.append(line)
    f.close()
    f = open(configFileName, 'w')
    for line in all_of_it:
        parts = line.split(' ')
        if parts[0] == name:
            found = True
            line = "{} {}".format(name,value)
        f.write(line)
    if not found:
        f.write("{} {}".format(name,value))
    f.close()


def readBackupFile(filename):
    global commandList
    f = open(filename, 'r')
    for line in f:
        # chomp line to remove trailing whitespace
        line = line.rstrip()
        if re.match(r'^\s*#', line , re.I):
            continue 
        if re.match(r'^\s*$', line, re.I):
            continue
        commandList.append(line)
    f.close()

def createMenuBar(root):
    menubar = Menu(root)
    root.config(menu = menubar)
    file = Menu(menubar)
    edit = Menu(menubar)
    help_ = Menu(menubar)
    menubar.add_cascade( menu = file, label = "File")
    menubar.add_cascade( menu = edit, label = "Edit")
    menubar.add_cascade( menu = help_, label = "Help")
    file.add_command(label = 'New', command = lambda: print('TODO: New File'))
    file.add_separator()
    file.add_command(label = 'Open...', command = lambda: btnCallback("open"))
    file.add_command(label = 'Save', command = lambda: btnCallback("save"))
    file.add_command(label = 'Exit', command = lambda: exit())

    file.entryconfig('New', accelerator = 'Ctrl + N') # does not setup event, only puts text in btn
    file.entryconfig('Open...', accelerator = 'Ctrl + O')
    file.entryconfig('Save', accelerator = 'Ctrl + S')
    file.entryconfig('Exit', accelerator = 'Ctrl + Z')
    return(menubar)

if __name__ == "__main__":
    main()



