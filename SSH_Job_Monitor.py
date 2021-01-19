######################################################
#  Automatically check servers for Gaussian
#  jobs, either of current user in credentials.py 
#  and of all users in other_users list.

server_list = [
            #    35,
            #    37,
               39,
               40
               ]
               
root = '192.168.111'
print_cpu_usage = True
color = 'light_yellow'
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
users = [username] + other_users
extensive = False
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
yellowline = '%s----------------------------------------------------------------------------------------------------------------------%s' % (fg(color), fg(255))

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
                    stdin, stdout, stderr = ssh_client.exec_command(f'ps -u {name} -f')
                    stdout_lines = stdout.readlines()
                    # if name == 'user':
                    #     pprint(stdout_lines)
                    #     quit()
                    
                    output.append(stdout_lines)
                    if name == username:                                  # for now only checks queue by main user, but multi-queue control can be implemented in the future.
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
                            q_name_list = [q.split('/')[-1].strip('\n') for q in q_list]
                            j_name = j_list[0].split('/')[-1].strip('\n')
                            if j_name in q_name_list:
                                index = q_name_list.index(j_name) + 1
                                pending = len(q_list) - index
                                for q_path in q_list:              # remove job from pending list if it is running
                                    if j_name in q_path:
                                        q_list.remove(q_path)
                                        break
                        else:
                            pending = len(q_list)
                        if pending > 0:
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
                            PIDS.append(output[user][line].split()[1])
                            times.append(output[user][line].split()[6])
                            names.append(output[user][line].split()[9].strip('.chk'))
                            owner.append(users[user])
                ################################################################################## END OF CHECK, START OF PRINT
                s = 's' if len(PIDS) != 1 else ''
                print('\n%s---> %s%sServer %s%s%s : %s job%s running, %s pending in queue\n' % (fg(255), fg(color), attr('bold'), server.split('.')[-1], fg(255), attr('reset'), len(PIDS), s, pending))
                if cpu_mem_data:
                    print(f'CPU usage: {cpu_mem_data[0]} %')
                    print(f'RAM usage: {round(100 * (float(cpu_mem_data[1][0]) - float(cpu_mem_data[1][1])) / float(cpu_mem_data[1][0]), 1)} % - {round(float(cpu_mem_data[1][1]) / 1000, 1)} GB free / {round(float(cpu_mem_data[1][0]) / 1000, 1)} GB total')
                if len(PIDS) > 0:
                    print('\nRUNNING:\n')
                    longest_name_len = max([len(names[index][:-4]) for index in range(len(PIDS))])
                    for PID in range(len(PIDS)):
                        index = PIDS.index(PIDS[PID])
                        cputime_h = times[PID].split(':')[0]
                        cputime_m = times[PID].split(':')[1]
                        if '-' in cputime_h:
                            _time = cputime_h.split('-')
                            cputime_h = int(_time[1]) + float(cputime_m) / 60
                            days = int(_time[0])
                        else:
                            cputime_h = int(cputime_h)
                            cputime_h += float(cputime_m) / 60
                            days = None
                        runtime = round(days + cputime_h / 24, 2) if days else round(cputime_h, 2)
                        runtime2 = 'days' if days else 'hours'
                        # clock = time.ctime(time.time()).split()[3]
                        space = ' '*(longest_name_len - len(names[PID][:-4]))
                        c1 = fg(color) if owner[PID] == username else fg(255)
                        c2 = fg(255)
                        print('   %s%-5s%s - %s%s - CPU Time : %s %s' % (c1, owner[PID], c2, names[PID], space, runtime, runtime2))
                        
                if pending:
                    print(f'\nQUEUE ({username}):\n')
                    l = len(pending_list)
                    if l > 10 and not extensive:
                        for p in range(2):
                            p_name = pending_list[p].split('/')[-1].strip('\n').strip('.gjf')
                            p_owner = pending_list[p].split('/')[3]
                            print('   %-3s - %s%s%s - %s' % (p+1, fg(color), p_owner, fg(255), p_name))
                        print('         ...')
                        for p in [l-3, l-2, l-1]:
                            p_name = pending_list[p].split('/')[-1].strip('\n').strip('.gjf')
                            p_owner = pending_list[p].split('/')[3]
                            print('   %-3s - %s%s%s - %s' % (p+1, fg(color), p_owner, fg(255), p_name))
                    else:
                        for p in range(l):
                            p_name = pending_list[p].split('/')[-1].strip('\n').strip('.gjf')
                            p_owner = pending_list[p].split('/')[3]
                            print('   %-3s - %s%s%s - %s' % (p+1, fg(color), p_owner, fg(255), p_name))
                print(yellowline)
            inp = input('\n%s--> Finished. Press Enter to refresh or insert server number to check status. - ' % (fg(245)))
        try:
            while True:
                if int(inp) in server_list:
                    os.system('cls')
                    print('\n%s---> %s%sServer %s%s%s : job status\n' % (fg(255), fg(color), attr('bold'), inp, fg(255), attr('reset')))
                    print('\n'.join(qs(inp)))
                    inp = input('\n%s--> Finished. Press Enter to restart or insert server number to check status. - ' % (fg(245)))
        except Exception as e:
            if e is not ValueError:
                print(e)
                input('\n%sSomething went wrong. Oops.%s' % (fg(245), fg(255)))
            pass
        extensive = True if inp == 'e' else False
        os.system('cls')