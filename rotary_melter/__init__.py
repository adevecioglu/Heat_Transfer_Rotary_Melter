"""V11 Rotary Melter application and independent numerical verification."""
import os

__version__ = '3.0.0'
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_name, '1')
