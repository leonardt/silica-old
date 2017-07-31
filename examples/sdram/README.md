# Setup
## macOS
Tested on Macbook Pro (13-inch, 2017, Four Thunderbolt 3 Ports) with macOS Sierra (10.12.6)

### Dependencies  
```
brew install libftdi
brew cask install java
```

#### Managing FTDI Drivers
The built-in, Apple FTDI driver conflicts with the libftdi installed via Homebrew. Before using the Papilio Loader, you'll need to execute this command to unload it
```
sudo kextunload -b com.apple.driver.AppleUSBFTDI
```

When you're done you can reload the driver using
```
sudo kextload -b com.apple.driver.AppleUSBFTDI
```

If you don't unload the driver, you might see this message
```
Could not access USB device 0403:6010. If this is linux then use sudo.
```

### Verifying your Setup
1. Download and install the Papilio Loader GUI from [this link](http://forum.gadgetfactory.net/index.php?/files/file/10-papilio-loader-gui/) (choose the Mac.zip)
2. Download the Papilio Quickstart Sketch bit file for the Papilio Pro LX9 from [this link](http://papilio.cc/sketches/Quickstart-Papilio_Pro_LX9-v1.5.bit).
3. Run the Loader GUI (**NOTE**: Make sure you've unloaded the Apple FTDI driver as noted above).
4. In the `Target .bit file` field, select the `Quickstart-Papilio_Pro_LX9-v1.5.bit` file you just downloaded.
5. Click `Run`

You should see an output that looks like
```
Using devlist.txt
JTAG chainpos: 0 Device IDCODE = 0x24001093	Desc: XC6SLX9
Created from NCD file: top_avr_core_v8.ncd;UserID=0xFFFFFFFF
Target device: 6slx9tqg144
Created: 2012/02/13 17:18:57
Bitstream length: 2724832 bits

Uploading "/path/to/Downloads/Quickstart-Papilio_Pro_LX9-v1.5.bit". DNA is 0x19f0e1789e0753ff
Done.
Programming time 600.4 ms
USB transactions: Write 177 read 9 retries 5
```

More information about the QuickStart file can be found [here](http://papilio.cc/index.php?n=Papilio.P1QuickstartSketch).
It sends the ASCII table at 9600 8N1 over the serial port in a continuous loop, so we will monitor the port to verify that the bit file was loaded properly.

First, we must reload the Apple FTDI driver:
```
sudo kextload -b com.apple.driver.AppleUSBFTDI
```

Next, we need to find the USB device name of the Papilio Pro:
```
ls /dev | grep tty.usb
```

On my system this returns:
```
tty.usbserial-1431A
tty.usbserial-1431B
```

Unfortunately at this point, I have not found a way to determine which device corresponds to the board besides guess and check.

To monitor a port at the correct rate, use the command (swap out `/dev/tty.usbserial-1431B` to find the right port)
```
screen /dev/tty.usbserial-1431B 9600
```

If everything has gone correctly, one of the ports should be printing out messages like:
```
...
[, dec: 91, hex: 5B, oct: 133, bin: 1011011
\, dec: 92, hex: 5C, oct: 134, bin: 1011100
], dec: 93, hex: 5D, oct: 135, bin: 1011101
^, dec: 94, hex: 5E, oct: 136, bin: 1011110
_, dec: 95, hex: 5F, oct: 137, bin: 1011111
`, dec: 96, hex: 60, oct: 140, bin: 1100000
a, dec: 97, hex: 61, oct: 141, bin: 1100001
b, dec: 98, hex: 62, oct: 142, bin: 1100010
c, dec: 99, hex: 63, oct: 143, bin: 1100011
d, dec: 100, hex: 64, oct: 144, bin: 1100100
e, dec: 101, hex: 65, oct: 145, bin: 1100101
f, dec: 102, hex: 66, oct: 146, bin: 1100110
g, dec: 103, hex: 67, oct: 147, bin: 1100111
h, dec: 104, hex: 68, oct: 150, bin: 1101000
i, dec: 105, hex: 69, oct: 151, bin: 1101001
j, dec: 106, hex: 6A, oct: 152, bin: 1101010
k, dec: 107, hex: 6B, oct: 153, bin: 1101011
l, dec: 108, hex: 6C, oct: 154, bin: 1101100
m, dec: 109, hex: 6D, oct: 155, bin: 1101101
n, dec: 110, hex: 6E, oct: 156, bin: 1101110
o, dec: 111, hex: 6F, oct: 157, bin: 1101111
p, dec: 112, hex: 70, oct: 160, bin: 1110000
q, dec: 113, hex: 71, oct: 161, bin: 1110001
r, dec: 114, hex: 72, oct: 162, bin: 1110010
s, dec: 115, hex: 73, oct: 163, bin: 1110011
t, dec: 116, hex: 74, oct: 164, bin: 1110100
u, dec: 117, hex: 75, oct: 165, bin: 1110101
...
```
