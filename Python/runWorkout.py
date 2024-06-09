from tkinter import Tk, Label, StringVar, Frame, Button, W, LEFT, Canvas, Scrollbar, VERTICAL, simpledialog, messagebox
from datetime import datetime
import math
import requests
try:
    import winsound     # winsound is specific to Windows
except ImportError:     # Use 'beep' for non-Windows systems
    import os
    def playsound(frequency, duration):
        #apt-get install beep
        try:
            os.system('beep -f %s -l %s' % (frequency, duration))
        except Exception as e:
            print(f"Error playing sound: {e}")

else: # Import winsound successful for Windows systems
    def playsound(frequency, duration):
        try:
            winsound.Beep(frequency, duration)
        except RuntimeError as e:
            print(f"Error playing sound: {e}")

root = Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
print(screen_width, screen_height)

SHEET_NAME = ""
FONT_SETS = "Arial 20"
FONT_CURRENT_SET ="Arial 50 bold"
if screen_width < 1500:
    FONT_TIMER = "Arial 280 bold"
else:
    FONT_TIMER = "Arial 320 bold"
FONT_BUTTON = "Arial 14 bold"

Rept_text = []
Dist_text = []
Ti_text = []
Remarks_text = []
set_label = []

running = False
num_of_sets = 0
current_set_num = 1
current_rept_num = 1
total_rept_set = 1
total_secs = 0;
last_update_time = datetime.now()

def pad(n):
    # leading zeros
    return ('00' + str(n))[-2:]

def MMSS2Secs(s):
    # MM:SS format to Seconds
    return int(s[0:2]) * 60 + int(s[3:5])

def Secs2MMSS(secs):
    # Seconds to MM:SS format
    return pad(math.floor(secs / 60)) + ':' + pad(secs % 60)

def Secs2HHMMSS(secs):
    # Seconds to HH:MM:SS format
    return pad(math.floor(secs/3600)) + ':' + pad(math.floor(secs/60)%60) + ':' + pad(secs%60)

def counter_display():
    def count():
        global running
        global last_update_time
        global current_set_num
        global current_rept_num
        global total_rept_set
        global total_secs
        global num_of_sets
        
        if running:
            if (datetime.now() - last_update_time).seconds > 0:
                last_update_time = datetime.now()
                total_secs -= 1
                if total_secs == 0: # interval finished
                    print("interval finished")
                    playsound(440,150)
                    timer_label.config(fg="yellow")
                    current_rept_num += 1
                    if current_rept_num == (total_rept_set+1): # set finished
                        print("set finished")
                        current_rept_num = 1
                        current_set_num += 1
                        if current_set_num == num_of_sets: # workout finished
                            running = False
                            timer_text.set("E N D")
                            return
                        total_rept_set = int(Rept_text[current_set_num])
                        set_label[current_set_num-1].config(fg="white", bg="blue")
                        set_label[current_set_num].config(fg="pink", bg="blue")
                    total_secs = MMSS2Secs(Ti_text[current_set_num])    
                    current_set_text.set(str(current_rept_num) + " of " + set_display(current_set_num) + "\n" + Remarks_text[current_set_num])
                if total_secs < 3:
                    playsound(440,150)
                    timer_label.config(fg="red")
                timer_text.set(Secs2MMSS(total_secs))
            
            root.after(250, count)

    # Triggering the start of the counter.
    count()


def set_display(set_num):
  # Remove trailing whitespace and make string comparison case-insensitive
  if Dist_text[set_num].strip().upper() == "REST":
      return Dist_text[set_num] + " @" + Ti_text[set_num]
  else:    
      return Rept_text[set_num] + "x" + Dist_text[set_num] + " @" + Ti_text[set_num]
   
def btn_run():
    global running
    global last_update_time
    global total_secs
    global total_rept_set
    if running == False:
        print("Run")
        running = True
        BRun['state'] = 'disabled'
        BStop['state'] = 'normal'
        BPause['state'] = 'normal'
        total_secs = MMSS2Secs(Ti_text[current_set_num])
        total_rept_set = int(Rept_text[current_set_num])
        set_label[current_set_num].config(fg="pink", bg="blue")
        last_update_time = datetime.now()
        counter_display()

def btn_pause():
    global running    
    print("Pause")
    running=False
    BRun['state'] = 'normal'
    BStop['state'] = 'normal'
    BPause['state'] = 'disabled'


def btn_stop():
    global running
    global current_set_num
    global current_rept_num
    print("Stop")
    running = False
    set_label[current_set_num].config(fg="white", bg="blue")
    timer_label.config(fg="yellow")
    current_set_num = 1
    current_rept_num = 1
    BRun['state'] = 'normal'
    BStop['state'] = 'disabled'
    BPause['state'] = 'disabled'
    current_set_text.set(str(current_rept_num) + " of " + set_display(current_set_num) + "\n" + Remarks_text[current_set_num])
    timer_text.set(Ti_text[current_set_num])	
    
def update_scrollregion(event):
    SetsCanvas.configure(scrollregion=SetsCanvas.bbox("all"))

def btn_load():
    url = simpledialog.askstring("Input", "Enter the Google Sheets URL:", parent=root)
    if url:
        load_workout(url)

