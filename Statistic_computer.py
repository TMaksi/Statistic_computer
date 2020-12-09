import psutil
import re
import time

TEMPLATES = {
    'memory':{
        'all': 'Оперативная память: \n\tВсего оперативной памяти: {:.4} ГБ\n\t',
        'used': 'Используется: {:.4} ГБ\n\t',
        'free': 'Свободно: {:.4} ГБ\n\t',
        'total': 'Размер файла подкачки: {:.4} ГБ\n'
    },
    'disks': {
        'yes': 'Диск {}, \n\topts: {},\n\tТип файловой системы: {}, \n\tРазмер: {:.4} ГБ, \n\tЗанято: {:.4} ГБ, {:.4}%, \n\tСвободно: {:.4}ГБ\n',
        'no' : 'Диск {}, \n\topts: {}\n'
    },
    # pid, name, status, username, create_time
    'process': '{:<6}{:<40}{:<10}{:<30}{:<20}',
    'network': '\tотправлено: {}  MB, \n\tпринято: {} MB, \n\tотправлено пакетов: {}, \n\tпринято пакетов: {}'
}

#   Получение данных об оперативной памяти
def get_memory():
    res = {
        'all': psutil.virtual_memory().total / 1024 / 1024 / 1024,
        'used': psutil.virtual_memory().used / 1024 / 1024 / 1024,
        'free': psutil.virtual_memory().free / 1024 / 1024 / 1024,
        'total': psutil.swap_memory().total / 1024 / 1024 / 1024
    }
    return res

def get_disks():
    res = {
            'diskpart': {
                'device': [],
                'fstype': [],
                'opts': []
            },
            'usage': {}
        }
    for disk in psutil.disk_partitions():
        s = re.match(r'.*([:\\/]?[a-z|A-Z]+[:\\/]?).*', disk.device)
        s = s.group(1)
        res['diskpart']['device'].append(s)
        res['diskpart']['fstype'].append(disk.fstype)
        res['diskpart']['opts'].append(disk.opts)
    for i, disk in enumerate(res['diskpart']['device']):
        if res['diskpart']['fstype'][i] != '':
            res['usage'][disk] = {}
            res['usage'][disk]['total'] = psutil.disk_usage(path=disk).total / 1024 / 1024 / 1024
            res['usage'][disk]['used'] = psutil.disk_usage(disk).used / 1024 / 1024 / 1024
            res['usage'][disk]['free'] = psutil.disk_usage(disk).free / 1024 / 1024 / 1024
            res['usage'][disk]['percent'] = psutil.disk_usage(disk).percent
    return res

def get_process():
    res = {}
    for proc in psutil.process_iter():
        d = proc.as_dict(attrs=['pid', 'name', 'username', 'status', 'create_time'])
        d['create_time'] = time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(d['create_time']))
        if d['username'] == None:
            d['username'] = 'None'
        res[d['pid']] = {
            'name': d['name'],
            'username': d['username'],
            'status': d['status'],
            'create_time': d['create_time']
        }
    return res

def get_network():
    net = psutil.net_io_counters()
    res = {
            'bytes_sent': net.bytes_sent / 1024 / 1024,
            'bytes_recv': net.bytes_recv /1024 / 1024,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }
    return res

def show():
    #   Представление данных об оперативной памяти
    memory = get_memory()
    template_memory = ''
    for key in memory.keys():
        template_memory += TEMPLATES['memory'][key].format(memory[key])
    print(template_memory)
    # Представление данных по информации дискового пространства
    partitions = get_disks()
    for i in range(len(partitions['diskpart']['device'])):
        disk = partitions['diskpart']['device'][i]
        if partitions['diskpart']['fstype'][i] != '':
            part_str = TEMPLATES['disks']['yes'].format(disk, partitions['diskpart']['opts'][i], partitions['diskpart']['fstype'][i], partitions['usage'][disk]['total'], partitions['usage'][disk]['used'], partitions['usage'][disk]['percent'], partitions['usage'][disk]['free'])
        else:
            part_str = TEMPLATES['disks']['no'].format(disk, partitions['diskpart']['opts'][i])
        print(part_str)
    # Представление данных о процессах
    process = get_process()
    
    print('{:^6}{:^40}{:^10}{:^30}{:^20}'.format('pid', 'name', 'status', 'username', 'create_time'))
    print(' ' * 112)
    for i in process:
        proc_str = TEMPLATES['process'].format(i, process[i]['name'], process[i]['status'], process[i]['username'], process[i]['create_time'])
        print(proc_str)
    # Прдставление данных о сети
    network = get_network()
    print('\n\nСтатистика по сетевым данным:')
    net_str = TEMPLATES['network'].format(round(network['bytes_sent'], 2), round(network['bytes_recv'], 2), network['packets_sent'], network['packets_recv'])
    print(net_str)


if __name__ == "__main__":
    show()