from netmiko import ConnectHandler
from log import authLog
from functions import failedDevices, logInCSV

import traceback
import csv
import os
import re

shHostname = "show run | i hostname"
shIntStatus = "show interface status"
shRunDevice = "show run | sec device-sensor"
shRunAttDevTrk = "show run | inc device-tracking attach-policy DEVTRK|device-tracking attach-policy IPDT_POLICY"

shVlanID1105 = "show vlan id 1105"

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
                'session_log': 'Outputs/netmikoLog.txt',
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
                        
                    print(f"INFO: Taking a \"{shVlanID1105}\" for device: {validDeviceIP}")
                    shVlanID1105Out = sshAccess.send_command(shVlanID1105)
                    authLog.info(f"Automation successfully ran the command:{shVlanID1105}\n{shHostnameOut}{shVlanID1105}\n{shVlanID1105Out}")

                    if "Ports" in shVlanID1105Out:
                        print(f"INFO: Device: {validDeviceIP}, is an Elevance Site device")
                        authLog.info(f"Device: {validDeviceIP}, is an Elevance Site device")   

                        print(f"INFO: Taking a \"{shRunDevice}\" for device: {validDeviceIP}")
                        shRunDeviceOut = sshAccess.send_command(shRunDevice)
                        authLog.info(f"Automation successfully ran the command:{shRunDevice}\n{shHostnameOut}{shRunDevice}\n{shRunDeviceOut}")
                        
                        if not "Invalid input" in shRunDeviceOut:
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
                        else:
                            failedDevices(username, validDeviceIP, error=shRunDeviceOut)
                            continue

                        if missingConfig1 == True:
                            logInCSV(validDeviceIP, filename="Devices missing Device Track Config")
                            continue
                        
                        print(f"INFO: Taking a \"{shRunAttDevTrk}\" for device: {validDeviceIP}")
                        shRunAttDevTrkOut = sshAccess.send_command(shRunAttDevTrk)
                        authLog.info(f"Automation successfully ran the command:{shRunAttDevTrk}\n{shHostnameOut}{shRunAttDevTrk}\n{shRunAttDevTrkOut}")

                        shRunAttDevTrkOut1 = shIntDevTrack.findall(shRunAttDevTrkOut)
                        authLog.info(f"Found a total of {len(shRunAttDevTrkOut1)} matches of {shIntDevTrack.pattern}")
                        if len(shRunAttDevTrkOut1) > 2:
                            logInCSV(validDeviceIP, filename="Totally Configured Device Track Devices")
                            continue
                        else:
                            logInCSV(validDeviceIP, filename="Devices missing Device Track Config")
                            authLog.info(f"Skipping device: {validDeviceIP} due to missing configuration")
                            print(f"INFO: Skipping device: {validDeviceIP} due to missing configuration")
                            continue

                        # This section searches and filters based on per interface config
                        # shIntStatusOut = sshAccess.send_command(shIntStatus)
                        # authLog.info(f"Automation ran the command \"{shIntStatus}\" on device {validDeviceIP}\n{shHostnameOut}{shIntStatusOut}")
                        # print(f"INFO: Running the following command: \"{shIntStatus}\" on device {validDeviceIP}\n{shHostnameOut}{shIntStatusOut}")
                        # shIntStatusOut1 = re.findall(intPatt, shIntStatusOut)
                        # authLog.info(f"Automation found the following interfaces on device {validDeviceIP}: {shIntStatusOut1}")

                        # for interface in shIntStatusOut1:
                        #     interfaceOut = sshAccess.send_command(f'show run int {interface}')
                        #     if not shIntDevTrack.search(interfaceOut):
                        #         authLog.info(f"Configuration: {shIntDevTrack.pattern} is missing from device: {validDeviceIP} on interface {interface}")
                        #         authLog.info(f"Skipping device {validDeviceIP}")
                        #         print(f"INFO: Skipping device {validDeviceIP}")
                        #         missingConfig1 = True
                        #         break
                        #     else:
                        #         print(f"INFO: Interface {interface} has configured {shIntDevTrack.pattern} on device {validDeviceIP}")
                        #         authLog.info(f"Interface {interface} has configured {shIntDevTrack.pattern} on device {validDeviceIP}")
                        #         missingConfig1 = False
                        #         logInCSV = True
                        # if missingConfig1 == True:
                        #     with open('missingDeviceTrack_Configuration.csv', mode='a', newline='') as file:
                        #         writer = csv.writer(file)
                        #         writer.writerow([validDeviceIP])
                        #     continue


                
                        # with open(f"Outputs/{validDeviceIP}_complianceCheck-DevTrack.txt", "a") as file:
                        #     file.write(f"User {username} connected to device IP {validDeviceIP}\n\n")
                        #     file.write("="*20 + "\n")
                        #     file.write(f"Below is the missing configuration:\n")
                        #     file.write(f"{shHostnameOut}\n{'\n'.join(missingConfig)}\n\n")
                        #     file.write("="*20 + "\n")
                        #     file.write(f"Below is the current configuration:\n")
                        #     file.write(f"{shHostnameOut}{shRunDevice}\n{'\n'.join(configInDevice)}\n\n")
                        #     authLog.info(f"File {validDeviceIP}_dhcpSnoopCheck.txt was created successfully.")

                        print(f"Outputs and files successfully created for device {validDeviceIP}.")
                        print("For any erros or logs please check Logs -> systemLogs.txt\n")

                    else:
                        print(f"INFO: Device: {validDeviceIP}, is a Caremore Site device")
                        authLog.info(f"Device: {validDeviceIP}, is a Caremore Site device")
                        logInCSV(validDeviceIP, filename="devicesDiscarded")
                        continue

                except Exception as error:
                    print(f"ERROR: An error occurred: {error}\n", traceback.format_exc())
                    authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}")
                    failedDevices(username, validDeviceIP, error)

        except Exception as error:
            print(f"ERROR: An error occurred: {error}\n", traceback.format_exc())
            authLog.error(f"User {username} connected to {validDeviceIP} got an error: {error}")
            failedDevices(username, validDeviceIP, error)