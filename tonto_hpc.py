#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import hashlib
import re
import shutil

WFN_REGEX = re.compile(r'\"(.*)\.(FChk|sbf|fchk)\"')
STORAGE_DIRECTORY = 'tonto_hpc_files'
PLACEHOLDER_STDOUT = """_______________________________________________________________

 T   O   N   T   O

 A free object-based system for computational chemistry

 Version: tonto_hpc
 Platform: python
 Build-date: 2019-08-07

 For conditions of use, on-line documentation, and contributor
 and developer information see :-

 https://github.com/dylan-jayatilaka/tonto

 Dylan Jayatilaka
 Daniel Grimwood
 Peter Spackman
_______________________________________________________________


Timer started at 07/08/2019 08:53:19.

 
Warning from MOLECULE.BASE:merge_atom_groups ... No SCF data set, assuming singlet state, rhf

===========================================
Atom-atom polarization energy
===========================================

. Atomic dipole polarizabilities from Thakkar and Lupinetti (2006)

Polarization energy (kJ/mol) .....  0.000000

=======================================
Quantum mechanical interaction energies
=======================================

. E_pro-supermol(non-orthog) = E(Psi) where Psi = Psi_1 Psi_2
. is the non-orthogonal pro-supermolecule product wavefunction

. E_pro-supermol(orthog) = E(Psi) where Psi = A(Psi_1 Psi_2)
  is the antisymmetrized normalized pro-supermolecule wavefunction

. Delta E_X = E_X(Psi) - E_X(Psi_1) - E_X(Psi_2) where the
  terms on the right are calculated as  expectation values of
  of operators X which are the subterms of the Hamiltonian

. This dcomposition was first defined by Kitaura & Morokuma.
  The code follows: P. Su and H. Li (2009) JCP 131 p. 014102.
  See there for references, or Stone's 'Intermolecular Forces'.

. NOTE: E_pro-supermol(orthog) is the only QM valid number since
  it arises from an antisymmetric wavefunction; however the non-
  orthogonal promolecule does produce good electronic densities
  for use in X-ray crystallography, so the sub terms which come
  from it, produce here, may also be reasonable.

. NOTE: The energies here always apply to determinant orbital
  wavefunctions NOT correlated density matrices. However for
  correlated wavefunctions the highest occupied natural orbitals
  (HONOs) are used instead of the molecular orbitals (MOs).

Separation (Å) ............................        0.000000
1. Delta E_kinetic-energy .................        0.000000
2. Delta E_nn-repulsion ...................        0.000000
3. Delta E_en-attraction ..................        0.000000
4. Delta E_ee-repulsion ...................        0.000000
5. Delta E_ee-exchange ....................        0.000000

6. E_pro-supermol(non-orthog) .............        0.000000
7. E_pro-supermol(orthog) .................        0.000000

Delta E         (1+2+3+4+5) ...............        0.000000
Delta E_coulomb   (2+3+4) .................        0.000000
Delta E_repulsion        (-6+7) ...........        0.000000
Delta E_exch-repulsion  (5-6+7) ...........        0.000000

Delta E_coul (kJ/mol) .....................        0.000000
Delta E_ee-exchange (kJ/mol) ..............        0.000000
Delta E_repulsion (kJ/mol) ................        0.000000
Delta E_exch-rep (kJ/mol) .................        0.000000

===========================================
Grimme (2006) atom-atom dispersion energy
===========================================

. See: Grimme (2006) J. Comp. Chem.  27(15) p. 1787
. E_disp = sum over atoms (C6 / r^6).

Grimme06 dispersion energy (kJ/mol) .....  0.000000

Wall-clock time taken for job "Group1_Group2" is , 0 seconds, 0 milliseconds.
CPU time taken for job "Group1_Group2" is 0.001 CPU seconds.

******************************************************************************
THIS IS A PLACEHOLDER STDOUT FILE FOR LATTICE ENERGIES WHEN USING tonto_hpc.py
******************************************************************************
"""

def is_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

def which(prog):
    fpath, fname = os.path.split(prog)
    if fpath and is_executable(fname):
        return prog
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, prog)
            if is_executable(exe_file):
                return exe_file
    return None

def hash_file(contents):
    return hashlib.sha1(contents.encode('latin-1')).hexdigest()

def copy_wavefunctions(input_contents, output_directory):
    wavefunctions = WFN_REGEX.findall(input_contents)
    for wfn in wavefunctions:
        shutil.copy('.'.join(wfn), output_directory)

def file_contents(filename):
    if not os.path.exists(filename):
        return ''
    with open(filename) as f:
        return f.read()

def check_cache(input_contents):
    if not os.path.exists(STORAGE_DIRECTORY):
        os.mkdir(STORAGE_DIRECTORY)

    h = hash_file(input_contents)

    output_directory = os.path.join(
        STORAGE_DIRECTORY, h
    )
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    storage_filename = os.path.join(
        output_directory,
        'stdin'
    )
    output_filename = os.path.join(
        output_directory,
        'stdout'
    )
    if os.path.exists(output_filename):
        with open(output_filename) as of:
            with open('stdout', 'w') as f:
                f.write(of.read())
    else:
        with open(storage_filename, 'w') as f:
            f.write(input_contents)
        copy_wavefunctions(input_contents, output_directory)
        with open('stdout', 'w') as f:
            f.write(PLACEHOLDER_STDOUT)

def is_interaction_energy_input(contents):
    return 'put_group_12_energies' in contents

def run_tonto(input_contents):
    tonto_exe = which('tonto')
    if tonto_exe is None:
        with open('stdout', 'w') as f:
            f.write('Could not find tonto executable')
        sys.exit(1)
    if is_interaction_energy_input(input_contents):
        check_cache(input_contents)
    else:
        sys.exit(subprocess.call([tonto_exe]))


def main():
    input_filename = 'stdin'
    output_filename = 'stdout'
    input_contents = file_contents(input_filename)
    run_tonto(input_contents)
    sys.exit(0)

if __name__ == '__main__':
    main()
