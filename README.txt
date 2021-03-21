Purpose:
	To backup files from one area to another area.

ToDo:
- use multiple threads, one thread per toplevel folder
- Add ability to SKIP a backup row (without having to remove it). If you know that say the Pictures folder
  would take hours, then maybe you can skip it every other backup that you do.
- The backup work is now done in a seperate process. We need to add a way to allow the user to ABORT that
  process if they so desire.
- Allow Adding and Removing rows from the list
- Add a Text window area for messages, instead of writting to the console with print()
- When copy fails, save this info to tell the user the summary of failures when it's done.
- Keep a summary of new things copied during the run, to show to the user.
- Handle SymLinks; are we copying symlinks and how? Are they pointing to the old DISK or new DISK? Did
  it copy the symlink or did it try and copy the file that the symlink points to?
- Maintain a list of the TARGET's MD5 value for faster compares of subsequent backups.
  3/20/2021 changed algorithm to use 'import filecmp' module and filecmp.cmp(f1,f2) method
  This is much faster than using MD5 hash. And now we don't really need to maintain a history of hashes.
- Popup up a dialog box when the backup is done (or signify it in some way in the GUI)



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


