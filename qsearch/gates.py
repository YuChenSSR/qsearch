"""
This module defines the Gate class, which represents a quantum gate, as well as implementations of many common Gates.

Through the use of KroneckerGate and ProductGate, Gates can be formed for complex circuit structures.  The matrix and mat_jac functions are used for numerical optimization of parameterized gates.  The assemble function is used to generate an intermediate language of tuples that can be used by Assemblers to output descriptions of quantum circuits in other formats.
"""

import numpy as np
from . import utils, unitaries
from hashlib import md5

try:
    from qsrs import native_from_object
except ImportError:
    native_from_object = None

class Gate():
    """This class shows the framework for working with quantum gates in Qsearch."""
    def __init__(self):
        """Gates must set the following variables in __init__
        
        self.num_inputs : The number of parameters needed to generate a unitary.  This can be 0.
        self.qudits : The number of qudits acted on by a unitary of the size generated by the gate. For example, this would be 1 for U3, 2 for CNOT.
        """
        raise NotImplementedError("Subclasses of Gate should declare their own initializers.")
    
    def matrix(self, v):
        """Generates a matrix using the given vector of input parameters.  For a constant gate, v will be empty.

        Args:
            v : A numpy array of real floating point numbers, ranging from 0 to 2*PI.  Its size is equal to self.num_inputs
        
        Returns:
            np.ndarray : A unitary matrix with dtype="complex128", equal in size to d**self.qudits, where d is the intended
            qudit size (d is 2 for qubits, 3 for qutrits, etc.)
        """
        raise NotImplementedError("Subclasses of Gate are required to implement the matrix(v) method.")

    def mat_jac(self, v):
        """Generates a matrix and the jacobian(s) using the given vector of input parameters.

        It is not required to implement mat_jac for constant gates, nor is it required when using gradient-free Solvers.

        The jacobian matrices will be complex valued, and should be the elementwise partial derivative with respect to each of the parameters.
        There should be self.num_inputs matrices in the array, with the ith entry being the partial derivative with respect to v[i].
        See U3Gate for an example implementation.

        Args:
            v : A numpy array of real floating point numbers, ranging from 0 to 2*PI.  Its size is equal to self.num_inputs

        Returns:
            tuple : A tuple of the same unitary that would be returned by matrix(v), and an array of Jacobian matrices.
        """
        if self.num_inputs == 0:
            return (self.matrix(v), []) # A constant gate (one with no parameters) has no jacobian
        raise NotImplementedError("Subclasses of Gate are required to implement the mat_jac(v) method in order to be used with gradient optimizers.")

    def assemble(self, v, i=0):
        """Generates an array of tuples as an intermediate format before being processed by an Assembler for conversion to other circuit formats.

        Args:
            v : The same numpy array of real floating point numbers that might be passed to matrix(v).
            i : The index of the lowest-indexed qubit that the unitary generated by the gate acts on.


        Returns:
            list : A list of tuples following the format described above.

        The format of the tuples returned looks like:

        `("gate", gatename, (*gateparameters), (*gateindices))`

        Where `gatename` corresponds to a gate that an Assembler will recognize, `gateparameters` corresponds to the parameters for the specified gate
        (usually but not always calculated from v), and `gateindices` corresponds to the qubit indices that the gate acts on (usually but not always calculated from i).

        You can also have tuples of the form ("block", *tuples)
        Where tuples is an array of tuples in this same format.

        For some helpful examples, look at U3Gate, XZXZGate, CNOTGate, and NonadjacentCNOTGate.
        """
        raise NotImplementedError("Subclasses of Gate are required to implement the assemble(v, i) method.")

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __hash__(self):
        return int(md5(repr(self).encode()).hexdigest(), 16) # using md5 rather than the default python has method ensures that hashes don't change when restarting python, which can be a problem if hashes are saved as part of intermediate states

    def copy(self):
        return self

    def _parts(self):
        return [self]

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __repr__(self):
        return "Gate()"

    def validate_structure(self):
        return True

class IdentityGate(Gate):
    """Represents an identity gate of any number of qudits of any size."""
    def __init__(self, qudits=1, d=2):
        """
        Args:
            qudits : The number of qudits represented by this identity.
            d : The size of qudits represented by this identity (2 for qubits, 3 for qutrits, etc.)
        """
        self.num_inputs=0
        self._I = np.array(np.eye(d**qudits), dtype='complex128')
        self.qudits = qudits
        self._d = d

    def matrix(self, v):
        return self._I

    def assemble(self, v, i=0):
        return []

    def __repr__(self):
        if self.qudits == 1 and self._d == 2:
            return "IdentityGate()"
        else:
            return "IdentityGate(qudits={}, d={})".format(self.qudits, self._d)


