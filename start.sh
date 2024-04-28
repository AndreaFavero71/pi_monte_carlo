#!/usr/bin/env bash

#######   Andrea Favero,  28 April 2024  #####################################################
#
#  This bash script activates the venv, and starts the pi approximation via Monte carlo method
#
##############################################################################################

# activate the venv
source ~/pi_monte_carlo/.virtualenvs/bin/activate

# enter the folder with the main scripts
cd ~/pi_monte_carlo

# runs the robot main script
python pi.py