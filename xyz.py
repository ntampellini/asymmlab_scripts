#################################################################################

# Batch convert .log Gaussian files to .xyz format to open them with VMD.
# Creates a new ".xyz" directory in each path provided and generates an .xyz
# file for each .log found. Re-running the code updates the .xyz files 
# converting only .log files not already present in ".xyz" folder.

folders = [r'path1',
           r'path2',
           r'path3',
           r'path4']

safe = True #If True, checks .log convergence before writing relative .xyz file

#################################################################################

from cclib.io import ccread
import os
for d in folders:
    os.chdir(d)
    print(f'\n-----> Checking {d}')
    start = os.getcwd()
    folder = os.listdir()
    logs = []
    for f in folder:
        if f.endswith('.log') or f.endswith('.LOG'):
            if f.startswith('GS') or f.startswith('TS') or f.startswith('_TS'):
                logs.append(f)
    equilibrium_geometries = []
    atoms = []
    destination = os.path.join(os.getcwd(), '.xyz')
    if not os.path.exists(destination):
        os.mkdir('.xyz')
    os.chdir(destination)
    folder = os.listdir()
    names = [l[:-4] for l in logs]
    for f in folder:
        match = f[:-4] + '.log'
        if match in logs:
            logs.remove(match)
    if len(logs) == 0:
        print(f'-> No new files found in {d}')
    else:
        print(f'\n-> Found {len(logs)} new .log files, will start to turn them into .xyz files')
    periodic_table = {1:'H', 3:'Li', 6:'C', 7:'N', 8:'O', 9:'F', 16:'S'}
    fail = 0
    for l in logs:
        os.chdir(start)
        print(f'---> Reading file {logs.index(l)+1} out of {len(logs)} : {l}')
        data = ccread(l)
        if data is None:
            print(f'-> File {l} cannot be read with cclib. RIP')
            equilibrium_geometries.append([0])
            atoms.append([0])
            fail += 1
        else:
            if safe:
                try:
                    if data.optdone: #ccread doesn't yield .optdone if job is not an optimization (i.e. freq, SP)
                        equilibrium_geometries.append(data.atomcoords[-1])
                        atoms.append(data.atomnos)
                    else:
                        print(f'-> File {l} has not converged successfully. RIP')
                        equilibrium_geometries.append([0])
                        atoms.append([0])
                        fail += 1
                except:
                    print(f'-> Cannot tell if file {l} has converged successfully. Was the job an optimization? If it was, probably another error occurred.')
                    # This most likely means that data has no attribute optdone, as said before.
                    equilibrium_geometries.append([0])
                    atoms.append([0])
                    fail += 1
            else:
                equilibrium_geometries.append(data.atomcoords[-1])
                atoms.append(data.atomnos)
    for n in range(len(logs)):
        title = logs[n][:-4] + ".xyz"
        a = len(equilibrium_geometries[n])
        if len(atoms[n]) > 1:
            os.chdir(destination)
            with open(title, 'w') as f:
                f.write(f'{a}\n\n')
                for atom in range(len(atoms[n])):
                    f.write(f' {periodic_table[atoms[n][atom]]}\t\t{equilibrium_geometries[n][atom][0]}\t{equilibrium_geometries[n][atom][1]}\t{equilibrium_geometries[n][atom][2]}\n')
                f.write("\n")
    if len(logs) != 0:
        print(f'-> Wrote {len(logs)- fail}/{len(logs)} .xyz files to {destination}')