class XGate(Gate):
    """Represents a parameterized X rotation on one qubit."""
    def __init__(self):
        self.num_inputs = 1
        self.qudits = 1

    def matrix(self, v):
        return unitaries.rot_x(v[0])

    def mat_jac(self, v):
        U = unitaries.rot_x(v[0])
        J1 = unitaries.rot_x_jac(v[0])
        return U, [J1]

    def assemble(self, v, i=0):
        return [("gate", "X", (v[0],), (i,))]

    def __repr__(self):
        return "XGate()"

class YGate(Gate):
    """Represents a parameterized Y rotation on one qubit."""
    def __init__(self):
        self.num_inputs = 1
        self.qudits = 1

    def matrix(self, v):
        return unitaries.rot_y(v[0])

    def mat_jac(self, v):
        U = unitaries.rot_y(v[0])
        J1 = unitaries.rot_y_jac(v[0])
        return U, [J1]

    def assemble(self, v, i=0):
        return [("gate", "Y", (v[0],), (i,))]

    def __repr__(self):
        return "YGate()"

class ZGate(Gate):
    """Represents a parameterized Z rotation on one qubit."""
    def __init__(self):
        self.num_inputs = 1
        self.qudits = 1

    def matrix(self, v):
        return unitaries.rot_z(v[0])

    def mat_jac(self, v):
        U = unitaries.rot_z(v[0])
        J1 = unitaries.rot_z_jac(v[0])
        return U, [J1]

    def assemble(self, v, i=0):
        return [("gate", "Z", (v[0],), (i,))]

    def __repr__(self):
        return "ZGate()"

class ZXZXZGate(Gate):
    """Represents an arbitrary parameterized single-qubit gate, decomposed into 3 parameterized Z gates separated by X(PI/2) gates."""
    def __init__(self):
        self.num_inputs = 3
        self.qudits = 1

        self._x90 = unitaries.rot_x(np.pi/2)
        self._rot_z = unitaries.rot_z(0)
        self._out = np.array(np.eye(2), dtype='complex128')
        self._buffer = np.array(np.eye(2), dtype = 'complex128')
       
    def matrix(self, v):
        utils.re_rot_z(v[0], self._rot_z)
        self._out = np.dot(self._x90, self._rot_z, out=self._out)
        utils.re_rot_z(v[1], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._out, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z(v[2], self._rot_z)
        return np.dot(self._rot_z, self._out)

    def mat_jac(self, v):
        utils.re_rot_z_jac(v[0], self._rot_z)
        self._out = np.dot(self._x90, self._rot_z, out=self._out)
        utils.re_rot_z(v[1], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._out, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z(v[2], self._rot_z)
        J1 = np.dot(self._rot_z, self._out)

        utils.re_rot_z(v[0], self._rot_z)
        self._out = np.dot(self._x90, self._rot_z, out=self._out)
        utils.re_rot_z_jac(v[1], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._out, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z(v[2], self._rot_z)
        J2 = np.dot(self._rot_z, self._out)

        utils.re_rot_z(v[0], self._rot_z)
        self._out = np.dot(self._x90, self._rot_z, out=self._out)
        utils.re_rot_z(v[1], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._out, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z_jac(v[2], self._rot_z)
        J3 = np.dot(self._rot_z, self._out)
        
        utils.re_rot_z(v[2], self._rot_z)
        U = np.dot(self._rot_z, self._out)
        return (U, [J1, J2, J3])

    def assemble(self, v, i=0):
        out = []
        v = np.array(v)%(2*np.pi) # confine the range of what we print to come up with nicer numbers at no loss of generality
        out.append(("gate", "Z", (v[0],), (i,)))
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[1],), (i,)))
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[2],), (i,)))
        return [("block", out)]
 
    def __repr__(self):
        return "ZXZXZGate()"

class XZXZGate(Gate):
    """Represents a partially parameterized single qubit gate, equivalent to ZXZXZ but without the first Z gate.  This is useful because that first Z gate can commute through the control of a CNOT, thereby reducing the number of parameters we need to solve for."""
    def __init__(self):
        self.num_inputs = 2
        self.qudits = 1

        self._x90 = unitaries.rot_x(np.pi/2)
        self._rot_z = unitaries.rot_z(0)
        self._out = np.array(np.eye(2), dtype='complex128')
        self._buffer = np.array(np.eye(2), dtype = 'complex128')
        # need two buffers due to a bug in some implementations of numpy
        
    def matrix(self, v):
        utils.re_rot_z(v[0], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._x90, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z(v[1], self._rot_z)
        return np.dot(self._rot_z, self._out)

    def mat_jac(self, v):
        utils.re_rot_z_jac(v[0], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._x90, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z(v[1], self._rot_z)
        J1 = np.dot(self._rot_z, self._out)

        utils.re_rot_z(v[0], self._rot_z)
        self._buffer = np.dot(self._rot_z, self._x90, out=self._buffer)
        self._out = np.dot(self._x90, self._buffer, out=self._out)
        utils.re_rot_z_jac(v[1], self._rot_z)
        J2 = np.dot(self._rot_z, self._out)

        utils.re_rot_z(v[1], self._rot_z)
        U = np.dot(self._rot_z, self._out)
        return (U, [J1, J2])

    def assemble(self, v, i=0):
        out = []
        v = np.array(v)%(2*np.pi) # confine the range of what we print to come up with nicer numbers at no loss of generality
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[0],), (i,)))
        out.append(("gate", "X", (np.pi/2,), (i,)))
        out.append(("gate", "Z", (v[1],), (i,)))
        return [("block", out)]
 
    def __repr__(self):
        return "XZXZGate()"

