#!/usr/bin/env python
# coding: utf-8

"""
###################################################################################
# Andrea Favero          Rev. 24 April 2024
# 
# pi value approximation via Monte Carlo method and Central Limit Theorem
#
###################################################################################
"""

# __version__ variable
version = '0.0'



################  setting argparser ###############################################
import argparse

# argument parser object creation
parser = argparse.ArgumentParser(description='Arguments for pi estimation')

# --version argument is added to the parser
parser.add_argument('-v', '--version', help='Display version.', action='version',
                    version=f'%(prog)s ver:{version}')

args = parser.parse_args()   # argument parsed assignement
# #################################################################################





########################### imports ###############################################
import tkinter as tk                 # GUI library
import cv2                           # OpenCV library used for the Monte Carlo graphical part
from PIL import ImageTk, Image, ImageGrab # library for images

from threading import Thread         # library from threading (openCV, and Quesu, are operated in different threads from tkinter)
from queue import Queue              # library used to exchange data between openCV and tkinter
from enum import Enum, auto          # library used to generate tickets, used to exchange data between openCV and tkinter

import numpy as np                   # array management library
from numpy.random import uniform     # numpy function for random and uniformly dstributed values
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # library used for plotting charts in tkinter
import matplotlib.pyplot as plt      # library to make charts

import os.path, pathlib, json        # libraries for files and Json file management
import datetime as dt                # date and time library used as timestamp on a few situations (i.e. data log)
import time                          # time library
# #################################################################################





###################################################################################
###########  Classes for data exchange between tkinter and openCV  ################
###################################################################################

class TicketPurpose(Enum):
    SHARE_PI_VALUE = auto()


class Queue_manager():
    def __init__(self):
        self.queue_message = Queue() 
    

class Ticket:
   def __init__(self,
                ticket_type: TicketPurpose,
                ticket_value: str,
                ticket_bg: str):
       self.ticket_type = ticket_type
       self.ticket_value = ticket_value
       self.ticket_bg = ticket_bg
# #################################################################################






###################################################################################
################# Class for the settings management ###############################
###################################################################################
class Settings():
    def __init__(self):
        self.s = self.load_settings()
        if len(self.s) > 0:
            self.h = int(self.s['h'])                # h is parsed as integer (windows height for the openCV animation)
            self.wait = int(self.s['wait'])          # wait is parsed as integer (delay to initially slow down the dots plot)
            self.step = int(self.s['step'])          # step is parsed as integer (delay reduction step of the wait parameter)
            self.runs = int(self.s['runs'])          # runs is parsed as integer (number of Monte Carlo repetitions)
            self.dots = int(self.s['dots'])          # dots is parsed as integer (quantity of datapoints, dots when animation)
            self.animation = str(self.s['animation']) # animation is parsed as string (there are 3 levels of animation)
        else:
            self.close_window = True
            print("Error on loading settings")


    def get_settings(self):
        return self.s

    
    def load_settings(self):
        """Loades the settings s."""
        s = {}
        fname = 'pi_settings.txt'                    # file name for the settings
        folder = pathlib.Path().resolve()            # active folder
        fname = os.path.join(folder,fname)           # folder and file name for the settings
        if os.path.exists(fname):                    # case the settings file exists
            with open(fname, "r") as f:              # settings file is opened in reading mode
                s = json.load(f)                     # json file is parsed to a local dict variable
            s = self.parse_settings(s)               # parse the settings
        else:                                        # case the settings does not file exist
            print("Could not find pi_settings.txt")  # feedback is printed to the terminal    
        return s                                     # s (settings) is returned




    def save_settings(self, s):
        """Saves the settings s."""
        
        fname = 'pi_settings.txt'               # file name for the settings
        folder = pathlib.Path().resolve()       # active folder
        for key, value in s.items():            # iteration through the dict data
            s[key]=str(value)                   # values of data are converted to string
        os.umask(0) # The default umask is 0o22 which turns off write permission of group and others
        fname = os.path.join(folder, fname)     # folder and file name for the settings
        with open(os.open(fname, os.O_CREAT | os.O_WRONLY, 0o777), 'w') as f:  # settings_backup file is opened in writing mode
            f.write(json.dumps(s, indent=0))    # content of the setting file is saved in file
            f.truncate()                        # truncates file (prevents older characters at file-end, if new content is shorter)
        s = self.parse_settings(s)              # parse the settings
        return s




    def parse_settings(self, s):
        """Parse the settings s."""
        s['h'] = int(s['h'])                   # h is parsed as integer (windows height for the openCV animation)
        s['wait'] = int(s['wait'])             # wait is parsed as integer (delay to initially slow down the dots plot)
        s['step'] = int(s['step'])             # step is parsed as integer (delay reduction step of the wait parameter)
        s['runs'] = int(s['runs'])             # runs is parsed as integer (number of Monte Carlo repetitions)
        s['dots'] = int(s['dots'])             # dots is parsed as integer (quantity of datapoints, dots when animation)
        s['animation'] = str(s['animation'])   # animation is parsed as string (thre levels of animations)
        return s
# #################################################################################







###################################################################################
###################### Class for the Monte Carlo  t ###############################
###################################################################################

