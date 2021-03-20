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
import hashlib

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
        self.root.geometry("1200x400")

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
            #print(f"parts[1] is {parts[1]} and destination is {destination}")
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
    if param=="runBackup":
        runTheBackup()
        return

    if param=="openBackupFile":
        if openBackupFile():
            populateGuiList()
        return
    print("Clicked Me ",param)
    return

def createButtonBalloonWidget(widget, name, actionName, balloonText, rowvalue, columnvalue):
  b=Button(widget, text=name, command=lambda: btnCallback(actionName))
  b.grid(row=rowvalue, column=columnvalue, sticky=W+E)
  Gapp.balloon.bind(b, balloonText)

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
            copyCount = copyFolder( line, destination, mode)
            print("Copied {} files.".format(copyCount))
        else:
            print("Error: Source Directory Missing: {}".format(line))

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
def copyFolder( srcFolderPath, targetBaseFolder, copyMode ):
    copiedCount = 0
    srcFolderPath = srcFolderPath.replace("//", '\\')
    print("copyFolder( srcFolderPath={} targetBaseFolder={} copyMode={}".format(srcFolderPath, targetBaseFolder, copyMode))
    # this is a recursive copy operation
    for srcRoot, dirs, files in os.walk(srcFolderPath):
        for f in files:
            if f in Gapp.skipFiles:
                continue
            else:
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

                if True==filesAreDifferent(srcFile, targetFile):
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
    srcHash = checksum(srcFile)
    targetHash = checksum(targetFile)
    return not (srcHash == targetHash)

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

