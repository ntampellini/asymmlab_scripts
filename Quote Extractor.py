# Put this file in a directory to write a .txt file containing all quotes for .log Gaussian
# jobs files contained in every folder/subfolder.

import os
os.chdir(os.path.dirname(os.path.realpath(__file__)))
queue=[]
for root, dirs, files in os.walk(os.getcwd()):
    for name in files:
        if name.endswith((".LOG", ".log")):
            queue.append(os.path.join(root, name))
print(f'Found {len(queue)} Gaussian .log files')
bank = {}
num=0
for i in range(len(queue)):
    bank[i]=''
    with open(queue[i], 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            elif "@" in line:
                quote=[]
                line = f.readline()
                line = f.readline()
                flag=True
                while flag:
                    line = f.readline()
                    if "Job cpu" in line:
                        flag=False
                    else:
                        quote.append(line)
                bank[i]=quote
                num+=1
                print(f'{num} quotes found')
if os.path.exists('GaussianQuotes.txt'):
    os.remove('GaussianQuotes.txt') 
book=open('GaussianQuotes.txt','a')
print('Writing...')
for i in range(len(list(bank))):
    book.write('______________________________________________________________________________________________________________\n')
    for j in range(len(bank[list(bank)[i]])):
        book.write(bank[i][j])
        book.write('\n')
book.write('______________________________________________________________________________________________________________\n')
book.write(f'Total: {num} quotes')
book.close()