from typing import Iterable

shifts = (
    ((0, 0), (1, 3), (2, 2), (3, 1)),
    ((0, 0), (1, 5), (2, 4), (3, 3)),
    ((0, 0), (1, 7), (3, 5), (4, 4)),
)

A = (
    (1, 1, 1, 1, 1, 0, 0, 0),
    (0, 1, 1, 1, 1, 1, 0, 0),
    (0, 0, 1, 1, 1, 1, 1, 0),
    (0, 0, 0, 1, 1, 1, 1, 1),
    (1, 0, 0, 0, 1, 1, 1, 1),
    (1, 1, 0, 0, 0, 1, 1, 1),
    (1, 1, 1, 0, 0, 0, 1, 1),
    (1, 1, 1, 1, 0, 0, 0, 1),
)

# produce log and a_log tables, needed for multiplying in the
# field GF(2^m) (generator = 3)
a_log = [1]
for i in range(255):
    j = (a_log[-1] << 1) ^ a_log[-1]
    if j & 0x100 != 0:
        j ^= 0x11B
    a_log.append(j)

log = [0] * 256
for i in range(1, 255):
    log[a_log[i]] = i


# multiply two elements of GF(2^m)
def mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return a_log[(log[a & 0xFF] + log[b & 0xFF]) % 255]


# substitution box based on F^{-1}(x)
box = [[0] * 8 for _ in range(256)]
box[1][7] = 1
for i in range(2, 256):
    j = a_log[255 - log[i]]
    for t in range(8):
        box[i][t] = (j >> (7 - t)) & 0x01

B = [0, 1, 1, 0, 0, 0, 1, 1]

# affine transform:  box[i] <- B + A*box[i]
cox = [[0] * 8 for _ in range(256)]
for i in range(256):
    for t in range(8):
        cox[i][t] = B[t]
        for j in range(8):
            cox[i][t] ^= A[t][j] * box[i][j]

# S-boxes and inverse S-boxes
S = [0] * 256
Si = [0] * 256
for i in range(256):
    S[i] = cox[i][0] << 7
    for t in range(1, 8):
        S[i] ^= cox[i][t] << (7 - t)
    Si[S[i] & 0xFF] = i

# T-boxes
G = ((2, 1, 1, 3), (3, 2, 1, 1), (1, 3, 2, 1), (1, 1, 3, 2))

AA = [[0] * 8 for _ in range(4)]

for i in range(4):
    for j in range(4):
        AA[i][j] = G[i][j]
        AA[i][i + 4] = 1

for i in range(4):
    pivot = AA[i][i]
    for j in range(8):
        if AA[i][j] != 0:
            AA[i][j] = a_log[(255 + log[AA[i][j] & 0xFF] - log[pivot & 0xFF]) % 255]
    for t in range(4):
        if i != t:
            for j in range(i + 1, 8):
                AA[t][j] ^= mul(AA[i][j], AA[t][i])
            AA[t][i] = 0

iG = [[0] * 4 for _ in range(4)]

for i in range(4):
    for j in range(4):
        iG[i][j] = AA[i][j + 4]


def mul4(a: int, bs: Iterable[int]) -> int:
    if a == 0:
        return 0
    rr = 0
    for b in bs:
        rr <<= 8
        if b != 0:
            rr = rr | mul(a, b)
    return rr


T1: list[int] = []
T2: list[int] = []
T3: list[int] = []
T4: list[int] = []
T5: list[int] = []
T6: list[int] = []
T7: list[int] = []
T8: list[int] = []
U1: list[int] = []
U2: list[int] = []
U3: list[int] = []
U4: list[int] = []

for t in range(256):
    s = S[t]
    T1.append(mul4(s, G[0]))
    T2.append(mul4(s, G[1]))
    T3.append(mul4(s, G[2]))
    T4.append(mul4(s, G[3]))

    s = Si[t]
    T5.append(mul4(s, iG[0]))
    T6.append(mul4(s, iG[1]))
    T7.append(mul4(s, iG[2]))
    T8.append(mul4(s, iG[3]))

    U1.append(mul4(t, iG[0]))
    U2.append(mul4(t, iG[1]))
    U3.append(mul4(t, iG[2]))
    U4.append(mul4(t, iG[3]))

# round constants
r_con = [1]
r = 1
for t in range(1, 30):
    r = mul(2, r)
    r_con.append(r)
