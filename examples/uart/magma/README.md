**MacOS NOTE:** Use `pip3` if you installed Python 3 with Homebrew.
```
pip install pyserial  # To read uart messages on the host
make upload_mac
sudo python3 monitor.py /dev/tty.usbserial-1451B  # Change /dev/tty.usbserial-1451B to the port that you're icestick is plugged in.
```

To find your icestick's serial port
```
ls /dev/tty.* | grep usb  # Lists all the available serial ports
```