class U3Gate(Gate):
    """Represents an arbitrary parameterized single qubit gate, parameterized in the same way as IBM's U3 gate."""
    def __init__(self):
        self.num_inputs = 3
        self.qudits = 1

    def matrix(self, v):
        ct = np.cos(v[0]/2)
        st = np.sin(v[0]/2)
        cp = np.cos(v[1])
        sp = np.sin(v[1])
        cl = np.cos(v[2])
        sl = np.sin(v[2])
        return np.array([[ct, -st * (cl + 1j * sl)], [st * (cp + 1j * sp), ct * (cl * cp - sl * sp + 1j * cl * sp + 1j * sl * cp)]], dtype='complex128')


    def mat_jac(self, v):
        ct = np.cos(v[0]/2)
        st = np.sin(v[0]/2)
        cp = np.cos(v[1])
        sp = np.sin(v[1])
        cl = np.cos(v[2])
        sl = np.sin(v[2])

        U = np.array([[ct, -st * (cl + 1j * sl)], [st * (cp + 1j * sp), ct * (cl * cp - sl * sp + 1j * cl * sp + 1j * sl * cp)]], dtype='complex128')
        J1 = np.array([[-0.5*st, -0.5*ct * (cl + 1j * sl)], [0.5*ct * (cp + 1j * sp), -0.5*st * (cl * cp - sl * sp + 1j * cl * sp + 1j * sl * cp)]], dtype='complex128')
        J2 = np.array([[0, 0], [st *(-sp + 1j * cp), ct *(cl * -sp - sl * cp + 1j * cl * cp + 1j * sl * -sp)]], dtype='complex128')
        J3 = np.array([[0, -st *(-sl + 1j * cl)], [0, ct *(-sl * cp - cl * sp + 1j * -sl * sp + 1j * cl * cp)]], dtype='complex128')
        return (U, [J1, J2, J3])

    def assemble(self, v, i=0):
        v = np.array(v)%(2*np.pi) # confine the range to nice numbers
        return [("gate", "U3", (v[0], v[1], v[2]), (i,))]

    def __eq__(self, other):
        return type(self) == type(other)

    def __repr__(self):
        return "U3Gate()"

class U2Gate(Gate):
    """Represents a parameterized single qubit gate, parameterized in the same way as IBM's U2 gate."""
    def __init__(self):
        self.num_inputs = 2
        self.qudits = 1

    def matrix(self, v):
        return 1/np.sqrt(2) * np.array([[1, -np.exp(1j * v[1])], [np.exp(1j * v[0]), np.exp(1j * (v[0] + v[1]))]])

    def mat_jac(self, v):
        initial = 1/np.sqrt(2)
        e1 = np.exp(1j * v[1])
        e2 = np.exp(1j * v[0])
        e3 = np.exp(1j * (v[0] + v[1]))
        U = initial * np.array([[1, -e1], [e2, e3]])
        J1 = initial * np.array([[0, 0], [1j * e2, 1j * e3]])
        J2 = initial * np.array([[0, -1j * e1], [0, 1j * e3]])
        return (U, [J1, J2])

    def assemble(self, v, i=0):
        v = np.array(v)%(2*np.pi) # confine the range to nice numbers
        return [("gate", "U3", (np.pi/2, v[0], v[1]), (i,))]

    def __eq__(self, other):
        return type(self) == type(other)

    def __repr__(self):
        return "U2Gate()"

class U1Gate(Gate):
    """Represents an parameterized single qubit gate, parameterized in the same way as IBM's U1 gate."""
    def __init__(self):
        self.num_inputs = 1
        self.qudits = 1

    def matrix(self, v):
        return np.exp(1j*v[0]/2) * unitaries.rot_z(v[0])

    def mat_jac(self, v):
        U = np.exp(1j*v[0]/2) * unitaries.rot_z(v[0])
        J1 = 1j/2 * np.exp(1j*v[0]/2) * unitaries.rot_z(v[0]) + np.exp(1j*v[0]/2) * unitaries.rot_z_jac(v[0])
        return (U, [J1])

    def assemble(self, v, i=0):
        v = np.array(v)%(2*np.pi) # confine the range to nice numbers
        return [("gate", "U3", (0, 0, v[0]), (i,))]

    def __eq__(self, other):
        return type(self) == type(other)

    def __repr__(self):
        return "U1Gate()"

