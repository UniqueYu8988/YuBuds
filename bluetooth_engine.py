import asyncio
import subprocess
from winsdk.windows.devices.enumeration import DeviceInformation, DeviceInformationKind
from winsdk.windows.foundation import IPropertyValue, PropertyType

class BluetoothEngine:
    # Windows 标准电池电量属性 Key (GUID + PID)
    BATTERY_LEVEL_KEY = "{104EA319-6EE2-4701-BD47-8DDBF425BBE5} 2"
    # 连接状态属性 Key
    IS_CONNECTED_KEY = "System.Devices.Aep.IsConnected"
    # 容器 ID 属性 Key (用于关联物理设备的不同逻辑节点)
    CONTAINER_ID_KEY = "System.Devices.ContainerId"

    def __init__(self, target_name="Mijia Glasses Lite"):
        self.target_name = target_name

    @staticmethod
    def _unbox(val):
        """将 winsdk 属性值安全转换为 Python 类型"""
        if val is None:
            return None
        try:
            prop = IPropertyValue._from(val)
            if prop.type == PropertyType.UINT8:
                return prop.get_uint8()
            if prop.type == PropertyType.INT32:
                return prop.get_int32()
            if prop.type == PropertyType.BOOLEAN:
                return prop.get_boolean()
            if prop.type == PropertyType.GUID:
                return str(prop.get_guid())
            if prop.type == PropertyType.STRING:
                return prop.get_string()
            return str(val)
        except:
            return str(val)

    async def get_device_info(self):
        """
        核心逻辑：
        1. 搜索名称匹配的 AssociationEndpoint，获取其 ContainerId 和连接状态。
        2. 使用 ContainerId 扫描该物理设备下的所有节点 (Kind=Device 或 DeviceInterface)。
        3. 提取电池属性。
        """
        try:
            # 1. 查找目标设备的主入口 (尝试多种 Kind 以确保搜到)
            target_cid = None
            is_connected = False
            
            search_kinds = [
                DeviceInformationKind.ASSOCIATION_ENDPOINT,
                DeviceInformationKind.DEVICE_INTERFACE,
                DeviceInformationKind.DEVICE
            ]
            
            found_node = None
            for kind in search_kinds:
                nodes = await DeviceInformation.find_all_async(kind)
                for node in nodes:
                    if self.target_name.lower() in node.name.lower():
                        found_node = node
                        # 尝试获取属性
                        props = await DeviceInformation.create_from_id_async(node.id, [self.IS_CONNECTED_KEY, self.CONTAINER_ID_KEY])
                        
                        if props.properties.has_key(self.IS_CONNECTED_KEY):
                            if self._unbox(props.properties.lookup(self.IS_CONNECTED_KEY)):
                                is_connected = True
                        
                        if props.properties.has_key(self.CONTAINER_ID_KEY):
                            target_cid = self._unbox(props.properties.lookup(self.CONTAINER_ID_KEY))
                        
                        if target_cid: break
                if target_cid: break
            
            if not target_cid:
                return {"name": self.target_name, "is_connected": False, "battery": None, "found": False}

            # 2. 扫描容器内的所有节点以查找电量
            # 经验证，米家眼镜的电量通常在 Hands-Free AG 节点上，属于 Kindle.Device
            aqs = f'System.Devices.ContainerId:="{{{target_cid}}}"'
            
            # 我们检查 Device 和 DeviceInterface
            battery_value = None
            
            # 先查 Kind.Device
            nodes = await DeviceInformation.find_all_async(aqs, [self.BATTERY_LEVEL_KEY], DeviceInformationKind.DEVICE)
            for node in nodes:
                if node.properties.has_key(self.BATTERY_LEVEL_KEY):
                    val = self._unbox(node.properties.lookup(self.BATTERY_LEVEL_KEY))
                    if isinstance(val, int) and 0 <= val <= 100:
                        battery_value = val
                        break
            
            # 如果没找到，再查 DeviceInterface
            if battery_value is None:
                nodes = await DeviceInformation.find_all_async(aqs, [self.BATTERY_LEVEL_KEY], DeviceInformationKind.DEVICE_INTERFACE)
                for node in nodes:
                    if node.properties.has_key(self.BATTERY_LEVEL_KEY):
                        val = self._unbox(node.properties.lookup(self.BATTERY_LEVEL_KEY))
                        if isinstance(val, int) and 0 <= val <= 100:
                            battery_value = val
                            break

            return {
                "name": self.target_name,
                "is_connected": is_connected,
                "battery": battery_value,
                "found": True
            }

        except Exception as e:
            print(f"Error in BluetoothEngine: {e}")
            return {"name": self.target_name, "is_connected": False, "battery": None, "found": False, "error": str(e)}

    async def open_bluetooth_settings(self):
        """打开系统蓝牙设置"""
        try:
            subprocess.Popen('start ms-settings:bluetooth', shell=True)
            return True
        except:
            return False

    async def open_mic_settings(self):
        """打开系统麦克风隐私设置"""
        try:
            subprocess.Popen('start ms-settings:privacy-microphone', shell=True)
            return True
        except:
            return False

if __name__ == "__main__":
    async def test():
        engine = BluetoothEngine()
        res = await engine.get_device_info()
        print(f"扫描结果: {res}")
    
    asyncio.run(test())
