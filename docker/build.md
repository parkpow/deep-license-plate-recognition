

## 1. Get a Windows  env
Building the EXE for windows must be done in Windows ENV.
> The following steps were done on a 64bit **Windows 10 Home Insider Preview** Build 21343.rs_prerelease.210320-1757

## 2. Install Python 3.7.5

The customized version of PyInstaller is incompatible with python3.8 so you need to install Python 3.7.5 donwloadable from this link:
https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe


## 3. Install Customized PyInstaller
Download the custom PyInstaller from Google Drive:
https://drive.google.com/file/d/1lUhvvKAZ7DgMhcWPGFHB4dRH8__LZfjX/view?usp=sharing

1. Re-build bootloader
    Install required Build Tools, Install Microsoft Visual Studio Build tools, donwloadable from this link:
    https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2017

    > Note: The download option is at the bottom in dropdown. You don't have to install the full IDE

    To build Bootloader, chdir into the bootloader folder and run this command:
    `python ./waf all --target-arch=64bit`

2. Install Custom PyInstaller
    Chdir into the main folder and run this command:
    `python ./setup.py install`


## 4. Setup Installer Script
Clone or Download https://github.com/parkpow/deep-license-plate-recognition
Install Dependancies system wide by changing dir into the **docker** folder running this command:
`python manage.py install -r requirements.txt`


## 5. Update paths in installer spec
The installed Dependancies and other assests will need to be included in the EXE by PyIsntaller.
This is done by pointing PyInstaller to the correct location of the dependencies.

Updating these 2 paths in `docker/platerec_installer.spec`
1. site_packages - Path to where python installed the packages when you ran `pip install`
2. pathex - Path to the location of the installer script


Here is an example diff of making the changes:
```
diff --git a/docker/platerec_installer.spec b/docker/platerec_installer.spec
index 7296aff..c5c9371 100644
--- a/docker/platerec_installer.spec
+++ b/docker/platerec_installer.spec
@@ -10,8 +10,8 @@ import sys
 block_cipher = None

 if sys.platform == 'win32':
-    site_packages = 'C:/Python37/Lib/site-packages/'
-    pathex = ['Z:\\src']
+    site_packages = 'C:/Users/hp/AppData/Local/Programs/Python/Python37/Lib/site-packages/'
+    pathex = ['C:\\Users\hp\OneDrive\Desktop\deep-license-plate-recognition\docker']
 else:
     site_packages = '/root/.pyenv/versions/3.7.5/lib/python3.7/site-packages/'
     pathex = ['/src']
```

## 6. Build Single file EXE
Chdir into the `docker` folder and run this command:
`pyinstaller --onefile platerec_installer.py`

This will generate the EXE in the following path **deep-license-plate-recognition\docker\dist**

## 7. Sign the EXE with CA certificate
The signtool is installed when you install the Build tools.

Assumming the following enviroment:
- The CA Certificate is located in this path: "C:\Users\hp\Downloads\PRPP-Cert-022621.pfx"
- The CA Certificate password is: Uxz#######
- The Output EXE from the previous step is located in this path: "C:\Users\hp\Downloads\PlateRecognizer-Installer.exe"

Run this command to sign the EXE:
```
C:\Program Files (x86)\Windows Kits\10\App Certification Kit>signtool.exe sign /debug /f "C:\Users\hp\Downloads\PRPP-Cert-022621.pfx" /p Uxz####### "C:\Users\hp\Downloads\PlateRecognizer-Installer.exe"
```
