######################################################
#  Automatically check servers for Gaussian
#  jobs, either of current user in credentials.py 
#  and of all users in other_users list.

server_list = [
               35,
               37,
               39,
               40
               ]
               
root = '192.168.111'
print_cpu_usage = True
######################################################
from SSH_credentials import *
from colored import fg, bg, attr
import time
import paramiko
import copy
import sys
import os
import re
from pprint import pprint
ip_list = [root + '.' + str(ip) for ip in server_list]
users = other_users + [username]
extensive = False
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
yellowline = '%s----------------------------------------------------------------------------------------------------------------------%s' % (fg('light_yellow'), fg('white'))

def qs(server):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ssh_client.connect(root + '.' + str(server), username=username, password=password)

    channel = ssh_client.invoke_shell()

    channel_data = bytes()

    first = True
    empty = True

    while True:
        if channel.recv_ready():
            channel_data += channel.recv(9999)
            sample = channel_data.decode('utf-8')
            # pprint(sample)
            if len(sample.split('\n')) > 5:
                empty = False
            if not empty:
                data_1 = channel_data.decode('utf-8').split('\r\n')
                data_2 = [str(line).replace('\x1b', '').replace('\x00', '') for line in data_1]
                data_3 = [re.sub('\[.', '', line) for line in data_2 if line not in ('', '\r', 'qs\r', 'y\r', 'qs', '3')]
                for line in data_3:
                    if '@' in line:
                        data_3.remove(line)
                    elif line.startswith('3'):
                        data_3[data_3.index(line)] = line[1:]
                    elif 'The queue has' in line:
                        n = data_3.index(line)
                        data_3.insert(n - 1, yellowline)
                        for _ in range(14):              # chewing unuseful output
                            data_3.remove(data_3[n + 2])
                        data_3.insert(n + 2, 'Current job detailed status:\n')
                        break
                return data_3[3:]
            if first:
                channel.send('qs\n')
                time.sleep(0.5)
                channel.send('3')    # list all steps of current job
                time.sleep(0.5)
                first = False
        else:
            continue

def cpu():
    # ssh_client = paramiko.SSHClient()
    # ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # ssh_client.connect(root + '.' + str(server), username=username, password=password)

    channel = ssh_client.invoke_shell()

    channel_data = bytes()

    empty = True
    first = True
    count = 0     #abort request if stuck
    
    while True:
        if channel.recv_ready():
            channel_data += channel.recv(9999)
            sample = channel_data.decode('utf-8')
            # pprint(sample)
            if '%Cpu(s)' in sample:
                empty = False
            if not empty:
                data = channel_data.decode('utf-8').split('\n')
                data = [str(line).replace(r'\x1b', '').replace(r'\x00', '').replace(r'\x0f', '') for line in data]
                data = [re.sub(r'\[.', '', line) for line in data if line not in ('', r'qs\r', r'y\r')]
                for line in range(len(data)):
                    if '%Cpu(s)' in data[line]:
                        cpuline = line
                        break
                cpu_usage = data[cpuline].split()[1]
                memory = [data[cpuline+1].split()[3], data[cpuline+1].split()[5], data[cpuline+1].split()[7], data[cpuline+1].split()[9]] # total, free, used, buff/cache
                ssh_client.close()
                return (cpu_usage, memory)
            if empty:
                if first:
                    channel.send('top\n')
                    channel.send('q')
                    first = False
                time.sleep(0.5)
                count += 1
            if count == 10:
                return None
        else:
            continue


