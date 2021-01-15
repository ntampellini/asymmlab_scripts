#########################################################
#  Extracts .xyz coordinates files from Spartan '14
#  project files ('.spartan' extension). Move this file 
#  to the folder containing the projects and run it or 
#  set the working directory from line 14.
#########################################################

import os
import re
import gzip
import olefile

os.chdir(os.path.dirname(os.path.realpath(__file__)))
# os.chdir(r'yourpath')

def spartan_extract_xyz(spartan_file):
    count = 0
    def _nextline(byte_object):
        return byte_object.readline().decode().strip('\r\n')
    if not spartan_file.endswith('.spartan'):
        return None
    else:
        print('\nProcessing file', spartan_file)
        with olefile.OleFileIO(spartan_file, 'rb') as ole:
            molecules_list = []
            for path in ole.listdir():
                if path[0] == 'Molecules' and path[2] == 'Input.gz':
                   molecules_list.append(path[1])
            for mol in molecules_list:
                print(f'--> Extracting molecule {molecules_list.index(mol) + 1}/{len(molecules_list)}')
                inner = ole.openstream(['Molecules', mol, 'Input.gz'])
                with gzip.open(inner, 'rb') as inp:
                    xyz = []
                    labels = []
                    line = _nextline(inp)
                    line = _nextline(inp)
                    line = _nextline(inp)
                    line = _nextline(inp)
                    while line != 'ENDCART':
                        xyz.append(line)
                        line = _nextline(inp)
                    line = _nextline(inp)
                    line = _nextline(inp)
                    while line != 'ENDATOMLABELS':
                        labels.append(line)
                        line = _nextline(inp)
                    if not line or len(xyz) != len(labels):
                        raise Exception('Something went wrong')
                    filename = spartan_file.strip('.spartan')
                    with open(f'{filename}_{count}.xyz', 'w') as x:
                        x.write(str(len(xyz)) + '\n' + mol + '\n')
                        for atom in range(len(xyz)):
                            coordinates = xyz[atom].split()
                            label = re.sub(r'(\d+)', r' \1', labels[atom][1:-1]).split()[0]  # 'Br234' -> 'Br 234' -> 'Br'
                            x_pos = coordinates[1] if float(coordinates[1]) < 0 else ' ' + coordinates[1]
                            y_pos = coordinates[2] if float(coordinates[2]) < 0 else ' ' + coordinates[2]
                            z_pos = coordinates[3] if float(coordinates[3]) < 0 else ' ' + coordinates[3]
                            x.write('%-5s%-15s%-15s%-15s\n' % (label, x_pos, y_pos, z_pos))
                    count += 1

for f in os.listdir():
    spartan_extract_xyz(f)
input('\nDone.')