import pandas as pd
from GetMacTable import mac_fm
# import numpy as np

access_points = pd.read_csv('access_points.csv')
mac_address_tables = pd.read_csv('mac_address_tables.csv')
switches = pd.read_csv('switches.csv')

# Chuyen dinh dang MAC Address cho thong nhat

access_points['serial_number'] = access_points['serial_number'].apply(
    lambda x: mac_fm(x))
mac_address_tables['mac'] = mac_address_tables['mac'].apply(
    lambda x: mac_fm(x))
switches['mac'] = switches['mac'].apply(lambda x: mac_fm(x))

devices1 = access_points[['serial_number', 'displayname']].copy()
devices2 = switches[['mac', 'name']].copy()
devices2 = devices2.rename(columns={
    'mac': 'serial_number',
    'name': 'displayname'
})

full_devices = pd.concat([devices1, devices2], ignore_index=True)
full_devices['parent'] = 0
full_devices = full_devices.set_index('serial_number')
print(full_devices)

# xoa cac gia tri o port uplink va CPU

mac_address_tables = mac_address_tables[~mac_address_tables['port'].isin(
    ('gi28', 'CPU'))]

for mac in full_devices.index:
    parents = mac_address_tables[(mac_address_tables['mac'] == mac)]
    how_many_parents = len(parents.index)
    print('"{}" la con cua {} thiet bi'.format(mac, how_many_parents))
    full_devices.at[mac, 'parent'] = how_many_parents

column_name = ['serial_number', 'name', 'parent', 'port']
result_table = pd.DataFrame(columns=column_name)
for serial_number in full_devices.index:
    print('+++')
    print('Dang kiem tra thiet bi: %s' % serial_number)
    row = full_devices.loc[serial_number]
    # print(row)
    # lay ten thiet bi
    # print('***')
    name = row['displayname']
    # print(name)
    parent_class_id = row['parent']
    # print(parent_class_id)

    # tim thiet bi cap tren
    if parent_class_id != 0:
        possible_parent_devices = full_devices[full_devices['parent'] ==
                                               row['parent'] - 1]
        # print('===')
        # print(possible_parent_devices)
        # print('===')
        possible_parent_names = possible_parent_devices['displayname'].tolist()
        # print('///')
        # print(possible_parent_names)
        # print('///')
        parent_device_info = mac_address_tables[
            mac_address_tables['sw'].isin(possible_parent_names)
            & (mac_address_tables['mac'] == serial_number)]
        # print('ZZZ')
        # print(parent_device_info)
        # print('ZZZ')
        parent_device_info = parent_device_info.iloc[0]
        print(parent_device_info)
        parent_name = parent_device_info['sw']
        print(parent_name)
        connection_port = parent_device_info['port']
        print(connection_port)

    else:
        parent_name = 'Router'
        connection_port = 'NaN'

    device_info = pd.Series(
        [serial_number, name, parent_name, connection_port], index=column_name)
    result_table = result_table.append(device_info, ignore_index=True)
    result_table = result_table.sort_values(by=['parent', 'name'])

print(result_table)
result_table.to_csv('devices_connection_info.csv')
