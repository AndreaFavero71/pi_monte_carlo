#!/usr/bin/env bash

set -e

print_header () {
  echo
  echo $1
  echo
}

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo $0)"
  exit
fi

print_header "Deactivating graphical login"
systemctl --quiet set-default multi-user.target

print_header "Updating packages"
apt update
apt -y -qq upgrade

print_header "Installing required packages"
apt-get -y install libopencv-dev
apt-get -y install python3-opencv
apt-get -y install python3-matplotlib

print_header "Creating python virtual env"
python3 -m venv .virtualenvs --system-site-packages
source .virtualenvs/bin/activate

set +e

print_header "Configuring vnc server"
if ! crontab -l 2>/dev/null | grep -q "start.sh"; then
	(crontab -l 2>/dev/null;\
        echo -e 'MAILTO=""';\
        echo -e '@reboot su - pi -c "/usr/bin/vncserver-virtual :1 -randr=1280x720"')\
	| crontab -
fi

print_header "Giving execuatble rights to file start.sh"
chmod +x /home/pi/pi_monte_carlo/pi_monte_carlo/start.sh

print_header "Copying file start.desktop to Desktop"
cp /home/pi/pi_monte_carlo/pi_monte_carlo/setup/pi_start.desktop /home/pi/Desktop

print_header "Reboot now? (y lowercase to confirm)"
read x && [[ "$x" == "y" ]] && /sbin/reboot;

