###############################################################################################################
# Automates the use of Goodvibes frequency analysis corrections computed on a lower level (opt_freq_method)
# to a higher level single-point energy calculation (sp_method) and outputs a table with product distribution

opt_freq =           r'path_to_lower_level_opt+freq_calculations'
sp =                 r'path_to_high_level_SPE_calculations'
opt_freq_method =    'wB97X-D/6-31G(d)'
sp_method =          'wB97X-D/Def2TZVPP'
number_of_letters =  7

# For name comparison - es. for comparing two sets of molecules named 'conf_*_method1' and 
# 'conf_*_method2' with * being a number, the comparison should be done with the first 6 characters,
# so that the names of pairs of molecules, when trimmed to the first 6 characters, are identical.
# This allows the pairing of 'conf_1_method1' with 'conf_1_method2' and so on.
###############################################################################################################

import os
import numpy as np
from cclib.io import ccread

os.chdir(opt_freq)
folder = os.listdir()
dat = []
for f in folder:
    if f.endswith('.dat'):
        dat.append(f)
if len(dat) != 1:
    raise Exception(f'Goodvibes output (.dat) are more than one or are not present in {opt_freq}.')

with open(dat[0], 'r') as f:
    while True:
        line = f.readline()
        if not line:
            break
        if '   Structure                                           E' in line:
            flag = True
            N = []
            E = []
            H = []
            qhH = []
            TqhS = []
            line = f.readline()
            while flag:
                line = f.readline()
                if '   *********************' in line:
                    flag = False
                else:
                    string = line.split()
                    N.append(string[1])
                    E.append(float(string[2]))
                    H.append(float(string[4]))
                    qhH.append(float(string[5]))
                    TqhS.append(float(string[7]))

H_corrections = [qhH[i]-H[i] for i in range(len(H))]
n = [name[:number_of_letters] for name in N]
os.chdir(sp)
folder = os.listdir()
log = []
hybrid_names = []
for f in folder:
    if f.endswith('.log'):
        log.append(f)
for l in log:
    if l[:number_of_letters] in n:
        hybrid_names.append(l)

if len(hybrid_names) != len(n):
    raise Exception(f'There are {len(hybrid_names)} files in {sp} but {len(n)} files in {opt_freq}, cannot proceed. Tune file names or number_of_letters variable.')

sp_E = []
for l in hybrid_names:
    sp_E.append(ccread(l).scfenergies[-1]/27.211399) #correcting for cclib that converts to eV ._.

zipped = zip(sp_E, H_corrections)
hybrid_H = [e + hc for e, hc in zipped]

zipped = zip(hybrid_H, TqhS)
hybrid_G = [h + tqs for h, tqs in zipped]
    
# print(H_corrections)
# print(TqhS)
# print(E)
# print(sp_E)
# print(hybrid_H)
# print(hybrid_G)

min_E = min(sp_E)
rel_E = [(h - min_E)*627.50961 for h in sp_E]
boltz_E = [np.exp(-h*4184/(8.314*(273.15+25))) for h in rel_E]
sum_boltz_E = sum(boltz_E)
distribution_E = [round(i/sum_boltz_E*100, 2) for i in boltz_E]

min_H = min(hybrid_H)
rel_H = [(h - min_H)*627.50961 for h in hybrid_H]
boltz_H = [np.exp(-h*4184/(8.314*(273.15+25))) for h in rel_H]
sum_boltz_H = sum(boltz_H)
distribution_H = [round(i/sum_boltz_H*100, 2) for i in boltz_H]

min_G = min(hybrid_G)
rel_G = [(h - min_G)*627.50961 for h in hybrid_G]
boltz_G = [np.exp(-h*4184/(8.314*(273.15+25))) for h in rel_G]
sum_boltz_G = sum(boltz_G)
distribution_G = [round(i/sum_boltz_G*100, 2) for i in boltz_G]

txtname = 'Hybrid_Goodvibes_' + sp_method + '_' + opt_freq_method + '_results.txt'
f = open(txtname.replace('/','_'), 'w')

def fprint(string):
    print(string)
    string += '\n'
    f.write(string)

fprint(f'''Calculated energies obtained from single-point calculations at {sp_method} level,
while thermodynamic corrections at {opt_freq_method} level were obtained from Goodvibes.\nPython script by Nicolò Tampellini.\n
Goodbye Excel.\n\n''')

fprint(f'\n\n\n-----> SP Electronic Energy - sp_EE : {sp_method} level, no corrections')
fprint(f'\nName\t\t\t\tsp_EE\t  Prod. Dist.\t Cum. Ab.')
fprint('*********************************************************************')
for i in range(len(N)):
    a = '\n' if i % 2 == 1 else ''
    cum = f'{round(distribution_E[i] + distribution_E[i+1], 2)} %' if i % 2 == 0 and i+1 != len(N) else ''
    fprint('%-30s %-10s %-5s %s %s %s' % (n[i], '+'+str(round(rel_H[i], 2)), distribution_E[i], ' %\t', cum, a))
fprint('*********************************************************************')

fprint(f'\n\n\n-----> Hybrid ENTHALPY - H : {sp_method}//{opt_freq_method} levels')
fprint(f'\nName\t\t\t\thyb_H\t  Prod. Dist.\t Cum. Ab.')
fprint('*********************************************************************')
for i in range(len(N)):
    a = '\n' if i % 2 == 1 else ''
    cum = f'{round(distribution_H[i] + distribution_H[i+1], 2)} %' if i % 2 == 0 and i+1 != len(N) else ''
    fprint('%-30s %-10s %-5s %s %s %s' % (n[i], '+'+str(round(rel_H[i], 2)), distribution_H[i], ' %\t', cum, a))
fprint('*********************************************************************')

fprint(f'\n\n\n-----> Hybrid FREE ENERGY - G : {sp_method}//{opt_freq_method} levels')
fprint(f'\nName\t\t\t\thyb_G\t  Prod. Dist.\t Cum. Ab.')
fprint('*********************************************************************')
for i in range(len(N)):
    a = '\n' if i % 2 == 1 else ''
    cum = f'{round(distribution_G[i] + distribution_G[i+1], 2)} %' if i % 2 == 0 and i+1 != len(N) else ''
    fprint('%-30s %-10s %-5s %s %s %s' % (n[i], '+'+str(round(rel_G[i], 2)), distribution_G[i], ' %\t', cum, a))
fprint('*********************************************************************')