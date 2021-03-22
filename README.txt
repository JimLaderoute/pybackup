Purpose:
	To backup files from one area to another area.

ToDo:
- use multiple threads, one thread per toplevel folder [future]
- Have better text in the popup that says background processes are still running. It should
  say more like you have a Backup job that is still active. Would you like to stop it? Stopping
  the Backup job means some files may not get backed up.
- Add ability to SKIP a backup row (without having to remove it). If you know that say the Pictures folder
  would take hours, then maybe you can skip it every other backup that you do.
- Allow Adding and Removing rows from the list
- When copy fails, save this info to tell the user the summary of failures when it's done.
- Keep a summary of new things copied during the run, to show to the user. Currently we just print the number of
  files backed up. We would like to keep a log of the actual files that got backed up and allow the user
  to view them if they so choose to. Also, let them bring up a list of backup attempts that failed. Maybe this
  should be automatically brought up at the end? Or at least some popup dialog box that tells them what has 
  happened and have a button that says SHOW DETAILS, or something like that.
- Handle SymLinks; are we copying symlinks and how? Are they pointing to the old DISK or new DISK? Did
  it copy the symlink or did it try and copy the file that the symlink points to?
- Popup up a dialog box when the backup is done (or signify it in some way in the GUI)
- Refactor the code to use more classes; try and make this be a good example of professional looking code
  that follows all the design principles and design patterns.
- When it's in good-enough shape, put it on github and my website and let people know about it. 
- Create a binary image and create a downloadable installation script.

This requires packages.
	Pmw
	tkinter

sudo apt-get install software-properties-common	# if you don't already have this
sudo apt-add-repository universe
sudo apt-get update
sudo apt-get install python3-pip  # to install pip3 if you don't already have it
pip3 -h # to ensure you have it

pip3 install Pmw

sudo apt-get install python3-tk


