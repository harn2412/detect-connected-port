from telnetlib import Telnet
from time import sleep
import re
import pandas


def file_to_list(patch):
    with open(patch) as csv_file:
        lines = csv_file.read().splitlines()
        return lines


def mac_fm(mac_addr):
    """Chuyen dia chi MAC ve dang thong nhat
    :type mac_addr: str
    """
    # Kiem tra cac ky tu chua trong gia tri dau vao
    mac_addr = mac_addr.lower()
    mac_addr_set = set(mac_addr)
    mac_valid_char = set('0123456789' 'abcdef' '-:')

    if not mac_addr_set < mac_valid_char:
        unvalid_char = mac_addr_set - mac_valid_char
        raise ValueError("Co chua cac gia tri khong phu hop: %s" %
                         unvalid_char)

    # Xoa bo cac ky tu khong can thiet
    del_char = ['-', ':']
    for char in del_char:
        mac_addr = mac_addr.replace(char, '')

    # kiem tra do dai dia chi
    if len(mac_addr) != 12:
        raise ValueError("Khong dung chieu dai")

    return mac_addr


class DrayTekSw01:
    """Cac model bao gom G2280, G1280"""
    @staticmethod
    def get_mac_table(ip, user, password):
        """In ra bang Mac Address Table tren switch
        :type ip: str
        :type user: str
        :type password: str"""

        print('Dang lay MAC Address Table cua switch "%s"' % ip)
        with Telnet(ip) as tn:
            tn.write(user.encode('utf8') + b'\n')
            sleep(2)
            tn.write(password.encode('utf8') + b'\n')
            sleep(2)
            login_result = tn.read_until(b'#', 2)
            if b'#' not in login_result:
                print('Khong the dang nhap thiet bi')
                return None

            tn.write(b'show mac address-table\n')

            data = b''
            while True:
                temp = tn.read_until(b'#', 2)
                data += temp
                if b'#' in temp:
                    mac_text = data.decode('ascii').replace(
                        '--More--\x08\r\n\x1b[A\x1b[2K', '')
                    return mac_text
                else:
                    tn.write(b' ')
                    sleep(1)

    @staticmethod
    def parser(raw_data, sw_name):
        """
        :type raw_data: str
        :type sw_name: str
        """
        pattern = re.compile(
            r'''(
            (\d+)       # vlan
            \s+\|\s+    # split column
            (\S+)       # mac
            \s+\|\s+    # split column
            (\S+)       # type
            \s+\|\s+    # split column
            (\S+)       # port
            )''', re.VERBOSE)

        lines = raw_data.splitlines()
        rows = []

        for line in lines:
            result = pattern.search(line)
            if result:
                vlan = result.group(2)
                mac = mac_fm(result.group(3))
                learn_type = result.group(4)
                port = result.group(5)

                row = (sw_name, vlan, mac, learn_type, port)

                rows.append(row)

        header = ['sw', 'vlan', 'mac', 'learn_type', 'port']
        return header, rows


def main():
    hosts_df = pandas.read_csv('switches.csv')
    mac_df = pandas.DataFrame()

    for index, sw_info in hosts_df.iterrows():
        print('===***===')
        print('Dang tien hanh lay MAC Address Table cua switch "%s"' %
              sw_info['name'])

        draytek_models = ['g2280', 'g1280']
        if sw_info['model'] in draytek_models:
            worker = DrayTekSw01()
            print('Thiet bi thuoc nhom "DrayTekSw01"')
        else:
            raise ValueError('Thiet bi khong duoc ho tro: %s' % sw_info.model)

        mac_raw_fm = worker.get_mac_table(sw_info['ip'], sw_info['usr'],
                                          sw_info['pwd'])

        if mac_raw_fm is None:
            print('Khong tim thay du lieu, tien hanh bo qua ...')
            continue

        header, dump_mac_table = worker.parser(mac_raw_fm, sw_info['name'])
        dump_mac_df = pandas.DataFrame(dump_mac_table, columns=header)
        mac_df = mac_df.append(dump_mac_df, ignore_index=True)

        print(
            'Da hoan tat viec lay dia chi MAC, chuan bi chuyen qua switch khac ...'
        )

    mac_df.to_csv('mac_address_tables.csv', index=False)
    print('Hoan tat cong viec')


if __name__ == '__main__':
    main()
