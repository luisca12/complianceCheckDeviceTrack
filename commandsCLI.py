from netmiko import ConnectHandler
from log import authLog

import traceback
import re
import os

interface = ''
snoopTrust = "ip dhcp snooping trust"
snoopIntConfigOut = ""
snoopIntConfigOut1 = ""

shHostname = "show run | i hostname"
shIntStatus = "show interface status | exc SDW|sdw|LUM"
shVlanID1101 = "show vlan id 1101"
shVlanID1103 = "show vlan id 1103"

snoopGenIntConfigOutList = []

snoopGlobalConfig = [
    'ip dhcp snooping vlan 2-3999',
    'no ip dhcp snooping information option',
    'ip dhcp snooping',
    'errdisable recovery cause dhcp-rate-limit',
    'errdisable recovery interval 300',
    'class-map match-any system-cpp-police-protocol-snooping',
    'description Protocol snooping',
    'class-map match-any system-cpp-police-dhcp-snooping',
    'description DHCP snooping'
]

snoopIntConfig = [
    f'int {interface}',
    'ip dhcp snooping trust'
]

snoopGenIntConfig = [
    f'int {interface}',
    'ip dhcp snooping limit rate 50'
]

catchAll = [
    'event manager applet catchall',
    'event cli pattern ".*" sync no skip no',
    'action 1 syslog msg "$_cli_msg"',
    'exit',
    'terminal monitor'
]

delCatchAll = [
    'no event manager applet catchall',
    'exit',
    'terminal no monitor'
]

# Regex Patterns
intPatt = r'[a-zA-Z]+\d+\/(?:\d+\/)*\d+'
intPatt2 = r'[Te]+\d+\/(?:1+\/)+\d+'