if __name__ == '__main__':
    inp = ''
    while True:
        if inp == '' or int(inp) not in server_list:
            for server in ip_list:
                ssh_client.connect(server, username=username, password=password)
                output = []
                for name in users:
                    stdin, stdout, stderr = ssh_client.exec_command(f'ps -u {name} all')
                    output.append(stdout.readlines())

                    queue = os.path.join(os.getcwd() + '\\queue')
                    job = os.path.join(os.getcwd() + '\\job')

                    ftp_client=ssh_client.open_sftp()
                    try:
                        ftp_client.get(f'/home/{name}/wdir/running.queue', queue)
                        ftp_client.get(f'/home/{name}/wdir/running.job', job)
                    except:
                        q = open(queue, 'w')
                        j = open(job, 'w')
                    ftp_client.close()

                    q = open(queue, 'r')
                    j = open(job, 'r')
                    q_list = q.readlines()
                    j_list = j.readlines()
                    pending = 0
                
                    if len(j_list) == 1:
                        try:
                            pending = len(q_list) - q_list.index(j_list[0]) - 1
                        except:
                            pending = len(q_list)                                # to prevent crash if running job name is not in q_list, seem to work fine
                    pending_print = False
                    if pending > 0:
                        pending_print = True
                        pending_list = []
                        for p in range(pending):
                            try:
                                pending_list.append(q_list[1 + q_list.index(j_list[0]) + p])
                            except:
                                pending_list.append(q_list[p])                   # to prevent crash if running job name is not in q_list, seem to work fine
                    q.close()
                    j.close()
                    os.remove(queue)
                    os.remove(job)

                
                cpu_mem_data = cpu() if print_cpu_usage else None
                



                ssh_client.close()

                PIDS, times, names, owner = [], [], [], []
                for user in range(len(users)):
                    for line in range(len(output[user])):
                        if re.findall('/g16/g16/...', output[user][line]):
                            PIDS.append(output[user][line].split()[2])
                            times.append(output[user][line].split()[11])
                            names.append(output[user][line].split()[14].split('/')[-1])
                            owner.append(users[user])
                ################################################################################## END OF CHECK, START OF PRINT
                s = 's' if len(PIDS) != 1 else ''
                print('\n%s---> %s%sServer %s%s%s : %s job%s running, %s pending in queue\n' % (fg('white'), fg('light_yellow'), attr('bold'), server.split('.')[-1], fg('white'), attr('reset'), len(PIDS), s, pending))
                if cpu_mem_data:
                    print(f'CPU usage: {cpu_mem_data[0]} %')
                    print(f'RAM usage: {round(100 * (float(cpu_mem_data[1][0]) - float(cpu_mem_data[1][1])) / float(cpu_mem_data[1][0]), 1)} % - {round(float(cpu_mem_data[1][1]) / 1000, 1)} GB free / {round(float(cpu_mem_data[1][0]) / 1000, 1)} GB total')
                if len(PIDS) > 0:
                    print('\nRUNNING:\n')
                    longest_name_len = max([len(names[index][:-4]) for index in range(len(PIDS))])
                    for PID in range(len(PIDS)):
                        index = PIDS.index(PIDS[PID])
                        cputime = int(times[PID].split(':')[0]) / 60
                        runtime = round(cputime/24, 2) if cputime > 24 else round(cputime, 2)
                        runtime2 = 'days' if cputime > 24 else 'hours'
                        clock = time.ctime(time.time()).split()[3]
                        space = ' '*(longest_name_len - len(names[PID][:-4]))
                        print('   %-5s - %s%s - CPU Time : %s %s' % (owner[PID], names[PID][:-4], space, runtime, runtime2))
                        
                if pending_print:
                    print('\nQUEUE:\n')
                    l = len(pending_list)
                    if l > 10 and not extensive:
                        for p in range(2):
                            pp = pending_list[p].split('/')[-1][:-1]
                            print('   %-3s - %s' % (p+1, pp))
                        print('         ...')
                        for p in [l-3, l-2, l-1]:
                            pp = pending_list[p].split('/')[-1][:-1]
                            print('   %-3s - %s' % (p+1, pp))
                    else:
                        for p in range(l):
                            pp = pending_list[p].split('/')[-1][:-1]
                            print('   %-3s - %s' % (p+1, pp))
                print(yellowline)
            inp = input('\n%s--> Finished. Press Enter to refresh or insert server number to check status. - ' % (fg(245)))
        try:
            while True:
                if int(inp) in server_list:
                    os.system('cls')
                    print('\n%s---> %s%sServer %s%s%s : job status\n' % (fg('white'), fg('light_yellow'), attr('bold'), inp, fg('white'), attr('reset')))
                    print('\n'.join(qs(inp)))
                    inp = input('\n%s--> Finished. Press Enter to restart or insert server number to check status. - ' % (fg(245)))
        except Exception as e:
            if e is not ValueError:
                print(e)
                input('\n%sSomething went wrong. Oops.%s' % (fg(245), fg('white')))
            pass
        extensive = True if inp == 'e' else False
        os.system('cls')