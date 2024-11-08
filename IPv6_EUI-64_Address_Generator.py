# -*- coding: utf-8 -*-

import re
import sys
import json
import socket
import ipaddress
from PyQt5.QtWidgets import (
    QLabel,
    QDialog,
    QComboBox,
    QLineEdit,
    QGridLayout,
    QApplication
)
from PyQt5.QtCore import (
    Qt,
    QCoreApplication
)
from PyQt5.QtGui import (
    QFont
)


g_strWindowTitle = 'IPv6 EUI-64 Address Generator Build:20241108'


class MainWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.initUI()

    def initUI(self):
        # 设置对话框标题
        self.setWindowTitle(g_strWindowTitle)
        # 设置对话框标题栏具有最小化按钮
        self.setWindowFlag(Qt.WindowMinimizeButtonHint)

        self.Label_IPv6PrefixAddress = QLabel('IPv6地址（域名 / IPv6）', self)
        self.ComboBox_IPv6PrefixAddress = QComboBox(self)
        self.ComboBox_IPv6PrefixAddress.setEditable(True)  # 设置 QComboBox 允许编辑

        self.Label_MACAddress = QLabel('MAC地址', self)
        self.ComboBox_MACAddress = QComboBox(self)
        self.ComboBox_MACAddress.setEditable(True)  # 设置 QComboBox 允许编辑

        self.Label_IPv6Address = QLabel('生成的IPv6地址', self)
        self.ComboBox_IPv6Address = QLineEdit(self)
        self.ComboBox_IPv6Address.setReadOnly(True)  # 设置控件只读
        self.ComboBox_IPv6Address.setMinimumWidth(300)

        self.MyLayout = QGridLayout(self)
        self.MyLayout.addWidget(self.Label_IPv6PrefixAddress, 0, 0)
        self.MyLayout.addWidget(self.ComboBox_IPv6PrefixAddress, 0, 1)
        self.MyLayout.addWidget(self.Label_MACAddress, 1, 0)
        self.MyLayout.addWidget(self.ComboBox_MACAddress, 1, 1)
        self.MyLayout.addWidget(self.Label_IPv6Address, 2, 0)
        self.MyLayout.addWidget(self.ComboBox_IPv6Address, 2, 1)

        # 设置布局
        self.setLayout(self.MyLayout)

        # 信号槽绑定
        self.ComboBox_IPv6PrefixAddress.currentIndexChanged.connect(
            self.on_item_selected_IPv6PrefixAddress)
        self.ComboBox_IPv6PrefixAddress.editTextChanged.connect(
            self.on_edit_text_changed_IPv6PrefixAddress)

        self.ComboBox_MACAddress.currentIndexChanged.connect(
            self.on_item_selected_MACAddress)
        self.ComboBox_MACAddress.editTextChanged.connect(
            self.on_edit_text_changed_MACAddress)

        # 其它初始化
        try:
            with open('./config.json', 'r', encoding='UTF-8') as json_file:
                data = json.load(json_file)
                for index, item in enumerate(data['IPv6PrefixDomainList']):
                    if len(item):
                        self.ComboBox_IPv6PrefixAddress.addItem(item)
                for index, item in enumerate(data['MACAddressesList']):
                    if (item['MAC']):
                        self.ComboBox_MACAddress.addItem(item['MAC'])
                        if (item['Alias']):
                            self.ComboBox_MACAddress.setItemData(
                                index, item['Alias'], role=Qt.ToolTipRole)
        except Exception:
            pass
        self.ComboBox_IPv6PrefixAddress.setCurrentIndex(-1)
        self.ComboBox_MACAddress.setCurrentIndex(-1)

    # 选择条目时的槽函数
    def on_item_selected_IPv6PrefixAddress(self, index):
        self.Fun_GenerateIPv6Address()

    def on_item_selected_MACAddress(self, index):
        self.Fun_GenerateIPv6Address()

    # 编辑文本框内容变化时的槽函数
    def on_edit_text_changed_IPv6PrefixAddress(self, text):
        self.Fun_GenerateIPv6Address()

    def on_edit_text_changed_MACAddress(self, text):
        self.Fun_GenerateIPv6Address()

    def Fun_GenerateIPv6Address(self):
        self.ComboBox_IPv6Address.setText('')

        strIPv6PrefixAddress = self.ComboBox_IPv6PrefixAddress.currentText()
        if len(strIPv6PrefixAddress) and \
                self.Fun_IsIpv6Address(strIPv6PrefixAddress) is False:
            strIPv6PrefixAddress = self.Fun_GetIPv6Address(
                strIPv6PrefixAddress)
        strMACAddress = self.ComboBox_MACAddress.currentText()
        if len(strMACAddress) and \
                self.Fun_IsValidMACAddress(strMACAddress) is False:
            strMACAddress = ''
        if len(strIPv6PrefixAddress) and len(strMACAddress):
            try:
                # 将 IPv6 地址转换为 IPv6Address 对象
                ip = ipaddress.IPv6Address(strIPv6PrefixAddress)
                # 获取地址的完整表示并分割
                full_address = ip.exploded.split(':')

                # 提取前 64 位 (前 4 个组)
                strIPv6PD = ':'.join(full_address[:4])

                strIPv6Address = strIPv6PD + ':' + \
                    self.Fun_MAC2EUI64(strMACAddress)

                # 压缩IPv6地址
                if len(strIPv6Address):
                    strIPv6Address = self.Fun_CompressIPV6(strIPv6Address)

                self.ComboBox_IPv6Address.setText(strIPv6Address)

            except Exception:
                pass

    def Fun_IsIpv6Address(self, address):
        # IPv6地址正则表达式，支持简写和标准形式
        ipv6_pattern = (
            r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"  # 完整的8组十六进制
            r"|^([0-9a-fA-F]{1,4}:){1,7}:$"               # 支持::位置在末尾
            r"|^([0-9a-fA-F]{1,4}:){1,6}(:[0-9a-fA-F]{1,4}){1,1}$"  # 中间是::
            # 支持::最多两个字段
            r"|^([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}$"
            # 支持::最多三个字段
            r"|^([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}$"
            # 支持::最多四个字段
            r"|^([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}$"
            # 支持::最多五个字段
            r"|^([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}$"
            r"|^[0-9a-fA-F]{1,4}:((?::[0-9a-fA-F]{1,4}){1,6})$"  # 支持::后面6个字段
            r"|^::([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}$"  # ::在最前面
            r"|^::([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}$"  # ::在最前面，中间有一个字段
            r"|^::([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}$"  # ::最多两字段
            r"|^::([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}$"  # ::最多三字段
            r"|^::([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}$"  # ::最多四字段
            r"|^::([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}$"  # ::最多五字段
            r"|^::([0-9a-fA-F]{1,4}:){1,1}(:[0-9a-fA-F]{1,4}){1,6}$"  # ::最多六字段
            r"|^::$"  # 纯零地址
        )

        # 使用正则表达式进行匹配
        return bool(re.match(ipv6_pattern, address))

    def Fun_GetIPv6Address(self, domain):
        try:
            # 获取域名的IPv6地址
            ipv6_addresses = socket.getaddrinfo(domain, None, socket.AF_INET6)

            # 返回第一个IPv6地址
            for info in ipv6_addresses:
                # `info[4][0]` 包含IPv6地址
                return info[4][0]
        except socket.gaierror:
            # 如果无法解析域名
            return ''

    def Fun_MAC2EUI64(self, mac):
        # 将 MAC 地址转换为十进制格式
        mac_bytes = mac.split(':')
        mac_int = [int(byte, 16) for byte in mac_bytes]

        # 插入中间的 ff:fe
        eui64 = mac_int[:3] + [0xff, 0xfe] + mac_int[3:]

        # 将第一个字节的第七位反转
        eui64[0] ^= 0x02

        # 生成符合 IPv6 规范的后 64 位地址
        eui64_ipv6 = ':'.join(f'{byte:02x}' for byte in eui64)
        indexes_to_remove = {2, 8, 14, 20}  # 要删除的字符位置（索引从0开始）

        eui64_ipv6 = ''.join([char for i, char in enumerate(
            eui64_ipv6) if i not in indexes_to_remove])

        return eui64_ipv6

    def Fun_CompressIPV6(self, ipv6_address):
        return socket.inet_ntop(
            socket.AF_INET6,
            socket.inet_pton(
                socket.AF_INET6,
                ipv6_address
            )
        )

    def Fun_IsValidMACAddress(self, mac):
        # 匹配 MAC 地址的正则表达式
        mac_regex = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$')

        # 使用正则表达式进行匹配
        return bool(mac_regex.match(mac))


if __name__ == '__main__':
    QCoreApplication.\
        setAttribute(Qt.AA_EnableHighDpiScaling, True)  # 高分屏支持
    QCoreApplication.\
        setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # HiDPI pixmaps

    App = QApplication(sys.argv)

    # 设置默认字体
    Font = QFont()
    Font.setFamily('Segoe UI')
    # font.setPointSize(5)
    App.setFont(Font)

    # 创建主窗口
    Win = MainWindow()
    Win.show()

    sys.exit(App.exec_())
