#################################################################

# Analyzes a series of conformers that start and end with the 
# provided extension, and returns a table with name,
# relative energy in desired units, and atomic position RMSD 
# relative to lowest energy conformer, in Angstroms.


path = r'path_to_working_directory'
start = 'very_important_molecule_conformer_'
end = '.log'

units = 'kcal/mol'         # eV, kj/mol, hartree, wavenumber
write = False              # Writes a .txt file with console output
print_table = True         # prints results to terminal

#################################################################

import os
from cclib.io import ccread
from cclib.parser import utils
from spyrmsd import rmsd
import numpy as np

def conformer_analysis(path, start, end='.log', write=False, print_table=False):
    print_list = []
    os.chdir(path)
    confs = []
    for f in os.listdir():
            if f.startswith(start) and f.endswith(end):
                    confs.append(f)
    database = []
    energies = []
    if print_table:
        print('\nComputing...\n')
    for c in confs:
        data = ccread(c)
        atoms = data.atomnos
        xyz = data.atomcoords[-1]
        database.append([xyz, atoms])
        energy_kcal = utils.convertor(data.scfenergies[-1], 'eV', units)
        energies.append(energy_kcal)

    min_E = min(energies)
    rel_E = [(e - min_E) for e in energies]
    boltz_E = [np.exp(-E*4184/(8.314*(273.15+25))) for E in rel_E]
    sum_boltz_E = sum(boltz_E)
    distribution_E = [round(i/sum_boltz_E*100, 2) for i in boltz_E]

    def _energy(table_row):
        return table_row[1]

    #sort everything
    table = [[confs[i], rel_E[i], distribution_E[i], database[i]] for i in range(len(energies))]
    table.sort(key=_energy)

    ref = [table[0][3][0], table[0][3][1]] #xyz and atoms of reference structure for rmsd calc
    for e in range(len(database)):
        rms = rmsd.rmsd(ref[0], table[e][3][0], ref[1], table[e][3][1], center=True, minimize=True)
        table[e].append(rms)

    # print(ref)

    def fprint(string):
        if write:
            f.write(''.join(string))
            f.write('\n')
        # print(string)
        print_list.append(string)

    if write:
        title = path.split("\\")[-1] + '_Conformer_Analysis.txt'
        if os.path.exists(title):
            os.remove(title)
        f = open(title, 'w')

    longest_name = max([len(c) for c in confs])

    fprint(f'\nName' + ' '*(longest_name + 1) + 'rel_EE     Dist.       RMSD')
    fprint('*'*(longest_name + 34))
    for e in range(len(energies)):
        fprint('%s %s %-10s %-5s %-5s %-5s' % (table[e][0], ' '*((longest_name + 3) - len(table[e][0])), round(table[e][1], 3), table[e][2], ' %', round(table[e][4], 3)))
    fprint('*'*(longest_name + 34))
    if print_table:
        print('\n'.join(print_list))
    return table

conformer_analysis(path, start, end, write=write, print_table=print_table)