class SingleQutritGate(Gate):
    """This gate represents an arbitrary parameterized single-qutrit gate."""
    def __init__(self):
        self.num_inputs = 8
        self.qudits = 1

    def matrix(self, v):
        # for reference see the original implementation, qt_arb_rot in utils.py, which is now deprecated
        # this was re-written to be computationally more efficient and more readable
        s1 = np.sin(v[0])
        c1 = np.cos(v[0])
        s2 = np.sin(v[1])
        c2 = np.cos(v[1])
        s3 = np.sin(v[2])
        c3 = np.cos(v[2])
        
        p1 = np.exp(1j * v[3])
        m1 = np.exp(-1j * v[3])
        p2 = np.exp(1j * v[4])
        m2 = np.exp(-1j * v[4])
        p3 = np.exp(1j * v[5])
        m3 = np.exp(-1j * v[5])
        p4 = np.exp(1j * v[6])
        m4 = np.exp(-1j * v[6])
        p5 = np.exp(1j * v[7])
        m5 = np.exp(-1j * v[7])

        return np.array([
            [c1*c2*p1, s1*p3, c1*s2*p4],
            [s2*s3*m4*m5 - s1*c2*c3*p1*p2*m3, c1*c3*p2, -c2*s3*m1*m5 - s1*s2*c3*p2*m3*p4],
            [-s1*c2*s3*p1*m3*p5 - s2*c3*m2*m4, c1*s3*p5, c2*c3*m1*m2 - s1*s2*s3*m3*p4*p5]
            ], dtype = 'complex128')

    def mat_jac(self, v):
        s1 = np.sin(v[0])
        c1 = np.cos(v[0])
        s2 = np.sin(v[1])
        c2 = np.cos(v[1])
        s3 = np.sin(v[2])
        c3 = np.cos(v[2])
        
        p1 = np.exp(1j * v[3])
        m1 = np.exp(-1j * v[3])
        p2 = np.exp(1j * v[4])
        m2 = np.exp(-1j * v[4])
        p3 = np.exp(1j * v[5])
        m3 = np.exp(-1j * v[5])
        p4 = np.exp(1j * v[6])
        m4 = np.exp(-1j * v[6])
        p5 = np.exp(1j * v[7])
        m5 = np.exp(-1j * v[7])

        U = np.array([
            [c1*c2*p1, s1*p3, c1*s2*p4],
            [s2*s3*m4*m5 - s1*c2*c3*p1*p2*m3, c1*c3*p2, -c2*s3*m1*m5 - s1*s2*c3*p2*m3*p4],
            [-s1*c2*s3*p1*m3*p5 - s2*c3*m2*m4, c1*s3*p5, c2*c3*m1*m2 - s1*s2*s3*m3*p4*p5]
            ], dtype = 'complex128')

        Jt1 = np.array([
            [-s1*c2*p1, c1*p3, -s1*s2*p4],
            [-c1*c2*c3*p1*p2*m3, -s1*c3*p2, -c1*s2*c3*p2*m3*p4],
            [-c1*c2*s3*p1*m3*p5, -s1*s3*p5, -c1*s2*s3*m3*p4*p5]
            ], dtype = 'complex128')

        Jt2 = np.array([
            [-c1*s2*p1, 0, c1*c2*p4],
            [c2*s3*m4*m5 + s1*s2*c3*p1*p2*m3, 0, s2*s3*m1*m5 - s1*c2*c3*p2*m3*p4],
            [s1*s2*s3*p1*m3*p5 -c2*c3*m2*m4, 0, -s2*c3*m1*m2 - s1*c2*s3*m3*p4*p5]
            ], dtype = 'complex128')

        Jt3 = np.array([
            [0, 0, 0],
            [s2*c3*m4*m5 + s1*c2*s3*p1*p2*m3, -c1*s3*p2, -c2*c3*m1*m5 + s1*s2*s3*p2*m3*p4],
            [-s1*c2*c3*p1*m3*p5 + s2*s3*m2*m4, c1*c3*p5, -c2*s3*m1*m2 - s1*s2*c3*m3*p4*p5]
            ], dtype = 'complex128')

        Je1 = np.array([
            [1j*c1*c2*p1, 0, 0],
            [-1j*s1*c2*c3*p1*p2*m3, 0, 1j*c2*s3*m1*m5],
            [-1j*s1*c2*s3*p1*m3*p5, 0, -1j*c2*c3*m1*m2]
            ], dtype = 'complex128')

        Je2 = np.array([
            [0, 0, 0],
            [-1j*s1*c2*c3*p1*p2*m3, 1j*c1*c3*p2, -1j*s1*s2*c3*p2*m3*p4],
            [1j*s2*c3*m2*m4, 0, -1j*c2*c3*m1*m2]
            ], dtype = 'complex128')

        Je3 = np.array([
            [0, 1j*s1*p3, 0],
            [1j*s1*c2*c3*p1*p2*m3, 0, 1j*s1*s2*c3*p2*m3*p4],
            [1j*s1*c2*s3*p1*m3*p5, 0, 1j*s1*s2*s3*m3*p4*p5]
            ], dtype = 'complex128')

        Je4 = np.array([
            [0, 0, 1j*c1*s2*p4],
            [-1j*s2*s3*m4*m5, 0, -1j*s1*s2*c3*p2*m3*p4],
            [1j*s2*c3*m2*m4, 0, -1j*s1*s2*s3*m3*p4*p5]
            ], dtype = 'complex128')

        Je5 = np.array([
            [0, 0, 0],
            [-1j*s2*s3*m4*m5, 0, 1j*c2*s3*m1*m5],
            [-1j*s1*c2*s3*p1*m3*p5, 1j*c1*s3*p5, -1j*s1*s2*s3*m3*p4*p5]
            ], dtype = 'complex128')

        return (U, [Jt1, Jt2, Jt3, Je1, Je2, Je3, Je4, Je5])

    def assemble(self, v, i=0):
        return [("gate", "QUTRIT", (*v,), (i,))]
    
    def __repr__(self):
        return "SingleQutritGate()"