class MonteCarlo(Thread):
    
    def __init__(self):
        super().__init__()
  
        self.close_window = False
        
        s = settings.get_settings()
        self.step = int(str(s['step']))
        self.h = int(str(s['h']))
        self.w = int(1.7 * self.h)
        self.gap = int(0.04 * self.h)
        self.r = int((self.h -2*self.gap)//2)
        self.center = self.r
        
        self.x_text = self.h                    # x coordinate for the text starting position
        self.font = cv2.FONT_HERSHEY_SIMPLEX    # type of cv2 font used in this script
        self.fontScale1 = 0.00175 * self.h      # font size used, when not (locally)  changed
        self.fontScale2 = 0.0015 * self.h       # font size used, when not (locally)  changed
        self.fontColor = (255,255,255)          # font color, when not (locally) changed
        if self.fontScale2 < 0.6:               # case fontScale2 is smaller than 0.6 
            self.lineType = 1                   # font thickness is set to 1
        else:                                   # case fontScale2 is equal or larger than 0.6 
            self.lineType = 2                   # font thickness is set to 2
        
        self.init_draw()                        # cals the function that initializes the graphical area
    
    
    
    
    def init_draw(self):
        """Funtion generating the pixels arrays to base the animation upon."""
        self.sketch = np.zeros([self.h, self.w , 3],dtype=np.uint8)  # empty array
        self.sketch.fill(230)                   # array is filled with light gray
        
        
           
    
    
    def draw_square(self, thk):
        """Draws a square of side 2xradius, with thickness in argument."""
        
        # black square edge (outer square)
        cv2.rectangle(self.sketch, (self.gap, self.gap),
                      (self.gap+2*self.r, self.gap+2*self.r), (0, 0, 0), thk)
        
        # black square edge (1st sector)
        cv2.rectangle(self.sketch, (self.gap, self.gap),
                      (self.gap+self.r, self.gap+self.r), (0, 0, 0), thk)
        
        # black square edge (3rd sector)
        cv2.rectangle(self.sketch, (self.gap+self.r, self.gap+self.r),
                      (self.gap+2*self.r, self.gap+2*self.r), (0, 0, 0), thk)
        
        cv2.imshow('monte carlo', self.sketch)        # monte carlo window is shown
        key = cv2.waitKey(100)                        # showtime in ms
        
        if self.check_close_req(key):
            self.close_window = True
        
            


    def draw_circle(self, thk, animation):
        """Draws an animated circle of radius 'r', with thickness in argument."""
        
        if animation == 'min':
            cv2.circle(self.sketch, (self.gap+self.r, self.gap+self.r),
                       self.r, (0, 0, 0), thk) # black circle
            t_ref  = time.time()
            while time.time() - t_ref < 2:
                cv2.imshow('monte carlo', self.sketch)                  # 
                key = cv2.waitKey(1)                      # showtime in ms
                if self.check_close_req(key):
                    self.close_window = True
                    break
                
            self.redraw(thk, clean=True)
        
        else:
            idx = np.linspace(-np.pi, np.pi, self.r)
            x1 = int(np.cos(-np.pi)*self.r)+self.center+self.gap
            y1 = int(np.sin(-np.pi)*self.r)+self.center+self.gap
            for i in range(self.r -1):
                x2 = int(np.cos(idx[i+1])*self.r)+self.center+self.gap
                y2 = int(np.sin(idx[i+1])*self.r)+self.center+self.gap
                cv2.line(self.sketch, (x1, y1), (x2, y2), (0, 0, 0), thk)
                x1 = x2
                y1 = y2
                cv2.imshow('monte carlo', self.sketch)                  # 
                key = cv2.waitKey(1)                      # showtime in ms
                if self.check_close_req(key):
                    self.close_window = True
                    break


            
    def draw_arc(self, thk):
        """Draws an animated arc of radius '2r', with thickness in argument."""
        idx = np.linspace(-np.pi, np.pi, self.r)
        x1 = int(np.cos(-np.pi)*2*self.r)+self.gap
        y1 = int(np.sin(-np.pi)*2*self.r)+self.h-self.gap
        
        for i in range(self.r -1):
            x2 = int(np.cos(idx[i+1])*2*self.r)+self.gap
            y2 = int(np.sin(idx[i+1])*2*self.r)+self.h-self.gap
            cv2.line(self.sketch, (x1, y1), (x2, y2), (0, 0, 0), thk)
            x1 = x2
            y1 = y2
            
            cv2.imshow('monte carlo', self.sketch)  # 
            key = cv2.waitKey(1)                    # showtime in ms
            if self.check_close_req(key):
                self.close_window = True
                break



    def redraw(self, thk, clean=False):
        """Draws a gray square to erase previous draw.
            Redraws a square of side 2xradius and the circle, with thickness in argument."""
        if clean:
              # gray rectangle to 'erase' previous drawing
              cv2.rectangle(self.sketch, (0, 0), (self.gap+2*self.r+4, self.h),
                          (230, 230, 230), -1)
        
        # black square edge (outer square)
        cv2.rectangle(self.sketch, (-4, self.gap), (self.gap+2*self.r, self.h+4),
                      (0, 0, 0), thk)
        
        # black square edge (1st sector)
        cv2.rectangle(self.sketch, (self.gap, self.gap), (self.gap+2*self.r, self.h-self.gap),
                      (0, 0, 0), thk)
        
        # black square edge (3rd sector)
        cv2.rectangle(self.sketch, (-4, self.h-self.gap), (self.gap, self.h+4),
                      (0, 0, 0), thk)
        
        # black circle
        cv2.circle(self.sketch, (self.gap, self.h-self.gap), 2*self.r,
                   (0, 0, 0), thk)
        
        # the comand cv2.imshow() is not applied on purpose on this function


        

 

    def resize_draw(self, thk, animation):
        """Resizes as animation the square, circle and sectors, with fix top-right vertex."""
        
        if animation == 'min':
            idx = [self.r]
            idx2 = [2*self.r]
        else:
            idx = np.linspace(0, self.r, self.r)
            idx2 = np.linspace(self.r, 2*self.r, self.r)
        
        x2 = self.gap+2*self.r
        y1 = self.gap
        for i in range(len(idx)):
            # gray rectangle to 'erase' previous drawing
            cv2.rectangle(self.sketch, (0, 0), (self.gap+2*self.r+4, self.h),
                          (230, 230, 230), -1)
            # black square (outer square)
            cv2.rectangle(self.sketch, (self.gap-2*int(idx[i]), y1),
                          (x2, self.gap+2*self.r+2*int(idx[i])), (0, 0, 0), thk)
            
            # black square (1st sector)
            cv2.rectangle(self.sketch, (x2-int(idx2[i]), y1), (x2, y1+int(idx2[i])),
                          (0, 0, 0), thk)
            
            # black square (3rd sector)
            cv2.rectangle(self.sketch, (self.gap-2*int(idx[i]), y1+int(idx2[i])),
                          (x2-int(idx2[i]), self.gap+2*self.r+2*int(idx[i])),
                          (0, 0, 0), thk)
            
            # black circle
            cv2.circle(self.sketch, (x2-int(idx2[i]), y1+int(idx2[i])), self.r+int(idx[i]),
                       (0, 0, 0), thk)
            
            cv2.imshow('monte carlo', self.sketch)  # monte carlo window is shown
            key = cv2.waitKey(10)                   # showtime in ms
            if self.check_close_req(key):
                self.close_window = True
                break
        
        if not self.close_window:
            run = 0
            self.plot(run, in_circle_cum=0, i=0, pi=0, wait=2000, startup=True)
        

     
        

    def plot(self, run, in_circle_cum, i, pi, wait, startup=False):
        
        if startup:
            cv2.rectangle(self.sketch, (self.x_text, 4*self.gap),
                          (self.w, self.h), (230, 230, 230), -1)  # gray rectangle to 'erase' previous text
            cv2.putText(self.sketch, f'run = ', (self.x_text, 6*self.gap),
                        self.font, self.fontScale2,(0,0,0),self.lineType)
            cv2.putText(self.sketch, f'dots in circle = ', (self.x_text, 9*self.gap),
                        self.font, self.fontScale2,(0,0,0),self.lineType)
            cv2.putText(self.sketch, f'total dots = ', (self.x_text, 12*self.gap),
                        self.font, self.fontScale2,(0,0,0),self.lineType)
            cv2.putText(self.sketch, f'pi ~ ', (self.x_text, 15*self.gap),
                        self.font, self.fontScale1,(0,0,0),self.lineType)
        else:
            cv2.rectangle(self.sketch, (self.x_text, 4*self.gap),
                          (self.w, self.h), (230, 230, 230), -1)  # gray rectangle to 'erase' previous text
            cv2.putText(self.sketch, f'run = {run+1} of {self.runs}', (self.x_text, 6*self.gap),
                        self.font, self.fontScale2,(0,0,0),self.lineType)
            cv2.putText(self.sketch, f'dots in circle = {in_circle_cum[i]:,d}', (self.x_text, 9*self.gap),
                        self.font, self.fontScale2,(0,0,0),self.lineType)
            cv2.putText(self.sketch, f'total dots = {i+1:,d}', (self.x_text, 12*self.gap),
                        self.font, self.fontScale2,(0,0,0),self.lineType)
            cv2.putText(self.sketch, f'pi ~ {pi:.8f}', (self.x_text, 15*self.gap),
                        self.font, self.fontScale1,(0,0,0),self.lineType)
        
        cv2.imshow('monte carlo', self.sketch)          # 
        
        t_ref = time.time()
        while time.time() - t_ref < wait/1000:   # wait is ms for cv2 imshow
            key = cv2.waitKey(1)                 # showtime in ms
            if self.check_close_req(key):
                self.close_window = True
                break
            
                

        
        


    def print_formula(self):
        
        cv2.putText(self.sketch, f'pi = 4 x', (self.x_text, 3*self.gap),
                    self.font, self.fontScale2,(0,0,0),self.lineType)
        cv2.putText(self.sketch, f'dots in circle', (self.x_text+int(160*self.fontScale2),int(2.3*self.gap)),
                    self.font, self.fontScale2,(0,0,0),self.lineType)
        cv2.putText(self.sketch, f'total dots', (self.x_text+int(160*self.fontScale2), int(3.9*self.gap)),
                    self.font, self.fontScale2,(0,0,0),self.lineType)
        cv2.line(self.sketch, (self.x_text+int(155*self.fontScale2), int(2.7*self.gap)),
                 (self.x_text+int(370*self.fontScale2),int(2.7*self.gap)), (0,0,0), 2)
        
        cv2.imshow('monte carlo', self.sketch)
        key = cv2.waitKey(1)
        if self.check_close_req(key):
            self.close_window = True





    def write_log(self, pi_results):
        
        folder = pathlib.Path().resolve()            # active folder 
        folder = os.path.join(folder,'logs')         # folder to store the pi values
        if not os.path.exists(folder):               # if case the folder does not exist
            os.makedirs(folder)                      # folder is made if it doesn't exist
        
        datetime = dt.datetime.now().strftime('%Y%m%d_%H%M%S')  # date_time variable is assigned, for file name generation
        fname = 'Log_'+datetime+'.png'               # file name for the log
        fname = os.path.join(folder,fname)           # folder and file name for the settings

        with open(fname, 'w') as f:
            for pi in pi_results:
                f.write(str(pi)+'\n')



    def check_close_req(self, key):
        """Function that verifies is the ESC button is pressed when a CV2 window is opened.
        It also checks if the window closing 'X' of 'pi' window is pressed.
        The function returns True in case of window closig request."""
        
        try:                         # method to close CV2 windows, via the mouse click on the windows bar X
            if cv2.getWindowProperty("monte carlo", cv2.WND_PROP_VISIBLE) <1:  # X on top bar 
                return True          # True is returned
        except:                      # except case     
            pass                     # exception not really necessary, apart for having the try option
        
        if key == 27 & 0xFF:         # ESC button method to close CV2 windows
            return True              # True is returned






    def monte_carlo(self, runs, dots, animation):
        """This is the key program part for the Monte Carlo."""
        
        start = time.time()
        self.init_draw()
        self.runs = runs
        self.dots = dots
        self.pi = 3.14
        self.pi_error = 0
        self.pi_results = []
        
        blocks, block0 = 1, 1
        if self.dots >= 10000:
            blocks = int(np.sqrt(self.dots))
#             if self.runs * 
            block0 = dots - blocks**2
        
        self.draw_square(thk=1)                    # black square edge
        if not self.close_window:
            thk=1
            self.draw_circle(thk, animation)       # circle in square
        
        if not self.close_window:
            self.print_formula()

        # some sleep time to realize the graphic on screen
        if not self.close_window:
            wait = 3
            t_ref = time.time()
            while time.time() - t_ref < wait:
                cv2.imshow('monte carlo', self.sketch) # 
                key = cv2.waitKey(1)               # showtime in ms
                if self.check_close_req(key):
                    self.close_window = True
                    break
        
        if not self.close_window:
            thk=1
            self.resize_draw(thk, animation)


        for run in range(self.runs):
            
            if self.close_window:
                break
            
            x = uniform(low=0.0, high=1.0, size=dots)
            y = uniform(low=0.0, high=1.0, size=dots)
            d = np.sqrt(x**2 + y**2)
            in_circle = np.array(d <= 1, dtype = np.int8)
            in_circle_cum = np.cumsum(in_circle,dtype = np.int32)
            pi_arr = np.array([in_circle_cum[i]*4/i for i in range(1,dots)], dtype = np.float64)

            pi = pi_arr[dots-2]
            self.pi_results.append(pi)
            self.pi_error = pi-np.pi
            self.print_formula()


            for i in range(1, dots):
                
                if self.close_window:
                    break
                
                if animation == 'max' or animation == 'med' or run == 0 or run == self.runs-1: 
                    if d[i] <= 1:
                        cv2.circle(self.sketch, (self.gap+int(2*self.r*x[i]),
                                                 self.h-self.gap-int(2*self.r*(y[i]))), 1, (255, 0, 0), -1)
                    else:
                        cv2.circle(self.sketch, (self.gap+int(2*self.r*x[i]),
                                                 self.h-self.gap-int(2*self.r*(y[i]))), 1, (0, 0, 255), -1)
                    
                    if self.close_window:
                        break
                
                    if animation == 'max' or run==0:
                        if i % self.step == 0 and i > 0 and not self.close_window:
                            pi = pi_arr[i-1]
                            self.plot(run, in_circle_cum, i, pi, wait)
                            
                            newstep = max(1, i//100)
                            if newstep > self.step:
                                self.step = newstep
                                wait -= 10
                                wait = max(1, wait)
            
            
            self.plot(run, in_circle_cum, dots-1, pi, wait=1)             # last update for the printed dots
            
            # iteration results are sent to the queue, via a ticket, and a tkinter event generator is called
            ticket = Ticket(ticket_type=TicketPurpose.SHARE_PI_VALUE,
                            ticket_value=f"{pi_arr[i-1]}", ticket_bg='no')  # ticket with the iteration results
            queue_manager.queue_message.put(ticket)                       # ticket is added to the queue
            gui.trigger_event()                                           # an event is generated at the GUI class
            
            
            
            if run == self.runs-1 and not self.close_window:
                
                # resuming the overall results
                pi = sum(self.pi_results)/self.runs                       # average pi value is calculated
                self.pi_error = pi-np.pi                                  # deviation from pi value
                self.pi_st_dev = np.std(self.pi_results)                  # standard deviation of the calculated pi values
                
                # overal results are sent to the queue, via a ticket, and a tkinter event generator is called
                ticket = Ticket(ticket_type=TicketPurpose.SHARE_PI_VALUE,
                                ticket_value=f"{pi}", ticket_bg='yes')    # ticket with the overall results
                queue_manager.queue_message.put(ticket)                   # ticket is added to the queue
                gui.trigger_event()                                       # an event is generated at the GUI class
                
                # another the printed dots update, to incorporate the overall pi value
                self.plot(run, in_circle_cum, dots-1, pi, wait=1)
                
                # iteration results are printed on the monte carlo window
                if self.runs == 1:
                    cv2.rectangle(self.sketch, (self.x_text, 4*self.gap),
                                  (self.w, 7*self.gap), (230, 230, 230), -1)  # gray rectangle to 'erase' previous text
                    cv2.putText(self.sketch, f'made {self.runs} iteration', (self.x_text, 6*self.gap),
                                self.font, self.fontScale2,(0,0,0),self.lineType)
                else:
                    cv2.rectangle(self.sketch, (self.x_text, 4*self.gap),
                                  (self.w, 10*self.gap), (230, 230, 230), -1)  # gray rectangle to 'erase' previous text
                    cv2.putText(self.sketch, f'made {self.runs} iterations', (self.x_text, 6*self.gap),
                                self.font, self.fontScale2,(0,0,0),self.lineType)
                    cv2.putText(self.sketch, f'each one with', (self.x_text, 9*self.gap),
                                self.font, self.fontScale2,(0,0,0),self.lineType)
                    cv2.putText(self.sketch, f'error = {self.pi_error:.8f}', (self.x_text, 18*self.gap),
                                self.font, self.fontScale1,(0,0,0),self.lineType)
                    cv2.putText(self.sketch, f'st.dev = {self.pi_st_dev:.8f}', (self.x_text, 21*self.gap),
                                self.font, self.fontScale1,(0,0,0),self.lineType)
                
                # increease the separation between the circle and the square area
                self.redraw(thk=2, clean=False)       # enlarged the arc and square borders
                self.draw_arc(thk=2)                  # black circle, tick edge
            
            # updating the monte carlo windows
            if not self.close_window:                 # case no request to quit
                cv2.imshow('monte carlo', self.sketch)  # monte carlo windows is shown
            else:                                     # case there is a request to quit
                break                                 # for loop is interupted
    
            
            # quickly resuming the results of each run in the openCV window
            if not self.close_window:                 # case no request to quit
                if animation == 'min':                # case the animation selected is 'min'
                    cv2.waitKey(1)                    # showtime in ms (1ms)
                elif animation == 'med':              # case the animation selected is 'med'
                    cv2.waitKey(100)                  # showtime in ms (0.1 s)
                elif animation == 'max':              # case the animation selected is 'max'
                    cv2.waitKey(1000)                 # showtime in ms (1 s)
            else:                                     # case there is a request to quit
                break                                 # for loop is interupted
            
            # the openCV area is cleaned, for the next iteration
            self.redraw(thk=1, clean=True)
                
        if run == self.runs-1:                        # case it is the last run
            cv2.waitKey(10000)                        # showtime in ms (10 s)
                    
        cv2.destroyAllWindows()                       # all openCV windows are closed
        
        if self.close_window:
            if self.runs > 1 and run > 0 and len(self.pi_results)>=1:
                self.pi = sum(self.pi_results)/(run+1)
                self.pi_error = self.pi-np.pi
                self.pi_st_dev = np.std(self.pi_results)
                print("\nInterrupted runs before end")
                print(f"Made a total of {run} runs, each one with {self.dots} dots")
                print(f"Estimated pi = {self.pi:.8f}")
                print(f"Error = {self.pi_error:.8f}")
                print(f"St.dev = {self.pi_st_dev:.8f}")
                
        else:
            self.pi = sum(self.pi_results)/self.runs
            self.pi_error = self.pi-np.pi
            print(f"\nMade a total of {self.runs} runs, each one with {self.dots} dots")
            print(f"Estimated pi = {self.pi:.8f}")
            print(f"Error = {self.pi_error:.8f}")
            print(f"St.dev = {self.pi_st_dev:.8f}")
        
        
        # analysis time is printed, if at least one complete run
        if (not self.close_window and len(self.pi_results)>=1) or (not self.close_window and len(self.pi_results)>1):
            tot_time = round(time.time()-start,2)
            hours = int(tot_time // 3600)
            minutes = int(tot_time % 3600 // 60)
            seconds = int(tot_time % 3600 % 60)
            print("Total time =", '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds), "(animation =", str(animation)+")")
            print()
            
            # pi values data is saved into a text file
            self.write_log(self.pi_results)
        
        # resets the close windows variable, for eventual new runs
        self.close_window = False
        
        try:
            return self.pi, self.pi_st_dev, self.pi_error, self.pi_results
        except:
            return self.pi, 0, self.pi_error, self.pi_results
# #################################################################################







###################################################################################
############################## Class for GUI ######################################
###################################################################################

class GUI(tk.Tk):

    def __init__(self):
        super().__init__()
        
        ########################### setting variables #############################
        self.histogram_window = None
        self.s = settings.get_settings()
        self.bind("<<CheckQueue>>", self.check_queue)
        
        # parsing the settings
        self.h = int(str(self.s['h']))
        self.runs = int(str(self.s['runs']))
        self.runs_unit = int(str(self.s['runs'])[:1])
        self.runs_multiplier = len(str(self.s['runs']))-1
        self.dots = int(str(self.s['dots']))
        self.dots_unit = int(str(self.s['dots'])[:1])
        self.dots_multiplier = len(str(self.s['dots']))-1
        self.animation = str(self.s['animation'])
        
        self.w = int(1.7 * self.h)
        
        self.pi_num_chrs = 14
        
        self.slide_num = 0
        
    

        ########################### setting the gui #####################################
        self.title("pi approximator")       # name is assigned to GUI root
        self.rowconfigure(0, weight=1)      # root is set to have 1 row of  weight=1
        self.columnconfigure(0,weight=1)    # root is set to have 1 column of weight=1
        self.resizable(1,1)
        
        self.ws = self.winfo_screenwidth()       # retrieves the width of the screen
        self.hs = self.winfo_screenheight()      # retrieves the height of the screen
        
        gui_w = 530                         # gui window width
        gui_h = 600                         # gui windows height
        self.geometry(f'{gui_w}x{gui_h}+{int(self.ws-gui_w)}+40') # windows is initially presented at top-right of the screen
        self.update()                       # force windows data updated
        
        main_w_w = self.winfo_width()       # retrieves the window width dimension set automatically 
        main_w_h = self.winfo_height()      # retrieves the window height dimension set automatically
        
        self.default_bg = self.cget("background")
        
        # main window goes to the only row/column, and centered
        self.create_mainWindow().grid(row=0,column=0,sticky='nsew')
        

             
    def trigger_event(self):
        self.event_generate("<<CheckQueue>>")
        
    
    def check_queue(self, event):
        """ Read the queue."""
        msg: Ticket
        msg= queue_manager.queue_message.get()
        if msg.ticket_type == TicketPurpose.SHARE_PI_VALUE:
            text = "pi ~ " + msg.ticket_value
            text = text[:self.pi_num_chrs]
            self.pi_value_label.configure(text=text)
            bg = msg.ticket_bg
            if bg == 'yes':
                self.pi_value_label.configure(bg='white')
            if bg == 'no':
                self.pi_value_label.configure(bg=self.default_bg)
            self.mainWindow.update()
    


    
    def create_mainWindow(self) -> tk.Frame:
        
        self.mainWindow = tk.Frame(self)    # main windows (called mainWindow) is derived from GUI
        
        #### runs related widgets ####
        self.runs_label = tk.LabelFrame(self.mainWindow, text="RUNS", labelanchor="nw", font=("Arial", "14"))
        self.runs_label.grid(row=0, column=0, rowspan=1, columnspan=4, sticky="n", padx=20, pady=8)

        # label for runs
        self.t_runs = tk.Label(self.runs_label, text = self.runs, width = 7, anchor = 'w', font=('arial','18'))
        self.t_runs.grid(row=0, column=0, sticky="W", padx=12, pady=5)

        # slider for the units
        self.s_runs_unit = tk.Scale(self.runs_label, label="UNIT", font=('arial','14'), orient='horizontal',
                                  relief='raised', length=150, from_=1, to_=9, resolution=1) 
        self.s_runs_unit.grid(row=0, column=1, sticky="w", padx=12, pady=5)
        self.s_runs_unit.set(self.runs_unit)
        self.s_runs_unit.bind("<ButtonRelease-1>", self.f_runs_unit)


        # slider for the multiplier (10 to the power of the slider value)
        self.s_runs_multiplier = tk.Scale(self.runs_label, label="x 10^", font=('arial','14'), orient='horizontal',
                                  relief='raised', length=150, from_=0, to_=6, resolution=1) 
        self.s_runs_multiplier.grid(row=0, column=2, sticky="w", padx=12, pady=5)
        self.s_runs_multiplier.set(self.runs_multiplier)
        self.s_runs_multiplier.bind("<ButtonRelease-1>", self.f_runs_multiplier)




        #### dots related widgets ####
        self.dots_label = tk.LabelFrame(self.mainWindow, text="DOTS", labelanchor="nw", font=("Arial", "14"))
        self.dots_label.grid(row=1, column=0, rowspan=1, columnspan=4, sticky="n", padx=20, pady=8)

        # label for runs
        self.t_dots = tk.Label(self.dots_label, text = self.dots, width = 7, anchor = 'w', font=('arial','18'))
        self.t_dots.grid(row=1, column=0, sticky="W", padx=12, pady=5)

        # slider for the units
        self.s_dots_unit = tk.Scale(self.dots_label, label="UNIT", font=('arial','14'), orient='horizontal',
                                  relief='raised', length=150, from_=1, to_=9, resolution=1) 
        self.s_dots_unit.grid(row=1, column=1, sticky="w", padx=12, pady=5)
        self.s_dots_unit.set(self.dots_unit)
        self.s_dots_unit.bind("<ButtonRelease-1>", self.f_dots_unit)


        # slider for the multiplier (10 to the power of the slider value)
        self.s_dots_multiplier = tk.Scale(self.dots_label, label="x 10^", font=('arial','14'), orient='horizontal',
                                  relief='raised', length=150, from_=3, to_=6, resolution=1) 
        self.s_dots_multiplier.grid(row=1, column=2, sticky="w", padx=12, pady=5)
        self.s_dots_multiplier.set(self.dots_multiplier)
        self.s_dots_multiplier.bind("<ButtonRelease-1>", self.f_dots_multiplier)



        #### save settings related widgets ####
        self.save_label = tk.LabelFrame(self.mainWindow, text="", labelanchor="nw", font=("Arial", "12"))
        self.save_label.grid(row=2, column=0, rowspan=1, columnspan=5, sticky="ns", padx=10, pady=8)

        self.b_save = tk.Button(self.save_label, text="SAVE  SETTINGS",
                                command= lambda: self.update_and_save(self.s), height=1, width=50)
        self.b_save.configure(font=("Arial", "12"))
        self.b_save.grid(column=1, row=1, sticky="w", rowspan=1, padx=10, pady=5)



        #### animation related widgets ####
        self.animation_label = tk.LabelFrame(self.mainWindow, text="ANIMATION", labelanchor="nw", font=("Arial", "14"))
        self.animation_label.grid(row=3, column=0, rowspan=1, columnspan=1, sticky="w", padx=20, pady=8)

        self.labels=["max", "med", "min"]    # levels of graphical animation
        self.gui_animation_var = tk.StringVar(self)
        for i, a_mode in enumerate(self.labels):
            rb=tk.Radiobutton(self.animation_label, text=a_mode, variable=self.gui_animation_var, value=a_mode)
            rb.configure(font=("Arial", "14"))
            rb.grid(column=0, row=i, sticky="w", padx=10, pady=12)
        self.gui_animation_var.set(self.animation)




        #### Monte Carlo method related widgets ####
        self.pi_label = tk.LabelFrame(self.mainWindow, text="MONTE CARLO", labelanchor="nw", font=("Arial", "14"))
        self.pi_label.grid(row=3, column=2, rowspan=1, columnspan=1, sticky="e", padx=10, pady=8)

        # btn to get info on screen
        self.b_info = tk.Button(self.pi_label, text="INFO",
                                command=lambda: self.show_info(self.h), height=1, width=7)
        self.b_info.configure(font=("Arial", "16"))
        self.b_info.grid(column=1, row=1, sticky="nsew", rowspan=1, padx=15, pady=4)

        # btn to start the Monte Carlo method
        self.b_pi = tk.Button(self.pi_label, text="\u03C0", command=self.start_monte_carlo , height=1, width=4) 
        self.b_pi.configure(font=("Arial", "42"))
        self.b_pi.grid(column=2, row=1, sticky="nsew", rowspan=1, padx=15, pady=5)
        
        
        # pi label, dynamically updated while Monte Carlo method is working
        self.pi_value_label = tk.Label(self.pi_label, text="", width=self.pi_num_chrs+2)
        self.pi_value_label.configure(font=("Arial", "24"))
        self.pi_value_label.grid(column=1, row=2, sticky="w", rowspan=1, columnspan=2, padx=10, pady=5)

 
        return self.mainWindow






    def f_runs_unit(self, val):
        self.runs_unit = int(self.s_runs_unit.get())        # runs unit from the slider assigned to the global variable
        self.runs = self.runs_unit * 10**self.runs_multiplier  # runs value is updated
        self.t_runs.configure(text = self.runs)             # change the label content
        self.t_runs.update()                                # force the text label updated
        self.s['runs'] = self.runs                          # settings is updated



    def f_runs_multiplier(self, val):
        self.runs_multiplier = int(self.s_runs_multiplier.get()) # runs multiplier from slider assigned to the global variable
        self.runs = self.runs_unit * 10**self.runs_multiplier  # runs value is updated
        self.t_runs.configure(text = self.runs)             # change the label content
        self.t_runs.update()                                # force the text label updated
        self.s['runs'] = self.runs                          # settings is updated



    def f_dots_unit(self, val):
        self.dots_unit = int(self.s_dots_unit.get())        # dots unit from the slider assigned to the global variable
        self.dots = self.dots_unit * 10**self.dots_multiplier  # dots value is updated
        self.t_dots.configure(text = self.dots)             # change the label content
        self.t_dots.update()                                # force the text label updated
        self.s['dots'] = self.dots                          # settings is updated



    def f_dots_multiplier(self, val):
        self.dots_multiplier = int(self.s_dots_multiplier.get()) # dots multiplier from slider assigned to the global variable
        self.dots = self.dots_unit * 10**self.dots_multiplier   # dots value is updated
        self.t_dots.configure(text = self.dots)             # change the label content
        self.t_dots.update()                                # force the text label updated
        self.s['dots'] = self.dots                          # settings is updated



    def update_and_save(self, s):
        s['animation'] = self.gui_animation_var.get()     # radio button is read
        settings.save_settings(s)



    def scroll_slides(self, direction):
        if direction == 'prev':
            self.slide_num -= 1
            if self.slide_num < 0:
                self.slide_num = int(len(self.slides) -1)
        elif direction == 'next':
            self.slide_num += 1
            if self.slide_num > len(self.slides) -1:
                self.slide_num = 0
        self.show_slide(self.slide_num)



    def show_slide(self, slide_num):
        img = self.slides[slide_num] # image is selected from the slides list
        img = Image.open(img)        # load the image
        img_w, img_h = img.size      # image size
        k = min(self.ws/img_w, self.hs/img_h) # coefficient screen vs image size
        img = img.resize((int(k*self.w),int(k*self.h))) # image resized
        img = ImageTk.PhotoImage(img)  # display image
        self.panel.img = img         # keep a reference so it's not garbage collected
        self.panel['image'] = img    



    def show_info(self, h):
        info_window = tk.Toplevel()
        info_window.title("Info")
        info_window.config(width= int(1.7*h), height=h)
        
        self.panel = tk.Label(info_window)
        self.panel.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="n", padx=20, pady=20)
        
        # button to load the previous slide
        prev_btn = tk.Button(info_window, text='<',
                             command=lambda: self.scroll_slides('prev'))
        prev_btn.configure(font=("Arial", "20"))
        prev_btn.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="w", padx=10, pady=20)
        
        # button to load the next slide
        next_btn = tk.Button(info_window, text='>',
                             command=lambda: self.scroll_slides('next'))
        next_btn.configure(font=("Arial", "20"))
        next_btn.grid(row=0, column=2, rowspan=1, columnspan=3, sticky="e", padx=10, pady=20)
        
        # button to close (destroy) the info window
        button_close = tk.Button(info_window, text="Close info", command=info_window.destroy)
        button_close.configure(font=("Arial", "14"))
        button_close.grid(row=0, column=1, rowspan=1, columnspan=3, sticky="ne", padx=20, pady=20)
        
        
        # manage the slides images
        self.slides = []
        slides_num = 9
        folder = pathlib.Path().resolve()            # active folder
        slide_names = ['Slide' + str(i) + '.jpg' for i in range(1,slides_num+1,1)]
        for fname in slide_names:
            img_fname = os.path.join(folder, 'info', fname)           # folder and file name for the settings
            self.slides.append(img_fname)
         
        self.show_slide(0) # shows the first slide
    

    
    

    def start_monte_carlo(self):     
                    
        if self.histogram_window:
            try:
                self.histogram_window.destroy()
            except tk.TclError:
                pass
        
        self.pi_value_label.configure(text="")
        self.pi_value_label.configure(bg=self.default_bg)
        self.mainWindow.update()
        
        # disable the Monte Carlo launch button
        self.b_pi['state'] = 'disabled'
        self.b_pi['relief'] = 'sunken'
        self.b_pi.update()
        self.mainWindow.update()
        
        animation = self.gui_animation_var.get() # checks the animation selection
        
        # starts the Monte Carlo
        pi, pi_st_dev, pi_error, pi_results = montecarlo.monte_carlo(self.runs, self.dots, animation)
        
        
        if len(pi_results)>=10:
            # calls a function to generate a histogram with the calculated pi values
            self.create_histogram(pi, pi_st_dev, pi_results, self.dots)
        
        # enable the Monte Carlo launch button
        self.b_pi['state'] = 'normal'
        self.b_pi['relief'] = 'raised'
        self.b_pi.update()
        self.mainWindow.update()
        
        return pi, pi_error, pi_results 



    def create_histogram(self, pi, pi_st_dev, pi_results, dots):
        
        datetime = dt.datetime.now().strftime('%Y%m%d_%H%M%S')  # date_time variable is assigned, for file name generation
        
        # number of Monte Carlo repeations
        runs = len(pi_results)
         
        # Create a new Tkinter window for the histogram
        self.histogram_window = tk.Toplevel(self.mainWindow)
        
        w = int(0.9*self.ws)
        h = int(0.9*self.hs)             
        self.histogram_window.geometry(f"{w}x{h}+10+40")    # Set the size and position of the Tkinter window
        self.histogram_window.title('Histogram')            # title for the new tkinter window       

        # clear the previous chart
        plt.clf()
        
        # Create the histogram
        plt.hist(pi_results, bins='scott', color='skyblue', edgecolor='black')

        # Set chart title and axes labels
        plt.title(f'pi  (avg = {str(pi)[:9]}, st.dev = {str(pi_st_dev)[:9]}, {runs} runs of {dots} dots)')
        plt.xlabel('Value')
        plt.ylabel('Frequency')

        # Display the histogram
        plt.tight_layout()

        # Embed the histogram into the Tkinter window
        canvas = FigureCanvasTkAgg(plt.gcf(), master=self.histogram_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Add a close button to the histogram window
        btn_close = tk.Button(self.histogram_window, text="Close", command=self.histogram_window.destroy)
        btn_close.place(relx=1, rely=0, anchor="ne", x=-10, y=10)  # Placing the close button on the top right
        
        folder = pathlib.Path().resolve()            # active folder 
        folder = os.path.join(folder,'charts')       # folder to store the hiostrogram images
        if not os.path.exists(folder):               # if case the folder does not exist
            os.makedirs(folder)                      # folder is made if it doesn't exist
        
        fname = 'histogram_'+datetime+'.png'         # file name for the histogram
        fname = os.path.join(folder,fname)           # folder and file name for the settings
        try:                                         # tentative
            plt.savefig(fname)                       # Save the current chart as an image file     
        except:                                      # in case of exception
            print("Could not save the histogram:", fname) # print a feedback to the terminal
            
        
    

    def on_closing(self):
        print("\nClosing the GUI application\n\n")   # feedback is printed to the terminal
        self.mainWindow.destroy()                    # frame mainWindow is destroyed
        time.sleep(0.5)                              # little delay
        self.destroy()                               # main window is destroyed
# #################################################################################





if __name__ == "__main__":
    
    settings = Settings()
    queue_manager = Queue_manager()    
    
    montecarlo = MonteCarlo()
    montecarlo.start()               # runs the MonteCarlo class in a separate thread
    
    gui = GUI()
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)    # closing the GUI
    gui.mainloop()

