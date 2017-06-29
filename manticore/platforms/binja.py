import logging

from ..core.cpu.binja import BinjaCpu
from ..core.smtlib import ConstraintSet
from .platform import Platform
from ..utils.event import forward_signals

logger = logging.getLogger("PLATFORM")

class RestartSyscall(Exception):
    pass

class Deadlock(Exception):
    pass

class Binja(Platform):
    def __init__(self, ifile):
        '''
        Builds a BinaryNinja Emulator
        :param ifile: file containing program to analyze
        '''
        super(Binja, self).__init__(ifile)

        # XXX needed -> move to platform
        self.program = ifile
        self.clocks = 0
        self.files = []

        # XXX needed -> move to platform
        self.syscall_trace = []

        # binary view
        self._bv = self._init_bv(ifile)
        self._constraints = ConstraintSet()
        self._entry_func = self._bv.get_functions_at(self._bv.entry_point)

        # constraints
        cpu = BinjaCpu(self._bv, self._constraints)

        # XXX needed -> move to platform
        self.procs = [cpu]
        self._current = 0
        self._function_abi = None
        self._syscall_abi = None

        for proc in self.procs:
            forward_signals(self, proc)

    # XXX needed
    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, constraints):
        self._constraints = constraints
        for proc in self.procs:
            proc.memory.constraints = constraints


    # XXX needed -> move to Platform as abstractproperty
    @property
    def current(self):
        return self.procs[self._current]

    # XXX refactor Linux, Windows etc
    def execute(self):
        """
        Execute one cpu instruction in the current thread (only one supported).
        :rtype: bool
        :return: C{True}

        :todo: This is where we could implement a simple schedule.
        """
        #Install event forwarders
        for proc in self.procs:
            forward_signals(self, proc)

        self.current.execute()
        return True

    @property
    def bv(self):
        return self._bv

    def __getstate__(self):
        state = {}
        # XXX (theo) required
        state['constraints'] = self.constraints
        state['procs'] = self.procs
        state['current'] = self._current
        state['syscall_trace'] = self.syscall_trace
        return state

    def __setstate__(self, state):
        # XXX (theo) required as a minimum set of params
        self._constraints = state['constraints']
        self.procs = state['procs']
        self._current = state['current']
        self.syscall_trace = state['syscall_trace']

        #Install event forwarders
        for proc in self.procs:
            forward_signals(self, proc)

    @staticmethod
    def _init_bv(program_file):
        """
        Reads a binary and returns a binary vieww

        FIXME (theo) this will be replaced by a function that simply loadss
        the IL from a file, but right now this is not serializable
        """
        # XXX do the import here so as to not affect users who don't have
        # BinaryNinja installed
        import binaryninja as bn
        bv = bn.binaryview.BinaryViewType.get_view_of_file(program_file)
        bv.update_analysis_and_wait()
        return bv
