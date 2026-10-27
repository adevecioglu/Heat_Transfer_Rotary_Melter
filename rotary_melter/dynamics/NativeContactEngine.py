"""Ownership-safe NumPy transport for C++ contact calculations; no physical law here."""
import ctypes
import weakref
import numpy as np
from ..NativeEngine import _load

_DOUBLE = ctypes.POINTER(ctypes.c_double)


class NativeContacts:
    def __init__(self):
        self.library = library = _load()
        library.rotary_motion_create.restype = ctypes.c_void_p
        library.rotary_motion_destroy.argtypes = [ctypes.c_void_p]
        library.rotary_motion_error.argtypes = [ctypes.c_void_p]
        library.rotary_motion_error.restype = ctypes.c_char_p
        library.rotary_motion_history_size.argtypes = [ctypes.c_void_p]
        library.rotary_motion_history_size.restype = ctypes.c_ulonglong
        library.rotary_motion_lattice.argtypes = [ctypes.c_void_p, _DOUBLE, ctypes.c_ulonglong, ctypes.c_double, _DOUBLE]
        library.rotary_motion_advance.argtypes = [ctypes.c_void_p, _DOUBLE, ctypes.c_ulonglong, ctypes.c_double, _DOUBLE,
            ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_int, ctypes.c_int, ctypes.c_double,
            ctypes.c_longlong, ctypes.c_int, _DOUBLE]
        library.rotary_motion_liquid_plane.argtypes = [ctypes.c_void_p, _DOUBLE, ctypes.c_ulonglong, ctypes.c_double,
                                                       _DOUBLE, ctypes.c_double, _DOUBLE]
        self.handle = library.rotary_motion_create()
        if not self.handle:
            raise MemoryError('Unable to allocate the native motion context.')
        self._finalizer = weakref.finalize(self, library.rotary_motion_destroy, self.handle)

    @staticmethod
    def _pointer(array):
        if array.dtype != np.float64 or not array.flags.c_contiguous:
            raise ValueError('Native contact arrays require contiguous float64 storage.')
        return array.ctypes.data_as(_DOUBLE)

    def _check(self, successful):
        if not successful:
            raise RuntimeError(self.library.rotary_motion_error(self.handle).decode('utf-8'))

    def lattice(self, count, radius, geometry):
        if not isinstance(count,int) or not 1 <= count <= 2_000_000:
            raise ValueError('Physical particle count must lie between 1 and 2,000,000.')
        if geometry.shape != (16,):
            raise ValueError('Contact geometry requires 16 values.')
        particles = np.zeros((count, 12), dtype=np.float64)
        self._check(self.library.rotary_motion_lattice(self.handle, self._pointer(particles), count,
                                                      radius, self._pointer(geometry)))
        return particles

    def advance(self, particles, radius, geometry, steps, dt, omega, iterations, position_iterations,
                first_iteration, rigid=True, gravity=9.81):
        if particles.ndim != 2 or particles.shape[1] != 12 or not particles.flags.writeable or geometry.shape != (16,):
            raise ValueError('Motion requires writable N×12 particle storage and 16 geometry values.')
        metrics = np.zeros(4, dtype=np.float64)
        self._check(self.library.rotary_motion_advance(self.handle, self._pointer(particles), len(particles),
            radius, self._pointer(geometry), steps, dt, omega, iterations, position_iterations, gravity,
            first_iteration, int(rigid), self._pointer(metrics)))
        return int(metrics[0]), int(metrics[1]), float(metrics[2]), int(metrics[3])

    def liquid_plane(self, particles, radius, geometry, volume):
        if particles.ndim != 2 or particles.shape[1] != 12 or geometry.shape != (16,):
            raise ValueError('Motion requires N×12 particle storage and 16 geometry values.')
        result = np.zeros(1, dtype=np.float64)
        self._check(self.library.rotary_motion_liquid_plane(self.handle, self._pointer(particles),len(particles),
            radius, self._pointer(geometry), volume, self._pointer(result)))
        return float(result[0])

    @property
    def history_size(self):
        return self.library.rotary_motion_history_size(self.handle)

    def close(self):
        self._finalizer()
