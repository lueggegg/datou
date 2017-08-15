echo WARNING: this script will delete ALL Hillstone virtual adapters (use the device manager to delete adapters one at a time)
pause
"C:\Program Files (x86)\Hillstone\Hillstone Secure Connect\bin\SSLChannel.exe" -d
"C:\Program Files (x86)\Hillstone\Hillstone Secure Connect\driver\tapinstall.exe" remove hssvc
pause
