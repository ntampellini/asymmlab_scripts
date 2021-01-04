import os
from cclib.io import ccread
from cclib.parser import utils

os.chdir(os.path.dirname(os.path.realpath(__file__)))
folder = os.listdir()
out = open('coordinates.txt', 'w')

pt = {
    1:'H',
    3:'Li',
    5:'B',
    6:'C',
    7:'N',
    8:'O',
    9:'F',
    13:'Al',
    14:'Si',
    15:'P',
    16:'S',
    17:'Cl',
    35:'Br'
    }

for f in folder:
    print('.')
    if f.endswith('.log'):
        data = ccread(f)
        name = f.split('.')[:-1][0]
        symbols = data.atomnos
        xyz = data.atomcoords[-1]
        energy = utils.convertor(data.scfenergies[-1], 'eV', 'hartree')

        out.write(str(name))
        out.write('\n')
        out.write('Energy (Hartree) = ')
        out.write(str(energy))
        out.write('\n')
        for atom in range(len(xyz)):
            x = str(xyz[atom][0]) if xyz[atom][0] < 0 else ' ' + str(xyz[atom][0])
            y = str(xyz[atom][1]) if xyz[atom][1] < 0 else ' ' + str(xyz[atom][1])
            z = str(xyz[atom][2]) if xyz[atom][2] < 0 else ' ' + str(xyz[atom][2])
            out.write('%-5s%-12s%-12s%-12s\n' % (pt[symbols[atom]], x, y, z))
        out.write('\n\n')