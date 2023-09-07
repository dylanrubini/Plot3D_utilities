from os import write
import numpy as np 
import os.path as osp
import struct
from pathlib import Path
from typing import List

from pandas.core.indexing import need_slice
from .block import Block, Sol

def __write_plot3D_block_binary(f, B:list, nblocks:int, nsplit:list):
    """Write binary plot3D block which contains X,Y,Z
        default format is Big-Endian

    Args:
        f (IO): file handle
        B (Block): writes a single block to a file
    """
    '''
        https://docs.python.org/3/library/struct.html
    '''

    nsplit_a, nsplit_r = nsplit
    nsplit_all = nsplit_a * nsplit_r

    def write_var(V:list, name:str, nb:int):

        IMAX = 0
        JMAX = 0
        for vv in V[(nb*nsplit_all):((nb*nsplit_all)+nsplit_all)]:
            if vv.IMAX > IMAX:
                IMAX = vv.IMAX

            if vv.JMAX > JMAX:
                JMAX = vv.JMAX
                
        KMAX = V[(nb*nsplit_all)].KMAX

        for k in range(KMAX):
            for nb_r in range(nsplit_r):                
                for j in range(JMAX):
                    for nb_a in range(nsplit_a):
                        for i in range(IMAX):
                            data = getattr(V[(nb*nsplit_all) + nb_a + (nb_r*nsplit_a)], name)
                            try:
                                d = data[i,j,k]
                            except IndexError:
                                break

                            f.write(struct.pack('f', d))

    filename = osp.basename(f.name)
    for nb in range(nblocks):
        print(f"{filename}: writing block = {nb}")        
        write_var(B, "X", nb)
        write_var(B, "Y", nb)
        write_var(B, "Z", nb)

def __write_plot3D_block_binary_sol(f, B:list, nblocks:int, 
                                    nsplit:list, if_consv=True):

    nsplit_a, nsplit_r = nsplit
    nsplit_all = nsplit_a * nsplit_r

    def write_var(V:list, name:str, nb:int, i_var:int=None):

        IMAX = 0
        JMAX = 0
        for vv in V[(nb*nsplit_all):((nb*nsplit_all)+nsplit_all)]:
            if vv.IMAX > IMAX:
                IMAX = vv.IMAX

            if vv.JMAX > JMAX:
                JMAX = vv.JMAX

        KMAX = V[(nb*nsplit_all)].KMAX

        for k in range(KMAX):
            for nb_r in range(nsplit_r):                
                for j in range(JMAX):
                    for nb_a in range(nsplit_a):
                        for i in range(IMAX):

                            data = getattr(V[(nb*nsplit_all) + nb_a + (nb_r*nsplit_a)], name)
                            if i_var is not None:
                                data = data[i_var]

                            try:
                                d = data[i,j,k]
                            except IndexError:
                                break

                            f.write(struct.pack('f', d))

    if if_consv:

        filename = osp.basename(f.name)
        for nb in range(nblocks):
            print(f"{filename}: writing block = {nb}")    
            f.write(struct.pack('f',B[nb].mach))
            f.write(struct.pack('f',B[nb].alpha))
            f.write(struct.pack('f',B[nb].rey))
            f.write(struct.pack('f',B[nb].time)) 

            write_var(B, "RO", nb)
            write_var(B, "ROVX", nb)
            write_var(B, "ROVY", nb)
            write_var(B, "ROVZ", nb)
            write_var(B, "ROE", nb)

    else:
        filename = osp.basename(f.name)
        for nb in range(nblocks):
            print(f"{filename}: writing block = {nb}")  
            for i_var in range(len(B[nb].F)):
                write_var(B, "F", nb, i_var)     

