# pi_monte_carlo

(this repo is still work in progress :-) )

Approximates pi via Monte Carlo method

This repo contains the relevant files to make a standalone device that approximates pi, with a graphical animation
![title image](https://github.com/AndreaFavero71/pi_monte_carlo/blob/main/pi_monte_carlo/images/title.jpg)

Further robot info at: https://www.instructables.com/member/AndreaFavero/

An impression of the device: https://youtu.be/TkHhk7qaoyI


# What is needed:
1. Raspberry Pi 4b
2. microSD
3. 7 inches touchscreen
4. Power supply (the original Raspberry Pi power supply 15W)
5. 3D print the box [stl file here](pi_monte_carlo/stl_files)



# How to setup the Rspberry Pi:
1. Flash your SD card with Raspberry Pi OS (64-bit) Bookworm
2. Put the sd card in the pi and power it. You can monitor the boot process if you connect an hdmi monitor to it but it is not essential. 
3. Try to connect to the Raspberry Pi via SSH.
5. After you are connected via ssh, type the following commands in the shell:

```
git clone https://github.com/AndreaFavero71/pi_monte_carlo.git
```

An automatic installation will follow, for now please refer to [document here](setup/Installation_steps.txt)
