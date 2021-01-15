###########################################################
#  Extracts atom coordinates from all readable .log,
#  .pdb, .xyz, etc. files in folder and writes them to
#  a 'coordinates.txt' file. When available, electronic
#  energy is also included before coordinates. Move this
#  file to the desired folder or change working directory
#  at line 15.
###########################################################
import os
from cclib.io import ccread
from cclib.parser import utils
from periodictable import elements

os.chdir(os.path.dirname(os.path.realpath(__file__)))
# os.chdir(r'yourpath')
folder = os.listdir()
out = open('coordinates.txt', 'w')

pt = {el.number:el.symbol for el in elements}

for f in folder:
    if f.endswith('.log'):
        print('Extracting', f)
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