def dhcpSnooopTr(validIPs, username, netDevice):
    # This function is to take a show run

    for validDeviceIP in validIPs:
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

            print(f"Connecting to device {validDeviceIP}...")
            with ConnectHandler(**currentNetDevice) as sshAccess:
                try:
                    sshAccess.enable()
                    catchAllOut = sshAccess.send_config_set(catchAll)
                    authLog.info(f"The script catchall was sent to the device {validDeviceIP}")
                    print(f"INFO: Script catchall was configured on the device {validDeviceIP}")
                    shHostnameOut = sshAccess.send_command(shHostname)
                    authLog.info(f"User {username} successfully found the hostname {shHostnameOut}")
                    shHostnameOut = shHostnameOut.replace('hostname', '')
                    shHostnameOut = shHostnameOut.strip()
                    shHostnameOut = shHostnameOut + "#"

                    print(f"INFO: Taking a \"{shVlanID1101}\" for device: {validDeviceIP}")
                    shVlanID1101Out = sshAccess.send_command(shVlanID1101)
                    authLog.info(f"Automation successfully ran the command:{shVlanID1101}\n{shHostnameOut}{shVlanID1101}\n{shVlanID1101Out}")

                    if "not found" in shVlanID1101Out:
                        print(f"INFO: Device {validDeviceIP} does not have VLANS 1101 and 1103, skipping device...")
                        authLog.info(f"Device {validDeviceIP} does not have VLANS 1101 and 1103, skipping device...")
                        continue

                    shVlanID1101Out1 = re.findall(intPatt, shVlanID1101Out)
                    authLog.info(f"The following interfaces were found under the command: {shVlanID1101}: {shVlanID1101Out1}")

                    if shVlanID1101Out1:
                        vlan1101IntList = []
                        
                        for interface in shVlanID1101Out1:
                            interface = interface.strip()
                            print(f"INFO: Checking configuration for interface {interface} on device {validDeviceIP}")
                            authLog.info(f"Checking configuration for interface {interface} on device {validDeviceIP}")
                            interfaceOut = sshAccess.send_command(f'show run int {interface}')
                            if snoopTrust in interfaceOut:
                                print(f"INFO: Interface {interface} has configured {snoopTrust} on device {validDeviceIP}")
                                authLog.info(f"Interface {interface} has configured {snoopTrust} on device {validDeviceIP}")
                                vlan1101IntList.append(f"Interface {interface} has configured {snoopTrust}")
                                configured = True
                                snoopIntConfigOut = f"No interfaces were modified, \"{snoopTrust}\" is already configured on interface {interface}"
                                authLog.info(f"No interfaces were modified on device {validDeviceIP}, \"{snoopTrust}\" is already configured on interface {interface}")
                            else:
                                print(f"INFO: Interface {interface} does NOT have configured {snoopTrust} on device {validDeviceIP}")
                                authLog.info(f"Interface {interface} does NOT have configured {snoopTrust} on device {validDeviceIP}")
                                vlan1101IntList.append(f"Interface {interface} does NOT have configured {snoopTrust} on device {validDeviceIP}")
                                print(f"INFO: Configuring interface {interface} on device {validDeviceIP}")
                                snoopIntConfig[0] = f'int {interface}'
                                snoopIntConfigOut = sshAccess.send_config_set(snoopIntConfig)
                                authLog.info(f"Automation sent the following configuration to interface {interface} on device {validDeviceIP}\n{snoopIntConfigOut}")
                                print(f"INFO: Successfully configured interface {interface} on device {validDeviceIP} with the below configuration:\n{snoopIntConfigOut1}")
                                configured = False
                    else:
                        print(f"INFO: No interfaces found under {shVlanID1101}")
                        authLog.info(f"No interfaces found under {shVlanID1101}")

                    print(f"INFO: Taking a \"{shVlanID1103}\" for device: {validDeviceIP}")
                    shVlanID1103Out = sshAccess.send_command(shVlanID1103)
                    authLog.info(f"Automation successfully ran the command:{shVlanID1103}\n{shHostnameOut}{shVlanID1103}\n{shVlanID1103Out}")
                    shVlanID1103Out1 = re.findall(intPatt, shVlanID1103Out)
                    authLog.info(f"The following interfaces were found under the command: {shVlanID1103}: {shVlanID1103Out1}")

                    if shVlanID1103Out1:
                        vlan1103IntList = []

                        for interface in shVlanID1103Out1:
                            interface = interface.strip()
                            print(f"INFO: Checking configuration for interface {interface} on device {validDeviceIP}")
                            authLog.info(f"Checking configuration for interface {interface} on device {validDeviceIP}")
                            interfaceOut = sshAccess.send_command(f'show run int {interface}')
                            if snoopTrust in interfaceOut:
                                print(f"INFO: Interface {interface} has configured {snoopTrust} on device {validDeviceIP}")
                                authLog.info(f"Interface {interface} has configured {snoopTrust} on device {validDeviceIP}")
                                vlan1103IntList.append(f"Interface {interface} has configured {snoopTrust}")
                                configured1 = True
                                snoopIntConfigOut1 = f"No interfaces were modified, \"{snoopTrust}\" is already configured on interface {interface}"
                                authLog.info(f"No interfaces were modified on device {validDeviceIP}, \"{snoopTrust}\" is already configured on interface {interface}")
                            else:
                                print(f"INFO: Interface {interface} does NOT have configured {snoopTrust} on device {validDeviceIP}")
                                authLog.info(f"Interface {interface} does NOT have configured {snoopTrust} on device {validDeviceIP}")
                                vlan1103IntList.append(f"Interface {interface} does NOT have configured {snoopTrust} on device {validDeviceIP}")
                                print(f"INFO: Configuring interface {interface} on device {validDeviceIP}")
                                snoopIntConfig[0] = f'int {interface}'
                                snoopIntConfigOut1 = sshAccess.send_config_set(snoopIntConfig)
                                print(f"INFO: Successfully configured interface {interface} on device {validDeviceIP} with the below configuration:\n{snoopIntConfigOut1}")
                                authLog.info(f"Automation sent the following configuration to interface {interface} on device {validDeviceIP}\n{snoopIntConfigOut1}")
                                configured1 = False
                    else:
                        print(f"INFO: No interfaces found under {shVlanID1103}")
                        authLog.info(f"No interfaces found under {shVlanID1103}")

                    if configured or configured1 == False:
                        snoopGlobalConfigOut = sshAccess.send_config_set(snoopGlobalConfig)
                        authLog.info(f"Automation sent the following General Configuration to device {validDeviceIP}\n{snoopGlobalConfigOut}")
                        print(f"INFO: The following General Configuration was sent to the device {validDeviceIP}\n{snoopGlobalConfigOut}")

                    shIntStatusOut = sshAccess.send_command(shIntStatus)
                    authLog.info(f"Automation ran the command \"{shIntStatus}\" on device {validDeviceIP}\n{shHostnameOut}{shIntStatusOut}")
                    print(f"INFO: Running the following command: \"{shIntStatus}\" on device {validDeviceIP}\n{shHostnameOut}{shIntStatusOut}")
                    shIntStatusOut1 = re.findall(intPatt, shIntStatusOut)
                    authLog.info(f"Automation found the following interfaces on device {validDeviceIP}: {shIntStatusOut1}")
                    shIntStatusOut2 = [match for match in shIntStatusOut1 if not re.match(intPatt2, match)]
                    authLog.info(f"Automation filtered the following interfaces on device {validDeviceIP}: {shIntStatusOut2}")
                    print(f"INFO: The following interfaces will be modified: {shIntStatusOut2}")

                    for interface in shIntStatusOut2:
                        print(f"INFO: Configuring interface {interface} on device {validDeviceIP}")
                        snoopGenIntConfig[0] = f'int {interface}'
                        snoopGenIntConfigOut = sshAccess.send_config_set(snoopGenIntConfig)
                        authLog.info(f"Automation sent the following configuration to interface {interface} on device {validDeviceIP}\n{snoopGenIntConfigOut}")
                        print(f"INFO: Successfully configured Interface {interface} on device {validDeviceIP}\n")
                        snoopGenIntConfigOutList.append(snoopGenIntConfigOut)

                    snoopGenIntConfigOutStr = " ".join(snoopGenIntConfigOutList)
                    snoopGenIntConfigOutStr.split("\n")

                    delCatchAllOut = sshAccess.send_config_set(delCatchAll)
                    authLog.info(f"The script catchall was unconfigured from the device {validDeviceIP}")
                    print(f"INFO: Script catchall was unconfigured from the device {validDeviceIP}")

                    writeMemOut = sshAccess.send_command('write')
                    print(f"INFO: Running configuration saved for device {validDeviceIP}")
                    print(f"INFO: All the configuration has been applied")
                    authLog.info(f"Running configuration saved for device {validDeviceIP}\n{shHostnameOut}'write'\n{writeMemOut}")

                    with open(f"Outputs/{validDeviceIP}_dhcpSnoopCheck.txt", "a") as file:
                        file.write(f"User {username} connected to device IP {validDeviceIP}\n\n")
                        file.write(f"Interfaces under vlan 1101:\n{vlan1101IntList}\n")
                        file.write(f"Interfaces under vlan 1103:\n{vlan1103IntList}\n")
                        file.write(f"\nConfiguration applied to the ports:\n")
                        file.write(f"\n{snoopIntConfigOut}\n")
                        file.write(f"\n{snoopIntConfigOut1}\n")
                        file.write(f"\nGeneral configuration applied to the device:\n{snoopGlobalConfigOut}\n")
                        file.write(f"\nConfiguration applied to every port:{snoopGenIntConfigOutStr}")
                        authLog.info(f"File {validDeviceIP}_dhcpSnoopCheck.txt was created successfully.")

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
        
        finally:
            print(f"Outputs and files successfully created for device {validDeviceIP}.\n")
            print("For any erros or logs please check Logs -> authLog.txt\n")
            print(f"Program finished, all the configuration has been applied.")