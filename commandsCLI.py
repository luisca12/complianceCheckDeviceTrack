from netmiko import ConnectHandler
from log import authLog

import traceback
import csv
import os
import re

shHostname = "show run | i hostname"
shIntStatus = "show interface status"
shRunDevice = "show run | sec device-sensor"

shVlanID20 = "show vlan id 20"

deviceTrackingConf = [
    'device-sensor filter-list lldp list lldp-list',
    'tlv name system-name',
    'tlv name system-description',
    'device-sensor filter-list dhcp list dhcp-list',
    'option name host-name',
    'option name domain-name',
    'option name requested-address',
    'option name parameter-request-list',
    'option name class-identifier',
    'option name client-identifier',
    'device-sensor filter-list cdp list cdp-list',
    'tlv name device-name',
    'tlv name address-type',
    'tlv name capabilities-type',
    'tlv name platform-type',
    'tlv name native-vlan-type',
    'tlv number 34',
    'device-sensor filter-spec dhcp include list dhcp-list',
    'device-sensor filter-spec lldp include list lldp-list',
    'device-sensor filter-spec cdp include list cdp-list',
    'device-sensor accounting',
    'device-sensor notify all-changes'
]

# Regex Patterns
intPatt = r'[a-zA-Z]+\d+\/(?:\d+\/)*\d+'
shIntDevTrack = re.compile(r'(device-tracking attach-policy DEVTRK)|(device-tracking attach-policy IPDT_POLICY)')

