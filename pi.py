#!/usr/bin/env python
# coding: utf-8

"""
###################################################################################
# Andrea Favero          Rev. 27 April 2024
# 
# pi value approximation via Monte Carlo method and Central Limit Theorem
#
###################################################################################
"""

# __version__ variable
version = '0.1'



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
from PIL import ImageTk, Image, ImageGrab # library for images management

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
    # A ticket class in used in 'between' tkinter and openCV, to share some data
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
        self.s = self.load_settings()                # the dict s is loaded
        if len(self.s) > 0:                          # case the dict is not empty
            self.h = int(self.s['h'])                # h is parsed as integer (windows height for the openCV animation)
            self.wait = int(self.s['wait'])          # wait is parsed as integer (delay to initially slow down the dots plot)
            self.step = int(self.s['step'])          # step is parsed as integer (delay reduction step of the wait parameter)
            self.runs = int(self.s['runs'])          # runs is parsed as integer (number of Monte Carlo repetitions)
            self.dots = int(self.s['dots'])          # dots is parsed as integer (quantity of datapoints, dots when animation)
            self.animation = str(self.s['animation']) # animation is parsed as string (there are 3 levels of animation)
        else:                                        # case the dict is empty
            self.close_window = True                 # close_window is set True
            print("Error on loading settings")       # feedback is printe to the terminal
    
    
    
    
    
    def get_settings(self):
        """Returns the settings s ."""
        return self.s
    
    
    
    
    
    def load_settings(self):
        """Loades the settings s ."""
        s = {}                                       # disct s is created
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
        """Saves the settings s ."""
        
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
        """Parse the settings s ."""
        s['h'] = int(s['h'])                    # h is parsed as integer (windows height for the openCV animation)
        s['wait'] = int(s['wait'])              # wait is parsed as integer (delay to initially slow down the dots plot)
        s['step'] = int(s['step'])              # step is parsed as integer (delay reduction step of the wait parameter)
        s['runs'] = int(s['runs'])              # runs is parsed as integer (number of Monte Carlo repetitions)
        s['dots'] = int(s['dots'])              # dots is parsed as integer (quantity of datapoints, dots when animation)
        s['animation'] = str(s['animation'])    # animation is parsed as string (thre levels of animations)
        return s
# #################################################################################







###################################################################################
###################### Class for the Monte Carlo  t ###############################
###################################################################################

