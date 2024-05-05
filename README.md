# pi_monte_carlo


Approximates π via Monte Carlo method, by using a Raspberry Pi.

This repo contains the relevant files to make a standalone device that approximates pi, with a graphical animation.

![title image](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/images/title1.jpg)

![title image](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/images/pi_monte_carlo.gif)

More info at: (https://www.instructables.com/Pi-Approximation-With-Raspberry-Pi-Monte-Carlo-Met/)

An impression of the device: (https://youtu.be/K6qTwk_mXm4)
<br /><br />


# Intro:
We all know pi as the mathematical constant, defined as "the ratio of a circle's circumference to its diameter" (~ 3.14159).<br />
Perhaps not everybody is aware that 'pi' can be approximated using a Raspberry Pi, employing a statistical method and an interesting graphical animation.<br />
Here, I propose a device that combines educational elements with graphical animation. While not the most efficient method for calculating pi, it serves as a valuable tool for comprehending the Monte Carlo method.<br />
This device essentially consists of a Raspberry Pi 4b with a 7-inch touchscreen display enclosed in a 3D-printed box. Python is used for the code.
<br /><br />

# What is needed:
1. Raspberry Pi 4b.
2. microSD.
3. 7 inches touchscreen (my choice, as reference: https://www.amazon.nl/Capacitive-1024x600-Display-Monitor-Raspberry/dp/B07YJDSCKR?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=A5BN6RQOA0WX3).
4. Power supply (the original Raspberry Pi power supply 15W).
5. 3D print the box via the [stl files](pi_monte_carlo/stl_files) (or use the [step files](https://github.com/AndreaFavero71/pi_monte_carlo/tree/main/step_files) for eventual changes).
6. A couple of 90deg HDMI adaptors.
7. Panel Mount Type-C USB-C Male To Female Extension Cable 0.2m ([as reference](https://www.aliexpress.com/item/1005003311183241.html?spm=a2g0o.productlist.main.1.4ad3c8WTc8WTma&algo_pvid=a3dedfe1-ca87-49fd-a086-d380b37663f2&algo_exp_id=a3dedfe1-ca87-49fd-a086-d380b37663f2-0&pdp_npi=4%40dis%21EUR%212.87%212.87%21%21%213.01%213.01%21%40211b600d17148410018833133ea3cf%2112000026774425260%21sea%21NL%21768246036%21&curPageLogUid=XzzZhWgdyiyb&utparam-url=scene%3Asearch%7Cquery_from%3A)). This allows battery operation and easy detachment of the power supply cable 
<br /><br />


# How to setup the Rspberry Pi:
1. Flash your SD card with Raspberry Pi OS (64-bit) Bookworm
2. Put the sd card in the pi and power it. You can monitor the boot process via the hdmi monitor but it is not essential. 
3. Try to connect to the Raspberry Pi via SSH.
5. After you are connected via ssh, type the following commands in the shell:

```
git clone https://github.com/AndreaFavero71/pi_monte_carlo.git
cd pi_monte_carlo
chmod +x install/setup.sh
sudo ./install/setup.sh
```

6. Make sure the script runs without error until the end. It should ask you to reboot. Type 'y' and hit enter.
7. If the question "Reboot (y/n)" does't appear, them the installation is facing issues; Try to fix the errors, and run the script again.
8. If the question "Reboot (y/n) does appear, You should get the proper environment after the reboot.
9. After the reboot, you can connect to the Raspberry Pi via VNC, or directly via the touchscreen: Double-click the pi icon on the Desktop to start the app.
10. You'll be asked to confirm the intention to run an executable. To remove this request: File Manager, Edit, Preferences, General (tab), Check the "Don't ask option on launch executable file" option.
11. If not done yet, apply the setting required for the purchased touchscreen. In my case:

```
sudo rm -rf LCD-show
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./LCD7C-show
```
The last command quickly plots a couple of commands and the board reboots). <br />
The device is now up and running 🙂.


If you prefer a manual installation, you can follow the steps listed at ([setup/Installation_steps.txt](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/install/Installation_steps.txt)) <br /><br />


# How the GUI work:
Main elements of the Graphical User Interface (GUI) are:
1. This device can be operated via the touchscreen (no keyboard or mouse are required, nor a connection with a PC).
2. On the GUI there are some sliders to set the number of repetitions (RUNS) and the number of observations (DOTS). The RUNS range from 1 unit to 900 thousand, while the DOTS range from 1'000 to 9 millions.
3. The number of observations (DOTS) will be generated for each run of the total RUNS.
4. Both the RUNS and the DOTS are defined by Scientific notations, to make possible a large variation range in a simple way.
5. The SAVE SETTINGS button saves the current settings for future use. (Settings are saved on a JSON file).
6. The INFO button opens a scrollable set of slides summarizing the method used. (See images in the next step).
7. There are three levels of animations, ranging from 'max' to 'min'. This decreases entertainment and increases speed.
8. The pi button begins the calculation.
9. A progress bar is active when multiple RUNS.
10. Estimated time remaining is plot when multiple RUNS.


After completing all the runs:

1) if at least 50 runs were made, the GUI displays a histogram with a short summary of data in the chart title) The histogram window includes buttons to access two additional charts:
    - Error plot versus runs.
    - Standard deviation plot versus runs.

2) some files are saved locally:
    - A text file log.tx with the estimate pi values (one per each run of the RUNS). Limited to first 50k datapoints in caase there are more.
    - The image of the histogram.
    - The image with the chart of the error vs versus runs (this chart will be saved upon accessing its window).
    - The image with the chart of the standard deviation versus runs (this chart will also be saved upon accessing its window).
    - The aforementioned files are also saved in case the process is interrupted before completion, provided that at least 50 RUNS have been completed.


# Short explanation of the method:
A short explanation of the method is provided, via 9 slides: https://github.com/AndreaFavero71/pi_monte_carlo/tree/main/info
<br /><br />

# More info:
For more info check: (https://www.instructables.com/Pi-Approximation-With-Raspberry-Pi-Monte-Carlo-Met/)
<br /><br />
