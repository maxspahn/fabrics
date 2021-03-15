import numpy as np
from scipy.integrate import odeint

from optFabrics.leaf import TimeVariantLeaf

class RootGeometry(object):
    def __init__(self, leaves, n, damper=None):
        self._n = n
        self._leaves = leaves
        self._h = np.zeros(n)
        self._rhs = np.zeros(n)
        self._rhs_aug = np.zeros(2*n)
        self._q = np.zeros(n)
        self._qdot = np.zeros(n)
        self._M = np.zeros((n, n))
        self._damper = damper
        self._d = np.zeros(n)

    def update(self, q, qdot, t=None):
        self._q = q
        self._qdot = qdot
        self._M = np.zeros((self._n, self._n))
        h_int = np.zeros(self._n)
        for leaf in self._leaves:
            isTimeVariant = isinstance(leaf, TimeVariantLeaf)
            if isTimeVariant:
                (M_leaf, h_leaf) = leaf.pull(q, qdot, t)
            else:
                (M_leaf, h_leaf) = leaf.pull(q, qdot)
            self._M += M_leaf
            h_int += np.dot(M_leaf, h_leaf)
        self._h = np.dot(np.linalg.pinv(self._M), h_int)
        if self._damper:
            (alpha, beta) = self._damper.damp(q, qdot, self._h)
            self._d = alpha * qdot - beta * qdot

    def setRHS(self):
        self._rhs = -self._h + self._d

    def augment(self):
        for i in range(self._n):
            self._rhs_aug[i] = self._qdot[i]
            self._rhs_aug[i + self._n] = self._rhs[i]

    def contDynamics(self, z, t):
        self.update(z[0:self._n], z[self._n:2*self._n], t)
        self.setRHS()
        self.augment()
        zdot = self._rhs_aug
        return zdot

    def computePath(self, z0, dt, T):
        t = np.arange(0.0, T, step=dt)
        sol, info = odeint(self.contDynamics, z0, t, full_output=True)
        return sol