def __write_plot3D_block_ASCII(f,B:Block,columns:int=6):
    """Write plot3D block in ascii format 

    Args:
        f (IO): file handle
        B (Block): writes a single block to a file
        columns (int, optional): Number of columns in the file. Defaults to 6.
    """
    def write_var(V:np.ndarray):
        bNewLine = False
        indx = 0
        for k in range(B.KMAX):
            for j in range(B.JMAX):
                for i in range(B.IMAX):
                    f.write('{0:8.8f} '.format(V[i,j,k]))
                    bNewLine=False
                    indx+=1
                    if (indx % columns) == 0:
                        f.write('\n')
                        bNewLine=True
                    
        if not bNewLine:
            f.write('\n')
    write_var(B.X)
    write_var(B.Y)
    write_var(B.Z)

def write_plot3D(filename:str, nsplit:list, blocks:List[Block], binary:bool=True):
    """Writes blocks to a Plot3D file

    Args:
        filename (str): name of the file to create 
        blocks (List[Block]): List containing all the blocks to write
        binary (bool, optional): Binary big endian. Defaults to True.
    """

    if sum(nsplit) != 2 and not binary:
        raise ValueError("ASCII files not supported if blocks splitting")

    nsplit_a, nsplit_r = nsplit
    nsplit_all = nsplit_a * nsplit_r

    if binary:
        with open(filename,'wb') as f:

            nblocks = len(blocks)
            nblocks //= nsplit_all            
            f.write(struct.pack('I',nblocks))

            for i, b in enumerate(blocks):

                if i % nsplit_all == 0:

                    IMAX = 0
                    for l in range(nsplit_a):
                        IMAX += blocks[i+l].IMAX

                    JMAX = 0
                    for l in range(nsplit_r):
                        JMAX += blocks[i+(l*nsplit_a)].JMAX

                    KMAX = b.KMAX

                    f.write(struct.pack('I',IMAX))
                    f.write(struct.pack('I',JMAX))
                    f.write(struct.pack('I',KMAX))

            __write_plot3D_block_binary(f, blocks, nblocks, nsplit)
    else:
        with open(filename,'w') as f:
            f.write('{0:d}\n'.format(len(blocks)))
            for b in blocks:
                IMAX,JMAX,KMAX = b.X.shape
                f.write('{0:d} {1:d} {2:d}\n'.format(IMAX,JMAX,KMAX))            
            for b in blocks:
                __write_plot3D_block_ASCII(f,b)


def write_plot3D_sol(filename:str, nsplit:list, blocks:List[Sol]):

    nsplit_a, nsplit_r = nsplit
    nsplit_all = nsplit_a * nsplit_r

    if not blocks[0].if_function_file:
        with open(filename,'wb') as f:

            nblocks = len(blocks)
            nblocks //= nsplit_all            
            f.write(struct.pack('I',nblocks))

            for i, b in enumerate(blocks):

                if i % nsplit_all == 0:

                    IMAX = 0
                    for l in range(nsplit_a):
                        IMAX += blocks[i+l].IMAX

                    JMAX = 0
                    for l in range(nsplit_r):
                        JMAX += blocks[i+(l*nsplit_a)].JMAX

                    KMAX = b.KMAX

                    f.write(struct.pack('I',IMAX))
                    f.write(struct.pack('I',JMAX))
                    f.write(struct.pack('I',KMAX))                 
           
            __write_plot3D_block_binary_sol(f, blocks, nblocks, nsplit)

    with open(Path(filename).with_suffix(".fff"),'wb') as f:

        nblocks = len(blocks)
        nblocks //= nsplit_all            
        f.write(struct.pack('I',nblocks))

        for i, b in enumerate(blocks):

            if i % nsplit_all == 0:

                IMAX = 0
                for l in range(nsplit_a):
                    IMAX += blocks[i+l].IMAX

                JMAX = 0
                for l in range(nsplit_r):
                    JMAX += blocks[i+(l*nsplit_a)].JMAX

                KMAX = b.KMAX

                f.write(struct.pack('I',IMAX))
                f.write(struct.pack('I',JMAX))
                f.write(struct.pack('I',KMAX))          
                f.write(struct.pack('I',b.N_VAR_ADD))
                  
        __write_plot3D_block_binary_sol(f, blocks, nblocks, nsplit, if_consv=False)
