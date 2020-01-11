import platform
import win32com
import wmi
"""
本模块基于windows操作系统，依赖wmi和win32com库，需要提前使用pip进行安装，
pip install wmi
pip install pypiwin32
或者下载安装包手动安装。
"""


class Win32Info(object):
    def __init__(self):
        self.wmi_obj = wmi.WMI()
        self.wmi_service_obj = win32com.client.Dispatch(
            "WbemScripting.SWbemLocator")
        self.wmi_service_connector = self.wmi_service_obj.ConnectServer(
            ".", "root\cimv2")

    def collect(self):
        data = {
            'os_type':
            platform.system(),
            'os_release':
            "%s %s %s" % (platform.release(), platform.architecture()[0],
                          platform.version()),
            'os_distribution':
            'Microsoft',
            'assert_type':
            'server'
        }
        # 分别获取各种硬件信息
        data.update(self.get_cpu_info())
        data.update(self.get_ram_info())
        data.update(self.get_motherboard_info())
        data.update(self.get_disk_info())
        data.update(self.get_nic_info())
        # 最后返回一个字典
        return data

    def get_cpu_info(self):
        """ 获取cpu相关的数据 """
        data = {}
        cpu_list = self.wmi_obj.Win32_Processor()
        cpu_core_count = 0
        for cpu in cpu_list:
            cpu_core_count += cpu.NumberOfCores

        cpu_model = cpu_list[0].Name
        data['cpu_count'] = len(cpu_list)
        data['cpu_model'] = cpu_model
        data['cpu_core_count'] = cpu_core_count

        return data

    def get_ram_info(self):
        """ 收集内存信息 """
        data = []
        ram_collections = self.wmi_service_connector.ExecQuery(
            'Select * from Win32_PhysicalMemory')
        for ram in ram_collections:
            ram_size = int(int(ram.Capacity) / (1024**3))
            item_data = {
                'slot': ram.DeviceLocator.strip(),
                'capacity': ram_size,
                'model': ram.Caption,
                'manufacturer': ram.Manufacturer,
                'sn': ram.SerialNumber,
            }
            data.append(item_data)  # 将每条内存的信息，添加到一个列表里
        return {'RAM': data}  # 再对data列表封装一层，返回一个字典，方便上级方法的调用

    def get_motherboard_info(self):
        """ 获取主板信息 """
        computer_info = self.wmi_obj.Win32_ComputerSystem()[0]
        system_info = self.wmi_obj.Win32_OperatingSystem()[0]
        data = {}
        data['manufacturer'] = computer_info.Manufacturer
        data['model'] = computer_info.Model
        data['wake_up_type'] = computer_info.WakeUpType
        data['sn'] = system_info.SerialNumber
        return data

    def get_disk_info(self):
        """ 硬盘信息 """
        data = []
        for disk in self.wmi_obj.Win32_DiskDrive():
            disk_data = {}
            interface_choices = ['SAS', 'SCSI', 'SATA', 'M.2']
            for interface in interface_choices:
                if interface in disk.Model:
                    disk_data['interface_type'] = interface
                    break
            else:
                disk_data['interface_type'] = 'unknown'

            disk_data['slot'] = disk.Index
            disk_data['sn'] = disk.SerialNumber
            disk_data['model'] = disk.Model
            disk_data['manufacturer'] = disk.Manufacturer
            disk_data['capacity'] = int(int(disk.Size) / (1024**3))
            data.append(disk_data)

        return {'physical_disk_driver': data}

    def get_nic_info(self):
        """ 网卡信息 """
        data = []
        for nic in self.wmi_obj.Win32_NetworkAdapterConfiguration():
            if nic.MACAddress is not None:
                nic_data = {}
                nic_data['mac'] = nic.MACAddress
                nic_data['model'] = nic.Caption
                nic_data['name'] = nic.Index
                if nic.IPAddress is not None:
                    nic_data['ip_address'] = nic.IPAddress
                    nic_data['net_mask'] = nic.IPSubnet
                else:
                    nic_data['ip_address'] = ''
                    nic_data['net_mask'] = ''
                data.append(nic_data)
        return {'nic': data}


if __name__ == "__main__":
    # 测试代码
    data = Win32Info().collect()
    for key in data:
        print(key, ":", data[key])