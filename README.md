srsRAN
======

[![Build Status](https://github.com/srsran/srsRAN_4G/actions/workflows/ccpp.yml/badge.svg?branch=master)](https://github.com/srsran/srsRAN_4G/actions/workflows/ccpp.yml)
[![CodeQL](https://github.com/srsran/srsRAN_4G/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/srsran/srsRAN_4G/actions/workflows/codeql.yml)
[![Coverity](https://scan.coverity.com/projects/28268/badge.svg)](https://scan.coverity.com/projects/srsran_4g_agpl)

srsRAN is an open source 4G software radio suite developed by [SRS](http://www.srs.io). For 5G RAN, see our new O-RAN CU/DU solution - [srsRAN Project](https://www.github.com/srsran/srsran_project).

See the [srsRAN 4G project pages](https://www.srsran.com) for information, guides and project news.

The srsRAN suite includes:
  * srsUE - a full-stack SDR 4G UE application with prototype 5G features
  * srsENB - a full-stack SDR 4G eNodeB application
  * srsEPC - a light-weight 4G core network implementation with MME, HSS and S/P-GW

For application features, build instructions and user guides see the [srsRAN 4G documentation](https://docs.srsran.com/projects/4g/).

For license details, see LICENSE file.

Support
=======

Mailing list: https://lists.srsran.com/mailman/listinfo/srsran-users

Update for srsUE with APDU proxy
======

## Step0: Equipment requirements

Get a computer with Ubuntu 18 installed, and a USRP B210

## Step1: Install UHD

**1. Update dependencies:**

```
sudo apt update
sudo apt upgrade
```

**2. Install sim card dependencies:**

```
sudo apt-get install pcscd pcsc-tools libccid libpcsclite-dev python-pyscard
```

**3. Install python `requests` module:**

```
sudo apt install python-pip
sudo pip install requests
```

**4. Install UHD:**

Open a new terminal at path home/

```
sudo apt-get install libboost-all-dev libusb-1.0-0-dev python-cheetah doxygen python-docutils g++ cmake python-setuptools python-mako
git clone https://github.com/EttusResearch/uhd
cd uhd
git checkout release_003_009_007 //We use 3.9.7 TLS version
git checkout UHD-3.9.LTS //For ubuntu 20.04, we need to select this branch.
cd host
mkdir build
cd build
cmake ../
make -j8
make test
sudo make install
sudo ldconfig
sudo uhd_images_downloader
```

**5. Test UHD Installation:**

Connect the USRP to the computer first

```
sudo uhd_find_devices
```

![](https://hackmd.io/_uploads/S13hY3UGp.png)

## Step2: Install srsRAN_4G

**1. Install some libs**

```
sudo apt-get install cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev
```

**2. Set srsLTE folder**

Clone this repo with branch `modem-support` and copy the whole folder under ~/uhd/host/build

You can rename the folder, below, I'll use `srsRAN_4G`

**3. Install srsLTE**

Open a new terminal at path ~/uhd/host/build/srsRAN_4G

```
mkdir build
cd build
cmake ../
make -j8
make test
sudo make install
```

* Note that make test will failed with one file (nas_test), just ignore it

## Step3: Run srsRAN_4G

**1. Copy ue.conf file**

Go to ~/uhd/host/build/srsRAN_4G/srsue you can see that there is a file name "ue.conf.example", copy it and paste it into ~/uhd/host/build/srsRAN_4G/build/srsue/src and chage filename into "ue.conf"

**2. Set ue.conf file**

Open the ue.conf file :

2-1 Set EARFCN value as below, the EARFCN value can be get from experiment1 
```
[rf]
dl_earfcn = EARFCN_value
```

2-2 Set pcap as below
```
[pcap]
enable = true
mac_filename = /home/your_username/ue_mac.pcap
mac_nr_filename = /home/your_username/ue_mac_nr.pcap
nas_filename = /home/your_username/ue_nas.pcap
```
2-3 Set IMSI and force_imsi_attach
* How to get your IMSI? Please check for note below.
```
[usim]
imsi = <your_imsi>

[nas]
force_imsi_attach = true
```
2-4 Set time_adv_nsamples
Set this value when you encounter "Scheduling Request Failed"
```
[rf]
time_adv_nsamples = 115
```
* Start with a low enough value, e.g. 115 samples, and then increase it by steps of five.

**3. Execute proxy**

The target python file(my_apdu.py) is under this repo, you can paste it to where you want to execute.

Execute the file with a phone connected to your computer.

* This file is for eSIM, for physical SIM, please check note below.

```
sudo python3 my_apdu.py
```

**4. Execute ue.conf file**

Open a new terminal at path ~/uhd/host/build/srsRAN_4G/build/srsue/src

```
cd ~/uhd/host/build/srsRAN_4G/build/srsue/src
sudo ./srsue ue.conf
```

The successful attachment should be shown as follows, “network attach successful”

![](https://hackmd.io/_uploads/ByETYnUGp.png)

# Note

## 1. How to get your IMSI?

**eSIM**
```
# Step 1: Select MF (3F00)
echo -e 'AT+CSIM=14,"00A40004023F00"\r' > /dev/umts_router && cat /dev/umts_router

# Step 2: Select ADF USIM(A0000000871002)
echo -e 'AT+CSIM=24,"00A4040007A0000000871002"\r' > /dev/umts_router && cat /dev/umts_router

# Step 3: Select EF_IMSI (6F07)
echo -e 'AT+CSIM=14,"00A40004026F07"\r' > /dev/umts_router && cat /dev/umts_router

# Step 4: Read 9 bytes IMSI
echo -e 'AT+CSIM=10,"00B0000009"\r' > /dev/umts_router && cat /dev/umts_router
```

**Physical SIM**
```
# Step 1: Select MF (3F00)
echo -e 'AT+CSIM=14,"00A40004023F00"\r' > /dev/umts_router && cat /dev/umts_router

# Step 2: Select DF_GSM (7F20)
echo -e 'AT+CSIM=14,"00A40004027F20"\r' > /dev/umts_router && cat /dev/umts_router

# Step 3: Select EF_IMSI (6F07)
echo -e 'AT+CSIM=14,"00A40004026F07"\r' > /dev/umts_router && cat /dev/umts_router

# Step 4: Read 9 bytes IMSI
echo -e 'AT+CSIM=10,"00B0000009"\r' > /dev/umts_router && cat /dev/umts_router
```
And you will get IMSI in BCD order

For example:

0849662914306484869000

→ 08 (length) + 4966291430648486 (data) + 9000 (success status)

→ 08 + 9 + **466011902511289(real IMSI)** + 9000

## 2. Proxy file for physical SIM

For physical SIM, you need to modify function `send_apdu` in my_apdu.py

1. Select #1 SIM card for physical SIM
```
# physical SIM: AT+CSUS=1, eSIM: AT+CSUS=2
self.send_raw("echo -e 'AT+CSUS=2\\r' > /dev/umts_router")
```

2. SELECT ADF USIM
```
self.send_raw("echo -e 'AT+CSIM=21,\"00A4040410<your_adf_usim_aid>\"\\r' > /dev/umts_router")
```

* How to get your ADF USIM AID?

```
adb shell
su
echo -e 'AT+CSIM=7, "00A40004022F00"\r' > /dev/umts_router && cat /dev/umts_router
echo -e 'AT+CSIM=5, "00B2010400"\r' > /dev/umts_router && cat /dev/umts_router
```
And find 32 chars start with `A000000087`

For example: A0000000871002FF33FF0189060500FF