class CSUMGate(Gate):
    """Represents the constant two-qutrit gate CSUM"""
    _csum =  np.array([[1,0,0, 0,0,0, 0,0,0],
                        [0,1,0, 0,0,0, 0,0,0],
                        [0,0,1, 0,0,0, 0,0,0],
                        [0,0,0, 0,0,1, 0,0,0],
                        [0,0,0, 1,0,0, 0,0,0],
                        [0,0,0, 0,1,0, 0,0,0],
                        [0,0,0, 0,0,0, 0,1,0],
                        [0,0,0, 0,0,0, 1,0,0],
                        [0,0,0, 0,0,0, 0,0,1]
                       ], dtype='complex128')
    
    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def matrix(self, v):
        return CSUMGate._csum

    def assemble(self, v, i=0):
        return [("gate", "CSUM", (), (i, i+1))]

    def __repr__(self):
        return "CSUMGate()"

class CPIGate(Gate):
    """Represents the constant two-qutrit gate CPI."""
    _cpi = np.array([[1,0,0, 0,0,0, 0,0,0],
                      [0,1,0, 0,0,0, 0,0,0],
                      [0,0,1, 0,0,0, 0,0,0],
                      [0,0,0, 0,1,0,0,0,0],
                      [0,0,0, 1,0,0, 0,0,0],
                      [0,0,0, 0,0,1, 0,0,0],
                      [0,0,0, 0,0,0, 1,0,0],
                      [0,0,0, 0,0,0, 0,1,0],
                      [0,0,0, 0,0,0, 0,0,1]
                     ], dtype='complex128')
    
    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def matrix(self, v):
        return CPIGate._cpi

    def assemble(self, v, i=0):
        return [("gate", "CPI", (), (i, i+1))]

    def __repr__(self):
        return "CPIGate()"

class CPIPhaseGate(Gate):
    """Represents the constant two-qutrit gate CPI with phase differences."""
    def __init__(self):
        self.num_inputs = 0
        self._cpi = np.array([[1,0,0, 0,0,0, 0,0,0],
                               [0,1,0, 0,0,0, 0,0,0],
                               [0,0,1, 0,0,0, 0,0,0],
                               [0,0,0, 0,-1,0,0,0,0],
                               [0,0,0, 1,0,0, 0,0,0],
                               [0,0,0, 0,0,1, 0,0,0],
                               [0,0,0, 0,0,0, 1,0,0],
                               [0,0,0, 0,0,0, 0,1,0],
                               [0,0,0, 0,0,0, 0,0,1]
                              ], dtype='complex128')
        diag_mod = np.array(np.diag([1]*4 + [np.exp(2j * np.random.random()*np.pi) for _ in range(0,5)]))
        self._cpi = np.matmul(self._cpi, diag_mod)
        self.qudits = 2

    def matrix(self, v):
        return self._cpi

    def assemble(self, v, i=0):
        return [("gate", "CPI-", (), (i, i+1))]

    def __repr__(self):
        return "CPIPhaseGate()"

class CNOTGate(Gate):
    """Represents the constant two-qubit gate CNOT."""
    _cnot = np.array([[1,0,0,0],
                       [0,1,0,0],
                       [0,0,0,1],
                       [0,0,1,0]], dtype='complex128')

    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def __eq__(self, other):
        return type(self) == type(other)

    def matrix(self, v):
        return CNOTGate._cnot

    def assemble(self, v, i=0):
        return [("gate", "CNOT", (), (i, i+1))]

    def __repr__(self):
        return "CNOTGate()"

