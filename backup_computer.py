#!C:\Users\wheez\AppData\Local\Programs\Python\Python39\python.exe
# 
# Reads in a file of directories/files that we want to be backed up.
#
# This app will prompt you for the destination area you wish to backup to.
# The default area is in a config file.
#

from tkinter import ttk
from tkinter import *
from tkinter.ttk import *
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
        self.configFileName = os.path.join(self.basePath , 'config_file.txt')
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
    # Setup a couple of tags so that we can use a striped style for the rows
    # listed in the tree listing.
    Gapp.treeViewWidget.tag_configure('oddrow', background="white")
    Gapp.treeViewWidget.tag_configure('evenrow', background="lightblue")
    #Gapp.treeViewWidget.config(selectmode = 'browse') # this allows only one item to be selected at a time

    # ---------- Create Widgets --------------------------
    fr2 = Frame(Gapp.root)
    fr2.columnconfigure(0, weight=1)
    fr2.grid(row=1, column=0, sticky=W+E)
    createButtonBalloonWidget(fr2, "RunBackup", "runBackup", "Begin the backup operation", 0, 0)

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

        item = addItemToTreeViewList(source=line, destination=destination, mode=mode, flag=isOdd)
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
# This is a callback function for a PushButton object
#
def btnCallback(param):
    print("Clicked Me ",param)
    if param=="runBackup":
        runTheBackup()
    if param=="openBackupFile":
        if openBackupFile():
            populateGuiList()

def createButtonBalloonWidget(widget, name, actionName, balloonText, rowvalue, columnvalue):
  b=Button(widget, text=name, command=lambda: btnCallback(actionName))
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
    print("cp {}... to {} using mode {}".format(folderName, targetBaseFolder, copyMode))
    # this is a recursive copy operation
    for root, dirs, files in os.walk(folderName):
        #print("-----------------------")
        #print("root:{}".format(root))
        #print("dirs:{}".format(dirs))
        #print("files:{}".format(files))
        for f in files:
            if f in Gapp.skipFiles:
                pass
                #print("SKIP {} {}".format(root,f))
            else:
                print("copy file {} {} => ".format(root,f))
                srcFile = os.path.join(root, f)
                targetFile = "{}".format(f)
                #shutil.copyfile( srcFile, targetFile)

def openBackupFile():
    filevar = filedialog.askopenfile(title="Folders to be backed up",
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