class MonteCarlo(Thread):
    """Class for the monte carlo data generation and analysis.
    It uses openCV to display the output"""
    
    def __init__(self):
        super().__init__()
  
        self.close_window = False               # boolean to track is the openCV window gets closed (X on right side of the bar)
        
        s = settings.get_settings()             # settings are retrieved
        self.wait = int(str(s['wait']))         # initial delay in ms per each dot plotting
        self.step = int(str(s['step']))         # delay reduction step of the wait parameter
        self.h = int(str(s['h']))               # window height parameter
        self.w = int(1.7 * self.h)              # window width parameter is proportional to the height
        self.gap = int(0.04 * self.h)           # gap parameter is is proportional to the height
        self.r = int((self.h -2*self.gap)//2)   # radius parameter is proportional to the height
        self.center = self.r                    # radius r is assigned to center variable        
              
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
        
        cv2.imshow('monte carlo', self.sketch)  # monte carlo window is shown
        key = cv2.waitKey(100)                  # showtime in ms
        
        if self.check_close_req(key):           # case the window has been closed
            self.close_window = True            # close_window is set True
    
    
    
    
    
    
    def draw_circle(self, thk, animation):
        """Draws an animated circle of radius 'r', with thickness in argument."""
        
        if animation == 'min':                  # case the animation is set to 'min'
            cv2.circle(self.sketch, (self.gap+self.r, self.gap+self.r),
                       self.r, (0, 0, 0), thk)  # black circle
            
            t_ref  = time.time()                # current time is assigned to t_ref variable
            while time.time() - t_ref < 2:      # while loop for 2 seconds
                cv2.imshow('monte carlo', self.sketch)  # monte carlo window is shown
                key = cv2.waitKey(1)            # showtime in ms
                if self.check_close_req(key):   # case the window has been closed
                    self.close_window = True    # close_window is set True
                    break                       # while loop is interrupted
                
            self.redraw(thk, clean=True)        # redraw function is called, in cleaning mode 
        
        else:                                   # case the animation is not set to 'min'  
            idx = np.linspace(-np.pi, np.pi, self.r)   # evenly spaced array from -pi to pi, with r quantity of intervals
            x1 = int(np.cos(-np.pi)*self.r)+self.center+self.gap   # initial x coordinate
            y1 = int(np.sin(-np.pi)*self.r)+self.center+self.gap   # initial y coordinate
            for i in range(self.r -1):          # iteration over the interval r
                x2 = int(np.cos(idx[i+1])*self.r)+self.center+self.gap  # second x coordinate
                y2 = int(np.sin(idx[i+1])*self.r)+self.center+self.gap  # second y coordinate
                cv2.line(self.sketch, (x1, y1), (x2, y2), (0, 0, 0), thk)  # a line s drawn between (x1,y1) and (x2,y2)
                x1 = x2                         # the second x coordinate is assigned to the initial x coordinate
                y1 = y2                         # the second y coordinate is assigned to the initial x coordinate
                cv2.imshow('monte carlo', self.sketch)   # monte carlo window is shown
                key = cv2.waitKey(1)            # showtime in ms
                if self.check_close_req(key):   # case the window has been closed
                    self.close_window = True    # close_window is set True
                    break                       # for loop is interrupted
    
    
    
    
    
    
    def draw_arc(self, thk):
        """Draws an animated arc of radius '2r', with thickness in argument."""
        idx = np.linspace(-np.pi, np.pi, self.r)  # evenly spaced array from -pi to pi, with r quantity of intervals
        x1 = int(np.cos(-np.pi)*2*self.r)+self.gap   # initial x coordinate (x1)
        y1 = int(np.sin(-np.pi)*2*self.r)+self.h-self.gap  # initial x coordinate (y1)
        
        for i in range(self.r -1):              # iteration over the interval r
            x2 = int(np.cos(idx[i+1])*2*self.r)+self.gap   # second x coordinate (x2)
            y2 = int(np.sin(idx[i+1])*2*self.r)+self.h-self.gap  # second y coordinate (y2)
            cv2.line(self.sketch, (x1, y1), (x2, y2), (0, 0, 0), thk)  # a line s drawn between (x1,y1) and (x2,y2)
            x1 = x2                             # the second x coordinate is assigned to the initial x coordinate
            y1 = y2                             # the second y coordinate is assigned to the initial x coordinate
            
            cv2.imshow('monte carlo', self.sketch)  # monte carlo window is shown
            key = cv2.waitKey(1)                # showtime in ms
            if self.check_close_req(key):       # case the window has been closed
                self.close_window = True        # close_window is set True
                break                           # for loop is interrupted
    
    
    
    
    
    
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
        
        if animation == 'min':                  # case the animation is set to 'min'
            idx = [self.r]                      # a single value (the radius r) is assigned to idx
            idx2 = [2*self.r]                   # a single value (the diameter 2*r) is assigned to idx2
        else:                                   # case the animation is not set to 'min'
            idx = np.linspace(0, self.r, self.r) # evenly spaced array from 0 to r, with r quantity of intervals
            idx2 = np.linspace(self.r, 2*self.r, self.r) # evenly spaced array from r to 2*r, with r quantity of intervals
        
        x2 = self.gap+2*self.r                  # x2 coordinate, based on gap and radius r
        y1 = self.gap                           # y1 coordinate, based on gap
        
        for i in range(len(idx)):               #iteration over the idx intervals (one iteration in case of animation 'min')
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
            key = cv2.waitKey(10)               # showtime in ms
            if self.check_close_req(key):       # case the window has been closed
                self.close_window = True        # close_window is set True
                break                           # for loop is interrupted
        
        if not self.close_window:               # case close_window is set False 
            run = 0                             # zero is assigned to run variable
            self.plot_dots(run, in_circle_cum=0, i=0, pi=0, wait=2000, startup=True) # dots plotting function
    
    
    
    
    
    
    def plot_dots(self, run, in_circle_cum, i, pi, wait, startup=False):
        """Plots the monte carlo dots."""
        if startup:                             # case startup is set True (sketch gets prepared)
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
        
        else:                                   # case startup is set False (sketch is already prepared)
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
        
        cv2.imshow('monte carlo', self.sketch)  # monte carlo window is shown
        
        t_ref = time.time()                     # current time is assigne to t_ref variable
        while time.time() - t_ref < wait/1000:  # wait is ms for cv2 imshow
            key = cv2.waitKey(1)                # showtime in ms
            if self.check_close_req(key):       # case the window has been closed
                self.close_window = True        # close_window is set True
                break                           # for loop is interrupted
    
    
    
    
    
    
    def plot_formula(self):
        """Prints a repetitive part of the openCV sketch (the formula) ."""
        cv2.putText(self.sketch, f'pi ~ 4 x', (self.x_text, 3*self.gap),
                    self.font, self.fontScale2,(0,0,0),self.lineType)
        cv2.putText(self.sketch, f'dots in circle', (self.x_text+int(160*self.fontScale2),int(2.3*self.gap)),
                    self.font, self.fontScale2,(0,0,0),self.lineType)
        cv2.putText(self.sketch, f'total dots', (self.x_text+int(160*self.fontScale2), int(3.9*self.gap)),
                    self.font, self.fontScale2,(0,0,0),self.lineType)
        cv2.line(self.sketch, (self.x_text+int(155*self.fontScale2), int(2.7*self.gap)),
                 (self.x_text+int(370*self.fontScale2),int(2.7*self.gap)), (0,0,0), 2)
        
        cv2.imshow('monte carlo', self.sketch)  # monte carlo window is shown
        key = cv2.waitKey(1)                    # showtime in ms
        if self.check_close_req(key):           # case the window has been closed
            self.close_window = True            # close_window is set True
    
    
    
    
    
    
    def write_log(self, pi_results, datetime):
        """writes the estimated pi values (runs quantity) to a text file."""
        folder = pathlib.Path().resolve()       # active folder 
        folder = os.path.join(folder,'logs')    # folder to store the pi values
        if not os.path.exists(folder):          # if case the folder does not exist
            os.makedirs(folder)                 # folder is made if it doesn't exist
        
        fname = datetime + '_log.txt'           # file name for the log
        fname = os.path.join(folder,fname)      # folder and file name for the settings

        with open(fname, 'w') as f:             # opens the file fname in writing mode 
            for pi in pi_results:               # iterates on estimated pi values in pi_results
                f.write(str(pi)+'\n')           # writes one estimated pi value per row
    
    
    
    
    
    
    def check_close_req(self, key):
        """Function that verifies is the ESC button is pressed when a CV2 window is opened.
        It also checks if the window closing 'X' of 'pi' window is pressed.
        The function returns True in case of window closig request."""
        
        try:                                    # tentative
            # method to close CV2 windows, via the mouse click on the windows bar X
            if cv2.getWindowProperty("monte carlo", cv2.WND_PROP_VISIBLE) <1:  # X on top bar 
                return True                     # True is returned
        except:                                 # except case     
            pass                                # do nothing
        
        if key == 27 & 0xFF:                    # ESC button method to close CV2 windows
            return True                         # True is returned
    
    
    
    
    
    
    def prepare_sketch(self, animation):
        """Prepares the sketch."""
        self.init_draw()                        # init_draw function is called (prepare the sketch)
        
        if not self.close_window:               # in case close_window is not set True
            self.draw_square(thk=1)             # black square edge
        
        if not self.close_window:               # in case close_window is not set True 
            thk=1                               # thickness is set to 1
            self.draw_circle(thk, animation)    # circle in square is drawn
        
        if not self.close_window:               # in case close_window is not set True     
            self.plot_formula()                 # formula is plotted to the openCV sketch
        
        if not self.close_window:               # in case close_window is not set True
            # some sleep time to let user realizing about the graphic on screen
            wait = 3                            # 3 is assigned to wait variable
            t_ref = time.time()                 # current time is assigned to t_ref variable 
            while time.time() - t_ref < wait:   # while loop for wait seconds
                cv2.imshow('monte carlo', self.sketch) # monte carlo window is shown
                key = cv2.waitKey(1)            # showtime in ms
                if self.check_close_req(key):   # case the window has been closed
                    self.close_window = True    # close_window is set True
                    break                       # while loop is interrupted
        
        if not self.close_window:               # in case close_window is not set True
            thk=1                               # thickness is set to 1
            self.resize_draw(thk, animation)    # resize_draw function is called (from 4 sectors to 1st sector)
    
    
    
    
    
    
    def monte_carlo(self, runs, dots, animation):
        """This is the key program part for the Monte Carlo."""
        
        start = time.time()                     # current time is assignet to start variable
        
        self.pi_results = []                    # list for the estimated pi values (one value each run)
        
        # assigning local variables (from arguments) to montecarlo class 
        self.runs = runs                        # runs in argument is assigned to the montecarlo Class
        self.dots = dots                        # dots in argument is assigned to the montecarlo Class
        self.animation = animation              # animation in argument is assigned to the montecarlo Class
        
        # variables intended to be returned are initialized
        # this is done to prevent issues in case the the window gets closed before completion
        self.pi_ext = 3.14                      # 3.14 is assigned to pi_ext
        self.pi_error = 0                       # zero is assiged to pi_error
        self.pi_st_dev = 0                      # zero is assiged to pi_st_dev
        self.pi_error = 0                       # zero is assiged to pi_error
        self.datetime = ''                      # empty string is assiged to datetime
        
        # the sketch gets prepared
        if not self.close_window or not tk_running:  # in case close_window is not set True or tk got closed
            self.prepare_sketch(self.animation) # the sketch gets prepared (square, circle, quadrants, formula,etc)               
        
        
        # iterative part of the montecarlo function              
        for run in range(self.runs):            # iteration over the runs
            
            if self.close_window or not tk_running:  # in case close_window is not set True or tk got closed
                break                           # for loop is interrupted
            
            ########################   the key montecarlo part are these few lines of code   ##################
            x = uniform(low=0.0, high=1.0, size=self.dots)  # uniform distributed array for x coordinates (size=self.dots) 
            y = uniform(low=0.0, high=1.0, size=self.dots)  # uniform distributed array for y coordinates (size=self.dots) 
            d = np.sqrt(x**2 + y**2)                   # d (distance) array of the (x,y) point from origin (0,0)
            in_circle = np.array(d <= 1, dtype = np.int8)  # boolean array for the points within the circle area
            in_circle_cum = np.cumsum(in_circle, dtype = np.int32) # array with cumulative sum of the points within circle
            
            # array with extimated pi value, from the second iteration onward (zero division prevention)
            pi_arr = np.array([in_circle_cum[i]*4/i for i in range(1, self.dots)], dtype = np.float64)
            pi_arr = np.insert(pi_arr, 0, 4, axis=0)  # an arbitarry value of '4' is added in front
            
            pi_ext = pi_arr[self.dots-1]              # estimated pi is the last value of the pi_arr
            self.pi_results.append(pi_ext)            # the stimated pi is appendende to the pi_results list           
            self.pi_error = pi_ext-np.pi              # the error of the estimated pi is assigned to pi_error list
            # #################################################################################################

            
            # iterative part within each run
            for i in range(self.dots):                # iteration over the dots
                
                if self.close_window or not tk_running:  # in case close_window is not set True or tk got closed
                    break                             # for loop is interrupted
                
                
                
                # notes about the animation
                
                # when animation 'max':
                    # First run the dots are plot with increasing speed
                    # From second run dots are plot with the last speed used in 1st run
                
                # when animation 'med':
                    # First run the dots are plot with increasing speed
                    # From second run all dots are plot together
                
                # when animation 'min':
                    # First run the dots are plot with increasing speed
                    # From second run to last but, dots arenot printed
                    # The last run all dots are plotted together
                
                if animation == 'max' or animation == 'med' or run == 0 or run == self.runs-1:
                    if d[i] <= 1:      # case the dot falls within the circle: d array (distance) at pos i has value <= 1
                                       # dot is printed in blue
                        cv2.circle(self.sketch, (self.gap+int(2*self.r*x[i]),
                                                 self.h-self.gap-int(2*self.r*(y[i]))), 1, (255, 0, 0), -1)
                    else:              # case the dot falls outside the circle: : d array (distance) at pos i has value > 1
                                       # dot is printed in red
                        cv2.circle(self.sketch, (self.gap+int(2*self.r*x[i]),
                                                 self.h-self.gap-int(2*self.r*(y[i]))), 1, (0, 0, 255), -1)
                    
                    if self.close_window or not tk_running:  # in case close_window is not set True or tk got closed
                        break                         # for loop is interrupted
                
                    if run==0 or animation == 'max':  # case of the 1st run or animation is set 'max'
                        
                        if i % self.step == 0 and not self.close_window:   # case the iteration have not reached the 'step' value
                            self.pi_ext = pi_arr[i]   # the estimated pi value is retrieved from pi_arr (array of estimated pi values)
                            self.plot_dots(run, in_circle_cum, i, self.pi_ext, self.wait) # dots and updated info are plotted
                            
                            # approach used to make the animation accelerating 
                            newstep = max(1, i // 100)  # for the first 100 dots the new step remins at one 
                            if newstep > self.step:   # case newstep is bigger than the step
                                self.step = newstep   # newstep is assigned to step
                                self.wait -= 10       # wait time is reduced by 10 (ms)
                                self.wait = max(1, self.wait) # wait time is never smaller than 1 ms
            
            
            # last update for the printed dots and informations
            self.plot_dots(run, in_circle_cum, self.dots-1, pi_ext, wait=1)
            
            # iteration results are sent to the queue, via a ticket, and a tkinter event generator is called
            ticket = Ticket(ticket_type=TicketPurpose.SHARE_PI_VALUE,
                            ticket_value=f"{pi_arr[i-1]}", ticket_bg='no')  # ticket with the iteration results
            queue_manager.queue_message.put(ticket)   # ticket is added to the queue
            gui.trigger_event()                       # an event is generated at the GUI class
            
            
            
            if run == self.runs-1 and not self.close_window:  # case the run is the last one (and no closure request)
                
                # resuming the overall results
                pi_ext = sum(self.pi_results)/self.runs   # average pi value is calculated
                self.pi_error = pi_ext-np.pi          # deviation from pi value
                self.pi_st_dev = np.std(self.pi_results)  # standard deviation of the calculated pi values
                
                
                # overal results are sent to the queue, via a ticket, and a tkinter event generator is called
                ticket = Ticket(ticket_type=TicketPurpose.SHARE_PI_VALUE,
                                ticket_value=f"{pi_ext}", ticket_bg='yes') # ticket with the overall results
                queue_manager.queue_message.put(ticket)  # ticket is added to the queue
                gui.trigger_event()                   # an event is generated at the GUI class
                
                
                # another the printed dots update, to incorporate the overall pi value
                self.plot_dots(run, in_circle_cum, self.dots-1, pi_ext, wait=1)
                
                
                # iteration results are printed on the monte carlo window
                if self.runs == 1:                    # case the set runs is one
                    cv2.rectangle(self.sketch, (self.x_text, 4*self.gap),
                                  (self.w, 7*self.gap), (230, 230, 230), -1)  # gray rectangle to 'erase' previous text
                    cv2.putText(self.sketch, f'made {self.runs} iteration', (self.x_text, 6*self.gap),
                                self.font, self.fontScale2,(0,0,0),self.lineType)  # text plot to the sketch
                else:                                 # case the set runs is not one
                    cv2.rectangle(self.sketch, (self.x_text, 4*self.gap),
                                  (self.w, 10*self.gap), (230, 230, 230), -1)  # gray rectangle to 'erase' previous text
                    cv2.putText(self.sketch, f'made {self.runs} iterations', (self.x_text, 6*self.gap),
                                self.font, self.fontScale2,(0,0,0),self.lineType)  # text plot to the sketch
                    cv2.putText(self.sketch, f'each one with', (self.x_text, 9*self.gap),
                                self.font, self.fontScale2,(0,0,0),self.lineType)  # text plot to the sketch
                    cv2.putText(self.sketch, f'error = {self.pi_error:.8f}', (self.x_text, 18*self.gap),
                                self.font, self.fontScale1,(0,0,0),self.lineType)  # text plot to the sketch
                    cv2.putText(self.sketch, f'st.dev = {self.pi_st_dev:.8f}', (self.x_text, 21*self.gap),
                                self.font, self.fontScale1,(0,0,0),self.lineType)  # text plot to the sketch
                
                # enlarge black lines to visually increase separation between the circle and the square area
                self.redraw(thk=2, clean=False)       # enlarged the arc and square borders
                self.draw_arc(thk=2)                  # black circle, tick edge
            
            # updating the monte carlo windows
            if not self.close_window and not self.close_window: # case no request to quit (and no closure request)
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
            self.redraw(thk=1, clean=True)            # redraw function is called in 'cleaning' mode
                
        if run == self.runs-1:                        # case it is the last run
            cv2.waitKey(10000)                        # showtime in ms (10 s)
                    
        cv2.destroyAllWindows()                       # all openCV windows are closed
        
        if tk_running:                                # case tkinter is runnig
            if self.close_window:                     # case the openCV window got closed
                
                # case there is at least one run completed
                if self.runs > 1 and run > 0 and len(self.pi_results)>=1: 
                    self.pi_ext = sum(self.pi_results) / (run + 1) # estimated pi is calculated on the runs made (run)
                    self.pi_error = self.pi_ext - np.pi      # error of estimated pi from pi is calculated 
                    self.pi_st_dev = np.std(self.pi_results) # st.dev of estimated pi is calculated on the runs made (run)
                    print("\nInterrupted runs before end")   # feedback is printed to terminal
                    print(f"Made a total of {run} runs, each one with {self.dots} dots") # feedback is printed to terminal
                    print(f"Estimated pi = {self.pi_ext:.8f}") # feedback is printed to terminal
                    print(f"Error = {self.pi_error:.8f}")    # feedback is printed to terminal
                    print(f"St.dev = {self.pi_st_dev:.8f}")  # feedback is printed to terminal
                    
            else:                                     # case the openCV window is not closed
                self.pi_ext = sum(self.pi_results) / self.runs # estimated pi is calculated
                self.pi_error = self.pi_ext - np.pi   # error of estimated pi from pi is calculated 
                if runs == 1 or run == 1:             # case of one single run
                    print(f"\nMade one run with {self.dots} dots") # feedback is printed to terminal (singular form)
                elif run>1:                           # case of more runs
                    print(f"\nMade a total of {self.runs} runs, each one with {self.dots} dots")
                print(f"Estimated pi = {self.pi_ext:.8f}") # feedback is printed to terminal
                print(f"Error = {self.pi_error:.8f}")   # feedback is printed to terminal
                print(f"St.dev = {self.pi_st_dev:.8f}") # feedback is printed to terminal
            
        
            # analysis time is printed to terminal if at least one complete run
            if len(self.pi_results) >= 1:             # case there is at least one run completed
                tot_time = time.time()-start          # analysis time in seconds (float) is calculated
                hours = int(tot_time // 3600)         # hours are calculated
                minutes = int(tot_time % 3600 // 60)  # minutes are calculated
                seconds = int(tot_time % 3600 % 60)   # seconds are calculated
                
                # time is printed to terminal
                print("Total time =", '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds), "(animation =", str(animation)+")")
                print()                               # empty line is printed
            
            
            # a datetime reference is generated, for file name generation
            self.datetime = dt.datetime.now().strftime('%Y%m%d_%H%M%S')  # date_time variable is assigned, for file name generation
            
            if len(self.pi_results) >= 10:            # case there are at least 10 runs completed
                self.write_log(self.pi_results, self.datetime) # pi values data is saved into a text file
            
            # resets the close windows variable, for eventual new runs
            self.close_window = False                 # close_window is set Fasle
        
        # this function has a return
        return self.pi_ext, self.pi_st_dev, self.pi_error, self.pi_results, self.datetime

# #################################################################################







###################################################################################
############################## Class for GUI ######################################
###################################################################################

class GUI(tk.Tk):

    def __init__(self):
        super().__init__()
        
        ########################### setting variables #############################
        self.histogram_window = None                  # histogram_window is initially set as None
        
        self.s = settings.get_settings()              # settings are retrieved
        
        # based on https://www.youtube.com/watch?v=ghSDvtVJPck
        self.bind("<<CheckQueue>>", self.check_queue) # event CheckQueue will force a check_queue
        
        # parsing the settings
        self.h = int(str(self.s['h']))                # window height parameter (in JSON file)
        self.runs = int(str(self.s['runs']))          # number of runs (at JSON file), to initially set slider
        self.dots = int(str(self.s['dots']))          # number of dots (at JSON file), to initially set slider
        self.animation = str(self.s['animation'])     # type of animation
        
        
        # settings derived from those at JSON file 
        self.runs_unit = int(str(self.s['runs'])[:1])  # first digit in runs, for scientific notation
        self.runs_multiplier = len(str(self.s['runs'])) - 1  # number of digits in runs, less one
        
        self.dots_unit = int(str(self.s['dots'])[:1])  # first digit in dots, for scientific notation
        self.dots_multiplier = len(str(self.s['dots'])) - 1  # number of digits in dots, less one
        
        self.w = int(1.7 * self.h)                    # tkintew window width is proposrtional to the set height
        self.pi_num_chrs = 14                         # number of digits at tkinter label for estimate pi printing
        self.slide_num = 0                            # initial slide (at INFO) to start the scrolling 
        
    

        ########################### setting the gui #####################################
        self.title("pi approximator")                 # name is assigned to GUI root
        self.rowconfigure(0, weight=1)                # root is set to have 1 row of  weight=1
        self.columnconfigure(0,weight=1)              # root is set to have 1 column of weight=1
        self.resizable(1,1)
        
        self.ws = self.winfo_screenwidth()            # retrieves the width of the screen
        self.hs = self.winfo_screenheight()           # retrieves the height of the screen
        
        gui_w = 530                                   # gui window width
        gui_h = 600                                   # gui windows height
        self.geometry(f'{gui_w}x{gui_h}+{int(self.ws-gui_w)}+40') # windows is initially presented at top-right of the screen
        self.update()                                 # force windows data updated
        
        main_w_w = self.winfo_width()                 # retrieves the window width dimension set automatically 
        main_w_h = self.winfo_height()                # retrieves the window height dimension set automatically
        
        self.default_bg = self.cget("background")     # thedefault background color is assigned to default_bg variable
        
        # creation of the main window
        self.create_mainWindow().grid(row=0,column=0,sticky='nsew')  # main window has only one row/column, and it is centered
    
    
    
    
    
    def trigger_event(self):
        """Function to generate an event in the GUI class.
        The function can be conveniently be called from outside the class.
        Modified from https://www.youtube.com/watch?v=ghSDvtVJPck"""
        
        try:                                          # tentative
            self.event_generate("<<CheckQueue>>")     # generate a CheckQueue event
        except tk.TclError:                           # case of tkinter exception
            pass                                      # do nothing
    
    
    
    
    
    
    def check_queue(self, event):
        """ Read the queue.
        Based on https://www.youtube.com/watch?v=ghSDvtVJPck"""
        
        msg: Ticket                                   # annotation that msg variable is of a Ticket type
        msg = queue_manager.queue_message.get()       # queue content is retrieved, and assigned to msg
        
        if msg.ticket_type == TicketPurpose.SHARE_PI_VALUE:  # case the ticket_type in msg equals the purpose of SHARE_PI_VALUE method
            
            text = "pi ~ " + msg.ticket_value         # ticket_value string is used to form a new text string
            text = text[:self.pi_num_chrs]            # the text string is truncated based on pi_num_chrs number of chrs
            self.pi_value_label.configure(text=text)  # label 'pi_value_label' is updated with the new text
            
            bg = msg.ticket_bg                        # ticket_bg is retrieved and assigned to bg variable
            if bg == 'yes':                           # case bg equals to 'yes'
                self.pi_value_label.configure(bg='white')  # label 'pi_value_label' is updated with white background
            if bg == 'no':                            # case bg equals to 'no'
                self.pi_value_label.configure(bg=self.default_bg) # label 'pi_value_label' is updated with default_bg background
            
            self.mainWindow.update()                  # tkinter mainWindow is forced updated, to secure the label update
    
    
    
    
    
    
    def create_mainWindow(self) -> tk.Frame:
        """Function to create the mainWindow and related buttons."""
        self.mainWindow = tk.Frame(self)              # main windows (called mainWindow) is derived from GUI
        
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
        
        # radiobutton for animation level selection
        self.labels=["max", "med", "min"]             # levels of graphical animation
        self.gui_animation_var = tk.StringVar(self)   # tkinter variable string type is assigned to gui_animation_var
        for i, a_mode in enumerate(self.labels):      # iteration over the labels names
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
        """Function called by the RUNS unit slider.
        It updates the runs variable and the runs label."""
        self.runs_unit = int(self.s_runs_unit.get())  # runs unit from the slider assigned to the global variable
        self.runs = self.runs_unit * 10**self.runs_multiplier  # runs value is updated
        self.t_runs.configure(text = self.runs)       # change the label content
        self.t_runs.update()                          # force the text label updated
        self.s['runs'] = self.runs                    # settings is updated
    
    
    
    
    
    
    def f_runs_multiplier(self, val):
        """Function called by the RUNS multiplier slider.
        It updates the runs variable and the runs label."""
        self.runs_multiplier = int(self.s_runs_multiplier.get()) # runs multiplier from slider assigned to the global variable
        self.runs = self.runs_unit * 10**self.runs_multiplier  # runs value is updated
        self.t_runs.configure(text = self.runs)       # change the label content
        self.t_runs.update()                          # force the text label updated
        self.s['runs'] = self.runs                    # settings is updated
    
    
    
    
    
    
    def f_dots_unit(self, val):
        """Function called by the DOTS unit slider.
        It updates the dots variable and the dots label."""
        self.dots_unit = int(self.s_dots_unit.get())  # dots unit from the slider assigned to the global variable
        self.dots = self.dots_unit * 10**self.dots_multiplier  # dots value is updated
        self.t_dots.configure(text = self.dots)       # change the label content
        self.t_dots.update()                          # force the text label updated
        self.s['dots'] = self.dots                    # settings is updated
    
    
    
    
    
    
    def f_dots_multiplier(self, val):
        """Function called by the DOTS multiplier slider.
        It updates the dots variable and the run label."""
        self.dots_multiplier = int(self.s_dots_multiplier.get()) # dots multiplier from slider assigned to the global variable
        self.dots = self.dots_unit * 10**self.dots_multiplier   # dots value is updated
        self.t_dots.configure(text = self.dots)       # change the label content
        self.t_dots.update()                          # force the text label updated
        self.s['dots'] = self.dots                    # settings is updated
    
    
    
    
    
    
    def update_and_save(self, s):
        """Function to save the current gui setting.
        Animation radiobutton is read, before proceeding."""
        s['animation'] = self.gui_animation_var.get() # radio button is read
        settings.save_settings(s)                     # call the save_settings function of settings class
    
    
    
    
    
    
    def scroll_slides(self, direction):
        """Function to scroll the info slides."""
        if direction == 'prev':                       # case direction equals to 'prev'
            self.slide_num -= 1                       # slide_num is decremented
            if self.slide_num < 0:                    # case slide_num is negative
                self.slide_num = int(len(self.slides) -1)  # max slide number is assigned to slide_num variable
        
        elif direction == 'next':                     # case direction equals to 'next'
            self.slide_num += 1                       # slide_num is incremented
            if self.slide_num > len(self.slides) -1:  # case slide_num is bigger tha max number of slides
                self.slide_num = 0                    # zero is assigned to slide_num
        
        self.show_slide(self.slide_num)               # show_slide function is called, by passing the slide_num
    
    
    
    
    
    
    def show_slide(self, slide_num):
        """Function that loads and show images."""
        img = self.slides[slide_num]                  # image is selected from the slides list
        img = Image.open(img)                         # load the image
        img_w, img_h = img.size                       # image size
        k = min(self.ws/img_w, self.hs/img_h)         # coefficient screen vs image size
        img = img.resize((int(0.85*k*img_w),int(0.85*k*img_h))) # image resized
        img = ImageTk.PhotoImage(img)                 # display image
        self.panel.img = img                          # keep a reference so it's not garbage collected
        self.panel['image'] = img                     # image is assigned to panel dictionary
    
    
    
    
    
    
    def show_info(self, h):
        """Function that creates a window ."""
        info_window = tk.Toplevel(self.mainWindow)    # info_window is created
        info_window.title("Info")                     # info_window title
        info_window.config(width= int(1.7*h), height=h) # info_window dimension

        self.panel = tk.Label(info_window)            # a label widget is assigned to panel name
        self.panel.grid(row=0, column=0, rowspan=1, columnspan=3,
                        sticky="n", padx=20, pady=20) # panel widget is positioned in grid
        
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
        self.slides = []                              # empty list to append the slides
        slides_quantity = 9                           # number of slides
        folder = pathlib.Path().resolve()             # active folder
        
        # list with slides names is generated
        slide_names = ['Slide' + str(i) + '.jpg' for i in range(1, slides_quantity+1, 1)]
        
        for fname in slide_names:                     # iteration over the slide names in slides names
            img_fname = os.path.join(folder, 'info', fname) # folder and file name for the settings
            self.slides.append(img_fname)             # slide image names are appended to the list 'slides'
         
        self.show_slide(0)                            # shows the first slide
    
    
    
    
    
    
    def start_monte_carlo(self):     
        """Function in gui class to call the montecarlo function in montecarlo class.
        Calls the charts generation functions, based on the monte carlo returned values."""
        
        if self.histogram_window:                     # if histogram_window is True (not None, nor False)
            try:                                      # tentative
                self.histogram_window.destroy()       # close histogram_window window, from the eventual previous test
            except tk.TclError:                       # case of tkinter exception
                pass                                  # do nothing
        
        # initialize some variables
        self.pi_value_label.configure(text="")        # pi_value_label is set empty
        self.pi_value_label.configure(bg=self.default_bg) # pi_value_label backfround is set to default color
        self.mainWindow.update()                      # mainWindow gets a forced update, to ensure the label is updated
        
        # disable the Monte Carlo launch button
        self.b_pi['state'] = 'disabled'               # b_p (button for pi calculation) is disabled
        self.b_pi['relief'] = 'sunken'                # b_p (button for pi calculation) is recessed
        self.b_pi.update()                            # b_p (button for pi calculation) is updated
        self.mainWindow.update()                      # mainWindow gets a forced update, to ensure b_p is updated

        
        animation = self.gui_animation_var.get()      # checks the animation selection
        
        # starts the Monte Carlo
        pi, pi_st_dev, pi_error, self.pi_results, self.datetime = montecarlo.monte_carlo(self.runs, self.dots, animation)
        
        if tk_running:                                # check if the GUI has not been closed
            
            datapoints = len(self.pi_results)         # quantity of datapoints 
            if datapoints >= 50:                      # case there are at least 50 datapoints
                # when there are at least 50 datapoints, then it makes sense to plot some charts
            
                # preparing data arrays for plotting
                self.x = np.linspace(1, datapoints, datapoints)  # array with x axis values, from 1 to datapoints
                error=[]                              # empty list to collect the error values
                st_dev=[]                             # empty list to collect the standard deviation values
                for i in range(datapoints):           # iteration over the quantity of datapoints
                    if i==0:                          # case of the the array index
                        error.append((self.pi_results[0] - np.pi))  # error is calculated, from the first estimated pi result
                        st_dev.append(0)              # zero standard deviation is appended
                    else:                             # case not of the first array index
                        pi_cumulative = np.cumsum(self.pi_results[:i])  # a cumulative sum is performed until the index 'i'
                        pi_ext = pi_cumulative[-1] / i  # estimated pi for 'i' quantity of datapoints
                        error.append(( pi_ext - np.pi))  # appended the error (error = difference between the estimated pi and pi)
                        st_dev.append(np.std(self.pi_results[:i])) # standard deviation for the estimated pi until the index 'i'
                
                self.error = np.array(error)          # error list is converted to numpy array
                self.st_dev = np.array(st_dev)        # st_dev list is converted to numpy array

                # calls a function to generate a histogram with the calculated pi values\
                # from the histrogram window there will be access to othe charts related windows
                self.create_histogram(pi, pi_st_dev, self.pi_results, self.dots)
        
            # enable the Monte Carlo launch button
            self.b_pi['state'] = 'normal'             # b_p (button for pi calculation) is enabled
            self.b_pi['relief'] = 'raised'            # b_p (button for pi calculation) is raised
            self.b_pi.update()                        # b_p (button for pi calculation) is updated
            self.mainWindow.update()                  # mainWindow gets a forced update, to ensure b_p is updated
        
        # this function has a return (not sure it is really needed)
        return pi, pi_error, self.pi_results 
    
    
    
    
    
    
    def create_histogram(self, pi, pi_st_dev, pi_results, dots):
        """Function to create a tkinter window and plot a histogram.
        Buttons are added to call other charts or to close this window."""
        
        # Create a new Tkinter window for the histogram
        self.histogram_window = tk.Toplevel(self.mainWindow)  # histogram_window is created
        
        w = int(0.85 * self.ws)                       # 85% of the screen width is assigned to w
        h = int(0.85 * self.hs)                       # 85% of the screen height is assigned to h
        
        self.histogram_window.geometry(f"{w}x{h}+10+40")  # Set the size and position of the Tkinter window
        self.histogram_window.title('Histogram')      # title for the new tkinter window
        
        canvas1 = tk.Canvas(self.histogram_window, width=w, height=60)
        canvas1.pack(side = tk.TOP)
        
        canvas2 = tk.Canvas(self.histogram_window)
        canvas2.pack(side = tk.BOTTOM, fill=tk.BOTH, expand=1)
        
        # Add a button to open the error window
        btn_open_error = tk.Button(canvas1, text="Plot pi error", command= self.plot_error)
        btn_open_error.place(relx=0, rely=0, anchor="nw", x=10, y=10)  # Placing the btn_open_error button on the top left
        
        # Add a button to open the standard deviation window
        btn_open_stdev = tk.Button(canvas1, text="Plot standard deviation", command= self.plot_st_dev)
        btn_open_stdev.place(relx=0.45, rely=0, anchor="nw", x=0, y=10)  # Placing the btn_open_stdev button on the middle
        
        # Add a close button to the histogram window
        btn_close = tk.Button(canvas1, text="Close", command=self.histogram_window.destroy)
        btn_close.place(relx=1, rely=0, anchor="ne", x=-10, y=10)  # Placing the close button on the top right
        
        
        # number of Monte Carlo repeations
        runs = len(pi_results)                        # number of runs
        runs = '{:,.0f}'.format(runs)                 # runs is formated to text with thousands separation
        dots = '{:,.0f}'.format(dots)                 # dots is formated to text with thousands separation
        
        # clear the previous chart
        plt.clf()                                     # previous matplotlib plot is cleared
        
        # Create the histogram (scott algorithm for the bins quantity)
        plt.hist(pi_results, bins='scott', color='skyblue', edgecolor='black') 

        # Set chart title (on two rows) and axes labels
        title =  f'pi approximation:  avg = {str(pi)[:9]}, st.dev = {str(pi_st_dev)[:9]}\n'
        title += f'( {runs} runs of {dots} dots each )'  # chart title
        plt.title(title, fontsize = 12)               # title is plot to the chart with fontsize assigned
        plt.xlabel('pi approximated values')          # x axis label is assigned
        plt.ylabel('Frequency')                       # y axis label is assigned

        # Display the histogram
        plt.tight_layout()                            # chart is plotted, with compact layout

        # Embed the histogram into the Tkinter window
        canvas = FigureCanvasTkAgg(plt.gcf(), master=canvas2)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # saves the error chart
        folder = pathlib.Path().resolve()             # active folder 
        folder = os.path.join(folder,'charts')        # folder to store the chart images
        if not os.path.exists(folder):                # if case the folder does not exist
            os.makedirs(folder)                       # folder is made if it doesn't exist
        
        fname = self.datetime + '_histogram.png'      # file name for the histogram
        fname = os.path.join(folder,fname)            # folder and file name for the settings
        try:                                          # tentative
            plt.savefig(fname)                        # Save the current chart as an image file     
        except:                                       # in case of exception
            print("Could not save the error chart:", fname) # print a feedback to the terminal
    
    
    
    
    
    
    def plot_error(self):
        """Function to create a tkinter window and plot a line chart.
        Button is added to close this window."""
        
        # Create a new Tkinter window for the error chart
        self.error_window = tk.Toplevel(self.mainWindow) # error_window is created
        
        w = int(0.85 * self.ws)                       # 85% of the screen width is assigned to w
        h = int(0.85 * self.hs)                       # 85% of the screen height is assigned to h
        
        self.error_window.geometry(f"{w}x{h}+10+40")  # Set the size and position of the Tkinter window
        self.error_window.title('pi approximation error')  # title for the new tkinter window
            
        # clear the previous chart
        plt.clf()                                     # previous matplotlib plot is cleared
        
        # Create the chart
        plt.plot(self.x, self.error, color='k', linewidth=1)
        
        # Set chart title (in two rows) and axes labels
        dots = '{:,.0f}'.format(len(self.error))      # dots value, and convertedt to text with thousands separator
        final_error = format(self.error[-1], '.8f')   # latest error datapoint, and converted to text with thousands separator
        title =  f'pi approximation error = {final_error[:10]}\n'   # chart title
        title += f'( {len(self.error)} runs of {dots} dots each )'
        plt.title(title, fontsize = 12)               # title is plot to the chart with fontsize assigned
        plt.xlabel('runs')                            # x axis label is assigned
        plt.ylabel('error')                           # y axis label is assigned
        plt.grid(linewidth=1)                         # chart grid is added
        
        # fill the areas underneat the result
        plt.fill_between(self.x, self.error, where=(self.error >= 0), color='lightsalmon')  # fill the positive side in light red
        plt.fill_between(self.x, self.error, where=(self.error <= 0), color='lightblue')  # fill the negative side in light blue

        # Display the histogram
        plt.tight_layout()                            # chart is plotted, with compact layout

        # Embed the histogram into the Tkinter window
        canvas = FigureCanvasTkAgg(plt.gcf(), master=self.error_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Add a close button to the error window
        btn_close = tk.Button(self.error_window, text="Close", command=self.error_window.destroy)
        btn_close.place(relx=1, rely=0, anchor="ne", x=-10, y=10)  # Placing the close button on the top right
        
        # saves the error chart
        folder = pathlib.Path().resolve()             # active folder 
        folder = os.path.join(folder,'charts')        # folder to store the chart images
        if not os.path.exists(folder):                # if case the folder does not exist
            os.makedirs(folder)                       # folder is made if it doesn't exist
        
        fname = self.datetime + '_error.png'          # file name for the error chart
        fname = os.path.join(folder,fname)            # folder and file name for the settings
        try:                                          # tentative
            plt.savefig(fname)                        # Save the current chart as an image file     
        except:                                       # in case of exception
            print("Could not save the error chart:", fname) # print a feedback to the terminal
    
    
    
    
    
    
    def plot_st_dev(self):
        """Function to create a tkinter window and plot a line chart.
        Button is added to close this window."""
        
        # Create a new Tkinter window for the standard deviation chart
        self.st_dev_window = tk.Toplevel(self.mainWindow)  # st_dev_window is created
        
        w = int(0.85 * self.ws)                       # 85% of the screen width is assigned to w
        h = int(0.85 * self.hs)                       # 85% of the screen height is assigned to h      
        
        self.st_dev_window.geometry(f"{w}x{h}+10+40") # Set the size and position of the Tkinter window
        self.st_dev_window.title('pi approximation st.dev')  # title for the new tkinter window
        
        
        # clear the previous chart
        plt.clf()                                     # previous matplotlib plot is cleared
        
        # Create the chart
        plt.plot(self.x, self.st_dev, color='k', linewidth=1)
        
        # Set chart title (in two rows) and axes labels
        dots = '{:,.0f}'.format(len(self.st_dev))     # dots value, and convertedt to text with thousands separator
        final_st_dev = format(self.st_dev[-1], '.8f') # latest st.dev value, and converted to text with thousands separator
        title =  f'pi approximation st.dev = {final_st_dev[:10]}\n' # chart title
        title += f'( {len(self.st_dev)} runs of {dots} dots each )' # chart title
        plt.title(title, fontsize = 12)               # title is plot to the chart with fontsize assigned
        plt.xlabel('runs')                            # x axis label is assigned
        plt.ylabel('standard deviation')              # y axis label is assigned
        plt.grid(linewidth=1)                         # chart grid is added

        # Display the histogram
        plt.tight_layout()                            # chart is plotted, with compact layout

        # Embed the histogram into the Tkinter window
        canvas = FigureCanvasTkAgg(plt.gcf(), master=self.st_dev_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Add a close button to the st_dev_window window
        btn_close = tk.Button(self.st_dev_window, text="Close", command= self.st_dev_window.destroy)
        btn_close.place(relx=1, rely=0, anchor="ne", x=-10, y=10)  # Placing the close button on the top right

        # saves the standard deviation chart
        folder = pathlib.Path().resolve()             # active folder 
        folder = os.path.join(folder,'charts')        # folder to store the chart images
        if not os.path.exists(folder):                # if case the folder does not exist
            os.makedirs(folder)                       # folder is made if it doesn't exist
        fname = self.datetime + '_st_dev.png'         # file name for the st_dev chart
        fname = os.path.join(folder,fname)            # folder and file name for the settings
        try:                                          # tentative
            plt.savefig(fname)                        # Save the current chart as an image file     
        except:                                       # in case of exception
            print("Could not save the st_dev chart:", fname) # print a feedback to the terminal
    
    
    
    
    
    
    def on_closing(self):
        print("\nClosing the GUI application\n\n")    # feedback is printed to the terminal
        
        global tk_running                             # tk_running global is used
        tk_running = False                            # tk_running is set False
        
        cv2.destroyAllWindows()                       # all openCV windows are closed
        self.mainWindow.destroy()                     # frame mainWindow is destroyed
        time.sleep(0.5)                               # little delay
        self.destroy()                                # main window is destroyed

# #################################################################################







if __name__ == "__main__":
    
    tk_running = True                # set a global variable to monitor the tkinter class being runnin
    
    settings = Settings()            # class Settings is activated, and assigned to settings
    queue_manager = Queue_manager()  # class Queue_manager is activated, and assigned to queue_manager
    
    montecarlo = MonteCarlo()        # class MonteCarlo is activated, and assigned to montecarlo
    montecarlo.start()               # runs the montecarlo class in a separate thread
    
    gui = GUI()                      # class GUI is activated, and assigned to gui
    gui.protocol("WM_DELETE_WINDOW", gui.on_closing)    # closing the GUI
    
    gui.mainloop()                   # gui is started

