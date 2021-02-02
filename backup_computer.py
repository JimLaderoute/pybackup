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
import Pmw
import re # to use regular expressions
import shutil

releaseTitle = "BackupComputer"
releaseVersion = "1.0"

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
        self.configFileName = self.basePath + '\\' + 'config_file.txt'
        self.treeViewWidget = None
        self.balloon = None

def exitApplication():
     Gapp.root.destroy()
     exit

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

    #Gapp.treeViewWidget.config(selectmode = 'browse') # this allows only one item to be selected at a time

    # ---------- Create Widgets --------------------------
    fr2 = Frame(Gapp.root)
    fr2.columnconfigure(0, weight=1)
    fr2.grid(row=1, column=0, sticky=W+E)
    createButtonBalloonWidget(fr2, "RunBackup", "Begin the backup operation", 0, 0)

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
    if os.path.exists(Gapp.configFileName):
        f = open(Gapp.configFileName, 'r')
        for line in f:
            line = line.rstrip()
            parts = line.split(" ")
            if parts[0]=="lastfile":
                Gapp.defaultBackupFile=parts[1]
        f.close()

    if Gapp.defaultBackupFile:
        if not os.path.exists(Gapp.defaultBackupFile):
            Gapp.defaultBackupFile = Gapp.basePath + "\\" + Gapp.defaultBackupFile
        readBackupFile(Gapp.defaultBackupFile)

    print("Config File: {}".format(Gapp.configFileName))
    print("Default Backup File: {}".format(Gapp.defaultBackupFile)) 

    populateGuiList()
    # --------- go into main graphics loop now
    Gapp.root.mainloop()

def populateGuiList():
    mode = ""
    destination = ""
    for line in Gapp.backupFileContents:
        parts = line.split(" ")
        if parts[0]=="destination":
            destination = normalize(parts[1])
            continue
        if parts[0]=="mode":
            mode = normalize(parts[1])
            continue
        if parts[0]=="skipFile":
            Gapp.skipFiles.append(parts[1])
            continue
        if parts[0]=="set":
            setVarValue(parts[1], normalize(parts[2]))
            continue
        if len(parts)==1:
            dirparts = line.split("/")
            dirparts[0] = normalize(dirparts[0])
            line = '/'.join(dirparts)

        item = addItemToTreeViewList(source=line, destination=destination, mode=mode)
        Gapp.treeViewWidget.focus(item)

def addItemToTreeViewList(source="source", destination="destination", mode="mode"):
    global Gapp
    print("source={} destination={} mode={}".format(source, destination, mode))
    item = Gapp.treeViewWidget.insert("", 'end', text=source, values=(destination, mode))
    return item

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
        populateGuiList()

def createButtonBalloonWidget(widget, name, balloonText, rowvalue, columnvalue):
  b=Button(widget, text=name, command=lambda: btnCallback(name))
  b.grid(row=rowvalue, column=columnvalue, sticky=W+E)
  Gapp.balloon.bind(b, balloonText)

# normalize will substitute $NAMES with a match in the
# environment variables or in our local variable space.
#
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

def runTheBackup():
    mode = ""
    destination = ""
    for line in Gapp.backupFileContents:
        parts = line.split(" ")
        if parts[0]=="destination":
            destination = normalize(parts[1])
            continue
        if parts[0]=="mode":
            mode = normalize(parts[1])
            continue
        if parts[0]=="skipFile":
            Gapp.skipFiles.append(parts[1])
            continue
        if parts[0]=="set":
            setVarValue(parts[1], normalize(parts[2]))
            continue
        if len(parts)==1:
            dirparts = line.split("/")
            dirparts[0] = normalize(dirparts[0])
            line = '/'.join(dirparts)

        # If the code has reached here, then the 'line' represents
        # the source folder that we want to backup. We will backup
        # every file down the entire directory tree. Will will skip
        # any file listed in the skipFiles list.

        if os.path.exists(line):
            copyFolder( line, destination, mode)
        else:
            print("Error: Source Directory Missing: {}".format(line))
        
def copyFolder( folderName, targetBaseFolder, copyMode ):
    print("cp {}\\... to {} using mode {}".format(folderName, targetBaseFolder, copyMode))
    # this is a recursive copy operation
    for root, dirs, files in os.walk(folderName):
        #print("-----------------------")
        #print("root:{}".format(root))
        #print("dirs:{}".format(dirs))
        #print("files:{}".format(files))
        for f in files:
            if f in Gapp.skipFiles:
                pass
                #print("SKIP {}\\{}".format(root,f))
            else:
                print("copy file {}\\{} => ".format(root,f))
                srcFile = "{}\\{}".format(root, f)
                targetFile = "{}".format(f)
                #shutil.copyfile( srcFile, targetFile)

def openFile():
    filevar = filedialog.askopenfile()
    if filevar == None:
        return
    readBackupFile(filevar.name)
    # update the last backup filename now
    writeConfigFile("lastfile", filevar.name)

def writeConfigFile(name,value):
    all_of_it = []
    found = False
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


def readBackupFile(filename):
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
    file.add_command(label = 'Exit', command = lambda: exitApplication())

    file.entryconfig('New', accelerator = 'Ctrl + N') # does not setup event, only puts text in btn
    file.entryconfig('Open...', accelerator = 'Ctrl + O')
    file.entryconfig('Save', accelerator = 'Ctrl + S')
    file.entryconfig('Exit', accelerator = 'Ctrl + Z')
    return(menubar)

if __name__ == "__main__":
    Gapp = MyApp()
    main()

