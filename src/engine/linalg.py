"""The little linear algebra a 15-factor model needs, in plain Python.

Matrices are lists of rows. Fifteen factors is small enough that this is fast (well under a
millisecond per solve) and it keeps the engine free of numpy, so a bank machine with pip and no
build tools installs it as is. Every routine is deterministic: same input, same bits out.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

Matrix = List[List[float]]
Vector = List[float]


def zeros(n: int, m: int) -> Matrix:
    return [[0.0] * m for _ in range(n)]


def transpose(a: Matrix) -> Matrix:
    return [list(col) for col in zip(*a)]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    bt = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in bt] for row in a]


def matvec(a: Matrix, v: Sequence[float]) -> Vector:
    return [sum(x * y for x, y in zip(row, v)) for row in a]


def dot(u: Sequence[float], v: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(u, v))


def quad(a: Matrix, v: Sequence[float]) -> float:
    """v' A v."""
    return dot(v, matvec(a, v))


def sub(a: Matrix, rows: Sequence[int], cols: Sequence[int]) -> Matrix:
    return [[a[i][j] for j in cols] for i in rows]


def is_symmetric(a: Matrix, tol: float = 1e-12) -> bool:
    n = len(a)
    return all(abs(a[i][j] - a[j][i]) <= tol for i in range(n) for j in range(i + 1, n))


def cholesky(a: Matrix) -> Matrix:
    """Lower L with L L' = A. Raises ValueError when A is not positive definite."""
    n = len(a)
    low = zeros(n, n)
    for i in range(n):
        for j in range(i + 1):
            s = a[i][j] - sum(low[i][k] * low[j][k] for k in range(j))
            if i == j:
                if s <= 0.0:
                    raise ValueError("not positive definite")
                low[i][i] = math.sqrt(s)
            else:
                low[i][j] = s / low[j][j]
    return low


def solve_spd(a: Matrix, b: Matrix) -> Matrix:
    """X with A X = B for symmetric positive definite A (by Cholesky)."""
    low = cholesky(a)
    n = len(a)
    out = zeros(n, len(b[0]))
    for c in range(len(b[0])):
        y = [0.0] * n
        for i in range(n):
            y[i] = (b[i][c] - sum(low[i][k] * y[k] for k in range(i))) / low[i][i]
        x = [0.0] * n
        for i in reversed(range(n)):
            x[i] = (y[i] - sum(low[k][i] * x[k] for k in range(i + 1, n))) / low[i][i]
        for i in range(n):
            out[i][c] = x[i]
    return out


def eigh(a: Matrix, sweeps: int = 100, tol: float = 1e-14) -> Tuple[Vector, Matrix]:
    """Eigenvalues and eigenvectors (columns) of a symmetric matrix, by cyclic Jacobi rotations."""
    n = len(a)
    m = [row[:] for row in a]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(sweeps):
        off = sum(m[i][j] ** 2 for i in range(n) for j in range(i + 1, n))
        if off < tol:
            break
        for p in range(n):
            for q in range(p + 1, n):
                if abs(m[p][q]) < 1e-300:
                    continue
                theta = (m[q][q] - m[p][p]) / (2.0 * m[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    mkp, mkq = m[k][p], m[k][q]
                    m[k][p] = c * mkp - s * mkq
                    m[k][q] = s * mkp + c * mkq
                for k in range(n):
                    mpk, mqk = m[p][k], m[q][k]
                    m[p][k] = c * mpk - s * mqk
                    m[q][k] = s * mpk + c * mqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq
    return [m[i][i] for i in range(n)], v


def clip_to_correlation(r: Matrix, floor: float = 0.01) -> Matrix:
    """The nearest-by-eigenvalue-clipping correlation matrix: negative eigenvalues raised to
    ``floor``, rebuilt, and rescaled to a unit diagonal (BRD 9.1, "nắn về xác định dương")."""
    n = len(r)
    w, v = eigh(r)
    w = [max(x, floor) for x in w]
    out = [[sum(v[i][k] * w[k] * v[j][k] for k in range(n)) for j in range(n)] for i in range(n)]
    d = [math.sqrt(out[i][i]) for i in range(n)]
    out = [[out[i][j] / (d[i] * d[j]) for j in range(n)] for i in range(n)]
    for i in range(n):  # exact symmetry and unit diagonal after rounding
        out[i][i] = 1.0
        for j in range(i + 1, n):
            out[j][i] = out[i][j]
    return out


def normal_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))
