from optparse import OptionParser
from socket import *
import android, sys, threading, traceback, time
from subprocess import *
from time import sleep
from math import *
from datetime import date,timedelta,datetime
from threading import Timer

import pygtk
import gtk

import sys, subprocess, traceback

img_s1 = "/tmp/img2txt_s1.tiff"
img_s2 = "/tmp/img2txt_s2.tiff"
img_s3 = "/tmp/img2txt_s3.tiff"

txt_pre = "/tmp/img2txtout"

def process_ocr(image_file):

    try:
		src_name = image_file

		p = subprocess.Popen("convert " + src_name + " " + img_s1, shell=True)
		p.wait()
		p = subprocess.Popen("tiff2bw " + img_s1 + " " + img_s2, shell=True)
		p.wait()
		p = subprocess.Popen("convert " + img_s2 + " -lat 30x30-5% -median 1x1 " + img_s3, shell=True)
		p.wait()
		p = subprocess.Popen("tesseract " + img_s3 + " " + txt_pre + " -l eng", shell=True)
		p.wait()

		f = open(txt_pre + ".txt", "r")
		data = f.read()
		f.close()

		print data
		return data
    except:
		print "exception"
		traceback.print_exc(file=sys.stdout)
		return ""







def readFileFromDroid(droid, filename, bytesToRead):
  file_str = ""
  init_read = 1
  while 1:
    result = droid.readFileBytes(filename, bytesToRead, init_read).result
    init_read = 0
    if 'ecode' in result:
      break
    x = result['b64'].replace("\n","").replace("\n",'')
    file_str += decodestring(x)
    print "Len File Str: %9d Bytes Read: %9d Current Offset: %9d Len Decoded Bytes %9d"%(len(file_str),result['read'],result['offset'],len(decodestring(x)))
  return file_str

def init_android_instance(port, minUpdateTimeMs=1,minUpdateDistance=1):
	port = int(port)
	d = android.Android(("localhost", port))
	print ("Android Scripting Environment initialized..time to start locating")
	d.startLocating(minUpdateTimeMs,minUpdateDistance)
	ev = d.getLastKnownLocation()
	while not ev.result:
		sleep(4)
		print ev.result
	return d

def take_droid_person_picture(droid, filename, comments):
	results = droid.readLocation().result
	location = 0,0
	if 'gps' in results and len(results['gps']) >0:
		location = results['gps']['longitude'], results['gps']['latitude']
	elif 'network' in results and len(results['network']) >0:
		location = results['network']['longitude'], results['network']['latitude']
	# creates picture in specified directory, and it can be shared with others when they can link up
	droid.cameraInteractiveCapturePersonPicture( filename, comments, location[0],location[1])
	# need to pull back the image here
	file_str = readFileFromDroid(droid, filename, 65535)
	fname = os.path.pathsplit()[1]
	f = open(fname, 'wb')
	f.write(file_str)
	f.close()
	
	
def take_droid_ocr_picture(droid, filename, comments):
	results = droid.readLocation().result
	location = 0,0
	if 'gps' in results and len(results['gps']) >0:
		location = results['gps']['longitude'], results['gps']['latitude']
	elif 'network' in results and len(results['network']) >0:
		location = results['network']['longitude'], results['network']['latitude']
	# creates picture in specified directory, and it can be shared with others when they can link up
	droid.cameraInteractiveCapturePersonPicture( filename, comments, location[0],location[1])
	# need to pull back the image here
	file_str = readFileFromDroid(droid, filename, 65535)
	fname = os.path.pathsplit()[1]
	f = open(fname, 'wb')
	f.write(file_str)
	f.close()
	return process_ocr(file_str)
	

class PersonPictureWindow:
	def take_picture(self, widget, data=None):
		name_str = "Name: "+self.fname.get_text()+" "+self.lname.get_text()
		name_str += "\nEvent Id:"+self.event.get_text()
		name_str += "\nComments:"+self.comment.get_text()
		print name_str
		take_droid_person_picture(self.droid, self.filename.get_text(), name_str)
		hbox = gtk.HBox(False, 0)
		hbox.show()

		image = gtk.Image()
		image.set_from_file(self.filename.get_text())
		image.show()
		hbox.pack_start(image, True, True, 0)
		self.vbox.pack_start(hbox, True, True, 0)
		# take pciture here
		# perform processing here

	def __init__(self, droid):
		# create a new window
		self.droid = droid
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.set_size_request(200, 100)
		window.set_title("GTK Entry")
		window.connect("delete_event", lambda w,e: gtk.main_quit())

		
		vbox = gtk.VBox(False, 0)
		window.add(vbox)
		vbox.show()
		self.vbox = vbox
		
		hbox = gtk.HBox(False, 0)
		hbox.show()
		hbox = hbox
		
		label = gtk.Label("First Name")
		label.show()
		fname = gtk.Entry()
		fname.set_max_length(50)
		
		fname.set_text("First Name")
		fname.select_region(0, len(fname.get_text()))
		fname.show()
		self.fname = fname		
	
		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(fname, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)

		hbox = gtk.HBox(False, 0)
		hbox.show()
		label = gtk.Label("Last Name")
		label.show()
		
		lname = gtk.Entry()
		lname.set_max_length(50)

		lname.set_text("Last Name")
		lname.select_region(0, len(lname.get_text()))
		lname.show()
		self.lname = lname


		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(lname, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)
		
		
		hbox = gtk.HBox(False, 0)
		hbox.show()
		label = gtk.Label("Event Id")
		label.show()
		event = gtk.Entry()
		event.set_max_length(50)
		event.set_text("Event Id")
		event.show()
		
		self.event = event

		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(event, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)


		hbox = gtk.HBox(False, 0)
		hbox.show()
		label = gtk.Label("Comments")
		label.show()
		comment = gtk.Entry()
		comment.set_max_length(50)
		comment.set_text("")
		comment.show()
		self.comment = comment
		

		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(comment, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)
		label = gtk.Label("File Name")
		label.show()
		filename = gtk.Entry()
		filename.set_max_length(50)
		filename.set_text("")
		filename.show()
		self.filename = filename
		

		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(filename, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)

		hbox = gtk.HBox(False, 0)
		vbox.add(hbox)
		hbox.show()
				          
		# button should actually capture a picture from android
		button = gtk.Button("Take Picture with Phone")
		button.connect("clicked", self.take_picture, None)
		vbox.pack_start(button, True, True, 0)
		#button.grab_default()
		button.show()
		window.show()

