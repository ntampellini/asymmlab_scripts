###############################################################################################################

# Automatizes the use of Goodvibes frequency analysis and writes/prints a table with product distribution

dirs = [r'path1',                          # List of working directories, can also be just one. 
        r'path2',
        r'path3',
        r'path4']

group = 2                                  # Graphically group 2 or more molecules, sorted alphabetically
vibes = True                               # If True, computes goodvibes frequency analysis and then prints
                                           # results, if False only prints results
flag = 'very_important_molecule_*.log'     # Flag used for goodvibes calculation

goodvibes_command = f'python -m goodvibes .\{flag} -q --cpu --freespace toluene'

# For Goodvibes command syntax, check project's repository at:
# https://github.com/bobbypaton/GoodVibes

###############################################################################################################
import os
import numpy as np
for directory in dirs:
    os.chdir(directory)
    title = directory.split("\\")[-1]
    t = 'Goodvibes_' + title + '.dat'
    goodvibes_command = goodvibes_command + ' --output ' + title + ' --check'
    if vibes:
        if os.path.exists(t):
            os.remove(t)
        os.system(goodvibes_command)
    with open(t, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            if '   Structure                                           E' in line:
                flag = True
                N = []
                E = []
                ZPEs = []
                H = []
                G = []
                line = f.readline()
                while flag:
                    line = f.readline()
                    if '   *********************' in line:
                        flag = False
                    else:
                        string = line.split()
                        name = string[1]
                        Energy = string[2]
                        ZPE = string[3]
                        qhH = string[5]
                        qhG = string[9]
                        N.append(name)
                        ZPEs.append(float(ZPE))
                        E.append(float(Energy))
                        H.append(float(qhH))
                        G.append(float(qhG))
    
    min_E = min(E)
    rel_E = [(e - min_E)*627.50961 for e in E]
    boltz_E = [np.exp(-E*4184/(8.314*(273.15+25))) for E in rel_E]
    sum_boltz_E = sum(boltz_E)
    distribution_E = [round(i/sum_boltz_E*100, 2) for i in boltz_E]

    min_ZPEs = min(ZPEs)
    rel_ZPEs = [(Z - min_ZPEs)*627.50961 for Z in ZPEs]
    boltz_ZPEs = [np.exp(-ZPEs*4184/(8.314*(273.15+25))) for ZPEs in rel_ZPEs]
    sum_boltz_ZPEs = sum(boltz_ZPEs)
    distribution_ZPEs = [round(i/sum_boltz_ZPEs*100, 2) for i in boltz_ZPEs]
    
    min_G = min(G)
    rel_G = [(g - min_G)*627.50961 for g in G]
    boltz_G = [np.exp(-g*4184/(8.314*(273.15+25))) for g in rel_G]
    sum_boltz_G = sum(boltz_G)
    distribution_G = [round(i/sum_boltz_G*100, 2) for i in boltz_G]

    min_H = min(H)
    rel_H = [(h - min_H)*627.50961 for h in H]
    boltz_H = [np.exp(-h*4184/(8.314*(273.15+25))) for h in rel_H]
    sum_boltz_H = sum(boltz_H)
    distribution_H = [round(i/sum_boltz_H*100, 2) for i in boltz_H]

    f = open('Goodvibes_' + title + '_results.txt', 'w')

    def fprint(string):
        if type(string) is str:
            print(string)
            string += '\n'
            f.write(string)
        elif type(string) is list:
            print(''.join(string))
            string.append('\n')
            for s in string:
                f.write(s)

    
    longest_name = max([len(n) for n in N])

    fprint(f'''Thermodynamic corrections obtained from Goodvibes, processed through Python script.\nGoodbye Excel.\n\nGoodvibes command used was:\n 
    {goodvibes_command}\n\nIt processed {len(G)} files.''')

    fprint(f'\n\n\n-----> ELECTRONIC ENERGY - EE')
    fprint([f'\nName', ' '*(longest_name + 1), 'EE         Prod. Dist.     Cum. Ab.'])
    fprint('*'*(longest_name + 41))
    for i in range(len(N)):
        a = '\n' if i % group == group - 1 else ''
        cum = f'{round(sum(distribution_E[i:i+group]), 2)} %' if i % group == 0 and i+group-1 != len(N) else ''
        fprint('%s %s %-10s %-5s %s %s %s' % (N[i], ' '*((longest_name + 3) - len(N[i])), '+'+str(round(rel_E[i], 2)), distribution_E[i], ' %\t', cum, a))
    fprint('*'*(longest_name + 41))

    fprint(f'\n\n\n-----> ENTHALPY - H')
    fprint([f'\nName', ' '*(longest_name + 1), 'qh-H       Prod. Dist.     Cum. Ab.'])
    fprint('*'*(longest_name + 41))
    for i in range(len(N)):
        a = '\n' if i % group == group - 1 else ''
        cum = f'{round(sum(distribution_H[i:i+group]), 2)} %' if i % group == 0 and i+group-1 != len(N) else ''
        fprint('%s %s %-10s %-5s %s %s %s' % (N[i], ' '*((longest_name + 3) - len(N[i])), '+'+str(round(rel_H[i], 2)), distribution_H[i], ' %\t', cum, a))
    fprint('*'*(longest_name + 41))

    fprint(f'\n\n\n-----> FREE ENERGY - G')
    fprint([f'\nName', ' '*(longest_name + 1), 'qh-G       Prod. Dist.     Cum. Ab.'])
    fprint('*'*(longest_name + 41))
    for i in range(len(N)):
        a = '\n' if i % group == group - 1 else ''
        cum = f'{round(sum(distribution_G[i:i+group]), 2)} %' if i % group == 0 and i+group-1 != len(N) else ''
        fprint('%s %s %-10s %-5s %s %s %s' % (N[i], ' '*((longest_name + 3) - len(N[i])), '+'+str(round(rel_G[i], 2)), distribution_G[i], ' %\t', cum, a))
    fprint('*'*(longest_name + 41))

    fprint(f'\n\n\n-----> ALL RESULTS')
    fprint([f'\nName', ' '*(longest_name + 1), 'EE_dist     qh-H_dist    qh-G_dist'])
    fprint('*'*(longest_name + 41))
    for i in range(len(N)):
        a = '\n' if i % group == group - 1 else ''
        fprint('%s %s %-5s %-5s %-5s %-6s %-5s %-5s %-5s' % (N[i], ' '*((longest_name + 3) - len(N[i])), distribution_E[i], ' %', distribution_H[i], ' %', distribution_G[i], ' %', a))
    fprint('*'*(longest_name + 41))
