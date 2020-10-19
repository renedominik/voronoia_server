#!/usr/bin/python

import numpy as np
from scipy import ndimage
import random
import sys
import os

args = sys.argv
out = args[1]
filename = args[2]

atomslist_allpdb=[]
holenumbers=[]
holes={}
involved_residues={}
with open( os.path.join(out, filename), 'r') as fp:
    for line in fp:
        if line.startswith('LENGTH'):
            maxatoms=int(line.split()[5])
            holenumbers = [0] * (maxatoms+1)
            atomslist_allpdb = [0] * (maxatoms+1)
        elif line.startswith('HOLE NUMBER'):
            line=line.split('HOLE NUMBER')[1]
            lines=line.split()
            holes[int(lines[0])]=lines[1:]
            for num in lines[1:]:
                holenumbers[int(num)]=1
        #print(holenumbers)
        if line.startswith('ATOM') or line.startswith('HETATM'):
            if holenumbers[int(line[6:11])]==1:
                atomslist_allpdb[int(line[6:11])] = [float(line[30:38]),float(line[38:46]),float(line[46:54])]
                involved_residues.setdefault(line[21], []).append(line[23:26].strip())

                
with open( os.path.join(out,'onlyHoles.pdb'), 'w') as fp:
    for key in holes:
        points=[]
        for elem in holes[key]:
            points.append(np.array(atomslist_allpdb[int(elem)]))
        points=np.array(points)
        rr = points.mean(axis=0)
        X=str('%8.3f' % (float(rr[0]))).rjust(8)
        Y=str('%8.3f' % (float(rr[1]))).rjust(8)
        Z=str('%8.3f' % (float(rr[2]))).rjust(8)
        B=str('%6.2f' % (float(random.random()))).rjust(6)
        atomRes=str(key).rjust(3)
        fp.write('ATOM    '+atomRes+'  H   HOL H '+atomRes+'    '+X+Y+Z+'  1.00'+B+'                 H  \n')

with open(os.path.join(out, 'selection'), 'w') as fp:
    ngl_inv_residues = ""
    for key in involved_residues:
        ids=list(dict.fromkeys(involved_residues[key]))
        ngl_inv_residues +="(:{} and ({})) ".format(key, ' '.join(ids))
    fp.write(ngl_inv_residues)
    print(ngl_inv_residues)