class OcrPictureWindow:
	def take_picture(self, widget, data=None):
		comments = "Event Id:"+self.event.get_text()
		comments += "\nComments:"+self.comment.get_text()
		print comments
		ocr_results = take_droid_ocr_picture(self.droid, self.filename.get_text(), comments)
		hbox = gtk.HBox(False, 0)
		hbox.show()
		image = gtk.Image()
		image.set_from_file(self.filename.get_text())
		image.show()
		hbox.pack_start(image, True, True, 0)
		self.vbox.pack_start(hbox, True, True, 0)
		
		hbox = gtk.HBox(False, 0)
		hbox.show()
		TextBox = gtk.TextView()
		TextBox.set_wrap_mode(gtk.WRAP_WORD)
		TextBox.set_editable(True)
		TextBox.set_cursor_visible(True)        
		TextBox.set_border_window_size(gtk.TEXT_WINDOW_LEFT,1)
		TextBox.set_border_window_size(gtk.TEXT_WINDOW_RIGHT,1)
		TextBox.set_border_window_size(gtk.TEXT_WINDOW_TOP,1)
		TextBox.set_border_window_size(gtk.TEXT_WINDOW_BOTTOM,1)
		TextBox.set_text(ocr_results)
		
	def __init__(self, droid):
		# create a new window
		self.droid = droid
		window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		window.set_size_request(200, 100)
		window.set_title("GTK Entry")
		window.connect("delete_event", lambda w,e: gtk.main_quit())

		vbox = gtk.VBox(False, 0)
		window.add(vbox)
		vbox.show()
		self.vbox = vbox
		hbox = gtk.HBox(False, 0)
		hbox.show()
		self.hbox = hbox
		
		hbox = gtk.HBox(False, 0)
		hbox.show()
		label = gtk.Label("Event Id")
		label.show()
		event = gtk.Entry()
		event.set_max_length(50)
		event.set_text("Event Id")
		event.show()
		
		self.event = event

		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(event, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)


		hbox = gtk.HBox(False, 0)
		hbox.show()
		label = gtk.Label("Comments")
		label.show()
		comment = gtk.Entry()
		comment.set_max_length(50)
		comment.set_text("")
		comment.show()
		self.comment = comment
		

		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(comment, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)

		label = gtk.Label("File Name")
		label.show()
		filename = gtk.Entry()
		filename.set_max_length(50)
		filename.set_text("")
		filename.show()
		self.filename = filename
		

		hbox.pack_start(label, True, True, 0)		
		hbox.pack_start(filename, True, True, 0)
		vbox.pack_start(hbox, True, True, 0)	

		hbox = gtk.HBox(False, 0)
		vbox.add(hbox)
		hbox.show()
				          
		# button should actually capture a picture from android
		button = gtk.Button("Take Picture with Phone")
		button.connect("clicked", self.take_picture, None)
		vbox.pack_start(button, True, True, 0)
		#button.grab_default()
		button.show()
		window.show()

class PictureTakerWindow:
	def get_personal_photo(self, widget, data=None):
		# data should contain persons name, email, dob, etc.
		# data should include photo name
		# picture should capture the GPS coordinates
		# persons info along with event data should be captured
		print "Get Personal Photo button pushed"
		personWindow = PersonPictureWindow(self.droid)

	def get_ocr_photo(self, widget, data=None):
		# picture should capture the GPS coordinates
		# data should include photo name
		# picture should capture the GPS coordinates
		# persons info along with event data should be captured
		print "Get OCR button pushed"
	def destroy(self, widget, data=None):
		gtk.main_quit()

	def delete_event(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def __init__(self, droid):
		self.droid = droid
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)
		self.window.set_border_width(10)
		self.box1 = gtk.HBox(False, 0)
		self.window.add(self.box1)
		self.person = gtk.Button("Personal Photo")
		self.ocr = gtk.Button("OCR Photo")
		self.box1.pack_start(self.ocr, True, True, 0)
		self.box1.pack_start(self.person, True, True, 0)
		
		self.person.connect("clicked", self.get_personal_photo, None)
		self.ocr.connect("clicked", self.get_ocr_photo, None)
		#self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
		#self.window.add(self.person)
		#self.window.add(self.ocr)
		self.ocr.show()
		self.person.show()
		self.box1.show()
		self.window.show()
		
	
	def main(self):
		gtk.main()

droid = None

if __name__ == "__main__":
	
	droid = init_android_instance(sys.argv[1])
	app = PictureTakerWindow(droid)
	app.main()
	
	
