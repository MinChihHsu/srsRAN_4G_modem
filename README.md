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
2-3 Set imsi and force_imsi_attach
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

