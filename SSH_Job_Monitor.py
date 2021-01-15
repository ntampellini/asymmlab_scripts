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
######################################################
from SSH_credentials import *
from colored import fg, bg, attr
import time
import paramiko
import copy
import sys
import os
import re
ip_list = [root + '.' + str(ip) for ip in server_list]
users = other_users + [username]
extensive = False
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def qs(server):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(root + '.' + server, username=username, password=password)

    channel = ssh_client.invoke_shell()

    channel_data = bytes()

    first = True

    while True:
        if channel.recv_ready():
            channel_data += channel.recv(9999)
            if not first:
                data = channel_data.decode('utf-8').split('\n')
                data = [str(line).replace('\x1b', '').replace('\x00', '') for line in data]
                data = [re.sub('\[.', '', line) for line in data if line not in ('', 'qs\r', 'y\r')]
                for line in data:
                    if 'View complete list of pending jobs?' in line:
                        data.remove(line)
                    if 'List all steps of running job?' in line:
                        data.remove(line)
                    if '~]$' in line:
                        data.remove(line)
            if first:
                channel.send('qs\n')
                time.sleep(0.5)
                channel.send('n')    # list all jobs in queue?
                time.sleep(0.5)
                channel.send('y')    # list current job status?
                time.sleep(0.5)
                channel.send('y')    # list current job opt steps?
                time.sleep(0.5)

                first = False
            else:
                return data[3:]
        else:
            continue

if __name__ == '__main__':
    inp = ''
    while True:
        if inp not in server_list:
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
                    if l > 100 and not extensive:
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
                print('%s----------------------------------------------------------------------------------------------------------------------' % (fg('light_yellow')))
            inp = input('\n%s--> Finished. Press Enter to refresh or insert server number to check status. - ' % (fg(245)))
        try:
            if int(inp) in server_list:
                os.system('cls')
                print('\n%s---> %s%sServer %s%s%s : job status\n' % (fg('white'), fg('light_yellow'), attr('bold'), inp, fg('white'), attr('reset')))
                print('\n'.join(qs(inp)))
                inp = input('\n%s--> Finished. Press Enter to restart.' % (fg(245)))
        except Exception as e:
            print(e)
            input('\n%sSomething went wrong. Oops.' % (fg(245)))
        extensive = True if inp == 'e' else False
        os.system('cls')