class CZGate(Gate):
    """Represents the constant two-qubit gate Controlled-Z."""
    _gate = np.array([[1,0,0,0],
                       [0,1,0,0],
                       [0,0,1,0],
                       [0,0,0,-1]], dtype='complex128')

    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def __eq__(self, other):
        return type(self) == type(other)

    def matrix(self, v):
        return CZGate._gate

    def assemble(self, v, i=0):
        return [("gate", "CZ", (), (i, i+1))]

    def __repr__(self):
        return "CZGate()"

class ISwapGate(Gate):
    """Represents the constant two-qubit gate ISwap."""
    _gate = np.array([[1,0,0,0],
                       [0,0,1j,0],
                       [0,1j,0,0],
                       [0,0,0,1]], dtype='complex128')

    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def __eq__(self, other):
        return type(self) == type(other)

    def matrix(self, v):
        return ISwapGate._gate

    def assemble(self, v, i=0):
        return [("gate", "ISWAP", (), (i, i+1))]

    def __repr__(self):
        return "ISwapGate()"

class XXGate(Gate):
    """Represents the constant two-qubit gate XX(pi/2)."""
    _gate = 1/np.sqrt(2) * np.array([[1,0,0,-1j],
                                    [0,1,-1j,0],
                                    [0,-1j,1,0],
                                    [-1j,0,0,1]], dtype='complex128')

    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def __eq__(self, other):
        return type(self) == type(other)

    def matrix(self, v):
        return XXGate._gate

    def assemble(self, v, i=0):
        return [("gate", "XX", (), (i, i+1))]

    def __repr__(self):
        return "XXGate()"

class NonadjacentCNOTGate(Gate):
    """Represents the two-qubit gate CNOT, but between two qubits that are not necessarily next to each other."""
    def __init__(self, qudits, control, target):
        """
        Args:
            qudits : The total number of qubits that a unitary of the size returned by this gate would represent.  For this gate, usually
                this is the total number of qubits in the larger circuit.
            control : The index of the control qubit, relative to the 0th qubit that would be affected by the unitary returned by this gate.
            target : The index of the target qubit, relative to the 0th qubit that would be affected by the unitary returned by this gate.
        """
        self.qudits = qudits
        self.num_inputs = 0
        self.control = control
        self.target = target
        self._U = unitaries.arbitrary_cnot(qudits, control, target)

    def matrix(self, v):
        return self._U

    def assemble(self, v, i=0):
        return [("gate", "CNOT", (), (self.control, self.target))]

    def __repr__(self):
        return "NonadjacentCNOTGate({}, {}, {})".format(self.qudits, self.control, self.target)

    def validate_structure(self):
        if self.control >= self.qudits or self.target > self.qudits:
            warn("Invalid NonadjacentCNOTGate; both control and target must be smaller than dits.  Expected {} > {} and {}".format(self.qudits, self.control, self.target))
            return False
        if self.control == self.target:
            warn("Invalid NonadjacentCNOTGate: control and target must be different. Expected {} != {}".format(self.control, self.target))
            return False
        return True

class UGate(Gate):
    """Represents an arbitrary constant gate, defined by the unitary passed to the initializer."""
    def __init__(self, U, d=2, gatename="CUSTOM", gateparams=(), gateindices=None):
        """        
        Args:
            U : The unitary for the operation that this gate represents, as a numpy ndarray with datatype="complex128".
            d : The size of qudits for the operation that this gate represents.  The default is 2, for qubits.
            gatename : A name for this gate, which will get passed to the Assembler at assembly time.
            gateparams : A tuple of parameters that will get passed to the Assembler at assembly time.
            gateindices : A tuple of indices for the qubits that this gate acts on, which will get passed to the Assembler at assembly time.  This overrides the default behavior, which is to return a tuple of all the indices starting with the one passed in assemble(v, i), and ending at i+self.qudits 
        """
        self.d = d
        self.U = U
        self.qudits = int(np.log(U.shape[0])/np.log(2))
        self.num_inputs = 0
        self.gatename = gatename
        self.gateparams = gateparams
        self.gateindices = gateindices

    def matrix(self, v):
        return self.U

    def assemble(self, v, i=0):
        gatename = self.gatename
        gateparams = self.gateparams
        indices = self.gateindices if self.gateindices is not None else tuple((i+j for j in range(self.qudits)))
        return [("gate", gatename, gateparams, indices)]

    def __repr__(self):
        if self.d == 2:
            return "UGate({})".format(repr(U))
        else:
            return "UGate({}, d={})".format(repr(U), self.d)

