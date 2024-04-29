# pi_monte_carlo


Approximates π via Monte Carlo method.

This repo contains the relevant files to make a standalone device that approximates pi, with a graphical animation.

![title image](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/pi_monte_carlo/images/title.jpg)
![title image](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/images/pi_monte_carlo.gif)

Further robot info at: (https://www.instructables.com/Pi-Approximation-With-Raspberry-Pi-Monte-Carlo-Met/)

An impression of the device: (https://youtu.be/K6qTwk_mXm4)
<br /><br />

# What is needed:
1. Raspberry Pi 4b.
2. microSD.
3. 7 inches touchscreen (my choice, as reference: https://www.amazon.nl/Capacitive-1024x600-Display-Monitor-Raspberry/dp/B07YJDSCKR?source=ps-sl-shoppingads-lpcontext&ref_=fplfs&psc=1&smid=A5BN6RQOA0WX3).
4. Power supply (the original Raspberry Pi power supply 15W).
5. 3D print the box [stl file here](pi_monte_carlo/stl_files).
6. A couple of 90deg HDMI adaptors.
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
11. If not done yet, apply the setting required by the purchased touchscreen.
12. The device is now up and running 🙂.

    
If you prefer a manual installation, you can follow the steps listed at ([setup/Installation_steps.txt](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/install/Installation_steps.txt)) <br /><br />

Note:
To setup the touchscreen indicated above:
1. sudo rm -rf LCD-show
2. git clone https://github.com/goodtft/LCD-show.git
3. chmod -R 755 LCD-show
4. cd LCD-show/
5. sudo ./LCD7C-show <br />

The last command quickly plots a couple of commands and the board reboots. <br />
The device has now a nice touchscreen 🙂 