def complCheck(validIPs, username, netDevice):
    # This function is to check for compliance

    for validDeviceIP in validIPs:
        missingConfig1 = False
        deviceConfigured = False
        configInDevice = []
        missingConfig = []
        try:
            validDeviceIP = validDeviceIP.strip()
            currentNetDevice = {
                'device_type': 'cisco_xe',
                'ip': validDeviceIP,
                'username': username,
                'password': netDevice['password'],
                'secret': netDevice['secret'],
                'global_delay_factor': 2.0,
                'timeout': 120,
                'session_log': 'netmikoLog.txt',
                'verbose': True,
                'session_log_file_mode': 'append'
            }

            print(f"INFO: Connecting to device {validDeviceIP}...")
            authLog.info(f"Connecting to device {validDeviceIP}...")
            with ConnectHandler(**currentNetDevice) as sshAccess:
                try:
                    authLog.info(f"Connected to device {validDeviceIP}")
                    sshAccess.enable()
                    shHostnameOut = sshAccess.send_command(shHostname)
                    authLog.info(f"User {username} successfully found the hostname {shHostnameOut}")
                    shHostnameOut = shHostnameOut.split(' ')[1]
                    shHostnameOut = shHostnameOut + "#"
                        
                    print(f"INFO: Taking a \"{shVlanID20}\" for device: {validDeviceIP}")
                    shVlanID20Out = sshAccess.send_command(shVlanID20)
                    authLog.info(f"Automation successfully ran the command:{shVlanID20}\n{shHostnameOut}{shVlanID20}\n{shVlanID20Out}")

                    if "not found" in shVlanID20Out:
                        print(f"INFO: Device: {validDeviceIP}, is an Elevance Site device")
                        authLog.info(f"Device: {validDeviceIP}, is an Elevance Site device")   

                        print(f"INFO: Taking a \"{shRunDevice}\" for device: {validDeviceIP}")
                        shRunDeviceOut = sshAccess.send_command(shRunDevice)
                        authLog.info(f"Automation successfully ran the command:{shRunDevice}\n{shHostnameOut}{shRunDevice}\n{shRunDeviceOut}")

                        for index, item in enumerate(deviceTrackingConf):
                            print(f"INFO: Checking for \"{item}\" in {validDeviceIP}")
                            if not item in shRunDeviceOut:
                                # missingConfig.append(item)
                                authLog.info(f"Configuration: {item} is missing from device {validDeviceIP}")
                                authLog.info(f"Skipping device: {validDeviceIP}")
                                print(f"INFO: Configuration: {item} is missing from device {validDeviceIP}, skipping device")
                                missingConfig1 = True
                                break
                            else:
                                # configInDevice.append(item)
                                missingConfig1 = False
                                authLog.info(f"Configuration: {item} was found on device {validDeviceIP}")

                        if missingConfig1 == True:
                            with open('missingDeviceTrack_Configuration.csv', mode='a', newline='') as file:
                                writer = csv.writer(file)
                                writer.writerow([validDeviceIP])
                            continue

                        shIntStatusOut = sshAccess.send_command(shIntStatus)
                        authLog.info(f"Automation ran the command \"{shIntStatus}\" on device {validDeviceIP}\n{shHostnameOut}{shIntStatusOut}")
                        print(f"INFO: Running the following command: \"{shIntStatus}\" on device {validDeviceIP}\n{shHostnameOut}{shIntStatusOut}")
                        shIntStatusOut1 = re.findall(intPatt, shIntStatusOut)
                        authLog.info(f"Automation found the following interfaces on device {validDeviceIP}: {shIntStatusOut1}")

                        for interface in shIntStatusOut1:
                            interfaceOut = sshAccess.send_command(f'show run int {interface}')
                            if not shIntDevTrack.search(interfaceOut):
                                authLog.info(f"Configuration: {shIntDevTrack.pattern} is missing from device: {validDeviceIP} on interface {interface}")
                                authLog.info(f"Skipping device {validDeviceIP}")
                                print(f"INFO: Skipping device {validDeviceIP}")
                                missingConfig1 = True
                                break
                            else:
                                print(f"INFO: Interface {interface} has configured {shIntDevTrack.pattern} on device {validDeviceIP}")
                                authLog.info(f"Interface {interface} has configured {shIntDevTrack.pattern} on device {validDeviceIP}")
                                missingConfig1 = False
                                deviceConfigured = True

                        if deviceConfigured == True:
                            with open('configuredDevices_DeviceTrack.csv', mode='a', newline='') as file:
                                writer = csv.writer(file)
                                writer.writerow([validDeviceIP])
                
                        # with open(f"Outputs/{validDeviceIP}_complianceCheck-DevTrack.txt", "a") as file:
                        #     file.write(f"User {username} connected to device IP {validDeviceIP}\n\n")
                        #     file.write("="*20 + "\n")
                        #     file.write(f"Below is the missing configuration:\n")
                        #     file.write(f"{shHostnameOut}\n{'\n'.join(missingConfig)}\n\n")
                        #     file.write("="*20 + "\n")
                        #     file.write(f"Below is the current configuration:\n")
                        #     file.write(f"{shHostnameOut}{shRunDevice}\n{'\n'.join(configInDevice)}\n\n")
                        #     authLog.info(f"File {validDeviceIP}_dhcpSnoopCheck.txt was created successfully.")

                        print(f"Outputs and files successfully created for device {validDeviceIP}.\n")
                        print("For any erros or logs please check Logs -> authLog.txt\n")
                        print(f"Program finished, all the configuration has been applied.")
                        
                    else:
                        print(f"INFO: Device: {validDeviceIP}, is a Caremore Site device")
                        authLog.info(f"Device: {validDeviceIP}, is a Caremore Site device")   
                        continue

                except Exception as error:
                    print(f"ERROR: An error occurred: {error}\n", traceback.format_exc())
                    authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}")
                    authLog.error(traceback.format_exc(),"\n")
                    os.system("PAUSE")
       
        except Exception as error:
            print(f"ERROR: An error occurred: {error}\n", traceback.format_exc())
            authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}")
            authLog.error(traceback.format_exc(),"\n")
            with open(f"failedDevices.txt","a") as failedDevices:
                failedDevices.write(f"User {username} connected to {validDeviceIP} got an error.\n")