class UpgradedConstantGate(Gate):
    """Represents a constant gate, based on the Gate passed to its initializer, but upgraded to act on qudits of a larger size."""
    def __init__(self, other, df=3):
        """
        Args:
            other : A Gate of a lower qudit size.
            df : The final, upgraded qudit size.  The default is 3, for upgrading gates from qubits to qutrits.
        """
        if other.num_inputs > 0:
            raise AttributeError("UpgradedConstantGate is designed for only constant gates")
        OU = other.matrix([])
        di = int(OU.shape[0]**(1/other.qudits))
        if df <= di:
            raise AttributeError("Gate cannot be upgraded because it is already of an equal or higher dit level")
        self.df = df
        self.qudits = other.qudits
        self.U = utils.upgrade_qudits(OU, di, df)
        self.num_inputs = 0
        self.subgate = other

    def matrix(self, v):
        return self.U

    def assemble(self, v, i=0):
        return self.subgate.assemble(v, i)

    def __repr__(self):
        return "UpgradedConstantGate({}, df={})".format(repr(self.subgate), self.df)


class CUGate(Gate):
    """Represents an arbitrary controlled gate, defined by the unitary passed to the initializer."""
    def __init__(self, U, gatename="Name", gateparams=(), flipped=False):
        """
        Args:
            U : The unitary to form the controlled-unitary gate, in the form of a numpy ndarray with dtype="complex128"
            gatename : A name for this controlled gate which will get passed to the Assembler at assembly time.
            gateparams : A tuple of parameters that will get passed to the Assembler at assembly time.
            flipped : A boolean flag, which if set to true, will flip the direction of the gate.  The default direction is for the control qubit to be the lower indexed qubit.
        """
        self.gatename = gatename
        self.gateparams = gateparams
        self.flipped = flipped
        self.num_inputs = 0
        self._U = U
        n = np.shape(U)[0]
        I = np.array(np.eye(n))
        top = np.pad(self._U if flipped else I, [(0,n),(0,n)], 'constant')
        bot = np.pad(I if flipped else self._U, [(n,0),(n,0)], 'constant')
        self._CU = np.array(top + bot)
        self.qudits = 2
        self.num_inputs = 0

    def matrix(self, v):
        return self._CU

    def assemble(self, v, i=0):
        gatename = self.gatename
        gateparams = self.gateparams
        indices = (i, i+1) if not flipped else (i+1, i)
        return [("gate", gatename, gateparams, indices)]

    def __repr__(self):
        return "CUGate(" + str(repr(self._U)) + ("" if self.name is None else ", name={}".format(repr(self.name))) + ("flipped=True" if self.flipped else "") + ")"

class CNOTRootGate(Gate):
    """Represents the sqrt(CNOT) gate.  Two sqrt(CNOT) gates in a row will form a CNOT gate."""
    _cnr = np.array([[1,0,0,0],
                       [0,1,0,0],
                       [0,0,0.5+0.5j,0.5-0.5j],
                       [0,0,0.5-0.5j,0.5+0.5j]])
    def __init__(self):
        self.num_inputs = 0
        self.qudits = 2

    def matrix(self, v):
        return CNOTRootGate._cnr

    def assemble(self, v, i=0):
        return [("gate", "sqrt(CNOT)", (), (i, i+1))]

    def __repr__(self):
        return "CNOTRootGate()"

class KroneckerGate(Gate):
    """Represents the Kronecker product of a list of gates.  This is equivalent to performing those gate in parallel in a quantum circuit."""
    def __init__(self, *subgates):
        """
        Args:
            *subgates : An sequence of Gates.  KroneckerGate will return the kronecker product of the unitaries returned by those Gates.
        """
        self.num_inputs = sum([gate.num_inputs for gate in subgates])
        self._subgates = subgates
        self.qudits = sum([gate.qudits for gate in subgates])

    def matrix(self, v):
        if len(self._subgates) < 2:
            return self._subgates[0].matrix(v)
        matrices = []
        index = 0
        for gate in self._subgates:
            U = gate.matrix(v[index:index+gate.num_inputs])
            matrices.append(U)
            index += gate.num_inputs
        U = matrices[0]
        for matrix in matrices[1:]:
            U = np.kron(U, matrix)
        return U

    def mat_jac(self, v):
        if len(self._subgates) < 2:
            return self._subgates[0].mat_jac(v)
        matjacs = []
        index = 0
        for gate in self._subgates:
            MJ = gate.mat_jac(v[index:index+gate.num_inputs])
            matjacs.append(MJ)
            index += gate.num_inputs

        U = None
        jacs = []
        for M, Js in matjacs:
            jacs = [np.kron(J, M) for J in jacs]
            for J in Js:
                jacs.append(J if U is None else np.kron(U,J))
            U = M if U is None else np.kron(U, M)

        return (U, jacs)

    def assemble(self, v, i=0):
        out = []
        index = 0
        for gate in self._subgates:
            out += gate.assemble(v[index:index+gate.num_inputs], i)
            index += gate.num_inputs
            i += gate.qudits
        return [("block", out)]

    def appending(self, gate):
        """Returns a new KroneckerGate with the new gate added to the list.
        
        
        Args:
            gate : A Gate to be added to the end of the list of gates in the new KroneckerGate.
        """
        return KroneckerGate(*self._subgates, gate)

    def _parts(self):
        return self._subgates

    def __deepcopy__(self, memo):
        return KroneckerGate(self._subgates.__deepcopy__(memo))

    def __repr__(self):
        return "KroneckerGate({})".format(repr(self._subgates)[1:-1])

    def validate_structure(self):
        valid = True
        num_inputs = 0
        dits = 0
        for subgate in self._subgates:
            if not subgate.validate_structure():
                valid = False
            num_inputs += subgate.num_inputs
            dits += subgate.qudits

        if num_inputs != self.num_inputs:
            warn("KroneckerGate had a num_inputs mismatch: expected {} but got {}".format(self.num_inputs, num_inputs))
            valid = False
        if dits != self.qudits:
            warn("KroneckerGate had a dits mismatch: expected {} but got {}".format(self.qudits, dits))
            valid = False
        return valid