def load_workout(url):
    global Rept_text, Dist_text, Ti_text, Remarks_text
    global num_of_sets, current_set_num, current_rept_num

    Rept_text.clear()
    Dist_text.clear()
    Ti_text.clear()
    Remarks_text.clear()

    # Load workout from file
    try:    # Attempt to HTTP request sheet data
        r = requests.get(url + "/export?format=csv")
        r.raise_for_status()    # Checks status code of HTTP Request
        data = (r.content.decode("utf-8").split("\r\n"))[1:]

        print("Load workout")
        num_of_sets=len(data)
        for r in data:
            print(f"Processing line: {r}") # Debug text
            try:    # Attempt to parse sheet data
                workout_line = r.split(",")
                if len(workout_line) < 5:
                    raise IndexError("Not enough columns")
                if workout_line[1] == "" or workout_line[1] == 0:
                    workout_line[1] = "1"
                Rept_text.append(workout_line[1])
                Dist_text.append(workout_line[2])
                Ti_text.append(workout_line[3])
                Remarks_text.append(workout_line[4].rstrip('\n'))
            except IndexError as i:     # Error accessing index out of bounds
                print(f"Error parsing workout data: {i}")
    except requests.RequestException as r:
        print(f"Error parsing workout data: {r}")
        data =[]
        num_of_sets = 0
        return False

    # Debug Texts
    print(f"Rept_text: {len(Rept_text)} items")
    print(f"Dist_text: {len(Dist_text)} items")
    print(f"Ti_text: {len(Ti_text)} items")
    print(f"Remarks_text: {len(Remarks_text)} items")

    update_workout_display()
    return True

def update_workout_display():
    global set_label
    global current_set_num, current_rept_num

    for label in set_label:
        if isinstance(label, Label):
            label.destroy()

    set_label = []
    set_label.append("X")

    for row in range(num_of_sets):
        try:
            print(f"Displaying set {row}: {set_display(row)}, {Remarks_text[row]}") # Debug Text
            l = Label(canvasFrame, text=set_display(row) + "\n" + Remarks_text[row], justify=LEFT, anchor="w", 
                      bg="blue", fg="white", font=FONT_SETS, borderwidth=2, relief="groove")
            l.grid(sticky='nswe')
            set_label.append(l)
        except IndexError as i:
            print(f"Error displaying workout: {i}")

    current_set_num = 1
    current_rept_num = 1
    current_set_text.set(str(current_rept_num) + "of" + set_display(current_set_num) + "\n" + Remarks_text[current_set_num])
    timer_text.set(Ti_text[current_set_num])

# Create canvasFrame
SetsFrame = Frame(root, bg="blue")
SetsFrame.grid(row=0, column=0, rowspan=2, sticky='nswe')
SetsFrame.rowconfigure(0, weight=1) 
SetsFrame.columnconfigure(0, weight=1) 

SetsCanvas = Canvas(SetsFrame, width=400, height=screen_height-260, bg="blue")
SetsCanvas.grid(row=0, column=0, sticky='nswe')

canvasFrame = Frame(SetsCanvas, bg="blue")
SetsCanvas.create_window(0, 0, window=canvasFrame, anchor="nw")

# Initialize current_set_text and timer_text
current_set_text = StringVar()
timer_text = StringVar()

# Check if SHEET_NAME has data or prompt for URL
if not SHEET_NAME or not load_workout(SHEET_NAME):
    while True:
        url = simpledialog.askstring("Input", "Enter the Google Sheets URL:", parent=root)
        if url and load_workout(url):
            break
        else:
            messagebox.showerror("Error", "Failed to load from the URL. Please try again.")

# Dummy data
Rept_text.append("X")
Dist_text.append("X")
Ti_text.append("X")
Remarks_text.append("X")

print("Display workout")

setsScroll = Scrollbar(SetsFrame, orient=VERTICAL)
setsScroll.config(command=SetsCanvas.yview)
SetsCanvas.config(yscrollcommand=setsScroll.set)
setsScroll.grid(row=0, column=1, sticky="ns")

canvasFrame.bind("<Configure>", update_scrollregion)

# Display current set
current_set_text = StringVar()
current_set_label = Label(root, textvariable=current_set_text, font=FONT_CURRENT_SET, fg="white", bg="blue")
current_set_text.set(str(current_rept_num) + " of " + set_display(current_set_num) + "\n" + Remarks_text[current_set_num])
current_set_label.grid(row=0, column=1, sticky='ew')
# Display timer for next exit
timer_text = StringVar()
timer_label = Label(root, textvariable=timer_text, font=FONT_TIMER, width=5, fg="yellow", bg="blue")
timer_text.set(Ti_text[current_set_num])
timer_label.grid(row=1, column=1, sticky='nsew')

# Display buttons
bottom_frame = Frame(root)
bottom_frame.grid(column=1, columnspan=3)
BRun = Button(bottom_frame, text="Run", font=FONT_BUTTON, command=btn_run)
BRun.grid(column=1, row=0, padx=30, pady=15)
BPause = Button(bottom_frame, text="Pause", font=FONT_BUTTON, command=btn_pause, state='disabled')
BPause.grid(column=2, row=0, padx=30)
BStop = Button(bottom_frame, text="Stop", font=FONT_BUTTON, command=btn_stop, state='disabled')
BStop.grid(column=3, row=0, padx=30)
BLoad = Button(bottom_frame, text="Load", font=FONT_BUTTON, command=btn_load)
BLoad.grid(column=4, row = 0, padx= 30)

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=2)

root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

root.geometry(str(screen_width-100) + "x" + str(screen_height-100) + '+50+20')
try:
    if os.path.isfile("swimming_workout.ico"):
        root.iconbitmap("swimming_workout.ico")
        icon_set = True
    elif os.path.isfile("swimming_workout.bmp"):
        root.iconbitmap("swimming_workout.bmp")
        icon_set = True
    elif os.path.isfile("swimming_workout.xbm"):
        root.iconbitmap("swimming_workout.xbm")
        icon_set = True
except Exception as e:
    print(f"Failed to set icon: {e}")
root.title("Swimming Workout Assist")
root.mainloop()