class ProductGate(Gate):
    """Represents a matrix product of Gates.  This is equivalent to performing those gates sequentially in a quantum circuit."""
    def __init__(self, *subgates):
        """
        Args:
            subgates : A list of Gates to be multiplied together.  ProductGate returns the matrix product of the unitaries returned by those Gates.
        """
        self.num_inputs = sum([gate.num_inputs for gate in subgates])
        self._subgates = []
        for subgate in subgates:
            if type(subgate) is ProductGate:
                self._subgates.extend(subgate._subgates)
            else:
                self._subgates.append(subgate)
        self.qudits = 0 if len(subgates) == 0 else subgates[0].qudits

    def matrix(self, v):
        if len(self._subgates) < 2:
            return self._subgates[0].matrix(v)
        matrices = []
        index = 0
        for gate in self._subgates:
            U = gate.matrix(v[index:index+gate.num_inputs])
            matrices.append(U)
            index += gate.num_inputs
        U = matrices[0]
        buffer1 = U.copy()
        buffer2 = U.copy()
        for matrix in matrices[1:]:
            U = np.matmul(matrix, U, out=buffer1)
            buffertmp = buffer2
            buffer2 = buffer1
            buffer1 = buffer2
        return U

    def mat_jac(self, v):
        if len(self._subgates) < 2:
            return self._subgates[0].mat_jac(v)
        submats = []
        subjacs = []
        index = 0
        for gate in self._subgates:
            U, Js = gate.mat_jac(v[index:index+gate.num_inputs])
            submats.append(U)
            subjacs.append(Js)
            index += gate.num_inputs
        
        B = np.eye(submats[0].shape[0], dtype='complex128')
        A = submats[0]
        jacs = []
        ba1 = A.copy()
        ba2 = A
        bb1 = B.copy()
        bb2 = B
        bj = B.copy()
        for matrix in submats[1:]:
            A = np.matmul(matrix, A, out=ba1)
            buffertmp = ba2
            ba2 = ba1
            ba1 = ba2

        for i, Js in enumerate(subjacs):
            A = np.matmul(A, submats[i].T.conjugate(), out=ba1) # remove the current matrix from the "after" array
            for J in Js:
                tmp = np.matmul(J, B, out=bj)
                jacs.append(np.matmul(A, tmp, out=J))
            B = np.matmul(submats[i], B, out=bb1) # add the current matrix to the "before" array before progressing
            buffertmp = ba1
            ba1 = ba2
            ba2 = buffertmp
            buffertmp = bb1
            bb1 = bb2
            bb2 = buffertmp
            
        return (B, jacs)

    def assemble(self, v, i=0):
        out = []
        index = 0
        for gate in self._subgates:
            out += gate.assemble(v[index:index+gate.num_inputs], i)
            index += gate.num_inputs
        return out

    def appending(self, *gates):
        """Returns a new ProductGate with the new gates appended to the end.

        Args:
            gates : A list of Gates to be appended.
        """
        return ProductGate(*self._subgates, *gates)

    def inserting(self, *gates, depth=-1):
        """Returns a new ProductGate with new `gates` inserted at some index `depth`.
        
        Args:
            gates : A list of Gates to be inserted.
            depth : An index in the subgates of the ProductGate after which the new gates will be inserted.  The default value of -1 will insert these gates at the begining of the ProductGate.
        """
        return ProductGate(*self._subgates[:depth], *gates, *self._subgates[depth:])

    def __deepcopy__(self, memo):
        return ProductGate(self._subgates.__deepcopy__(memo))

    def __repr__(self):
        return "ProductGate({})".format(repr(self._subgates)[1:-1])

    def validate_structure(self):
        valid = True
        num_inputs = 0
        for subgate in self._subgates:
            if subgate.qudits != self.qudits:
                warn("ProductGate had a size mismatch: expected {} but got {}".format(self.qudits, subgate.qudits))
                valid = False
            if not subgate.validate_structure():
                valid = False
            num_inputs += subgate.num_inputs

        if num_inputs != self.num_inputs:
            warn("ProductGate had a num_inputs mismatch: expected {} but got {}".format(self.num_inputs, num_inputs))
            valid = False
        valid = True
