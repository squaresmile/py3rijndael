from py3rijndael.constants import (
    T1,
    T2,
    T3,
    T4,
    T5,
    T6,
    T7,
    T8,
    U1,
    U2,
    U3,
    U4,
    S,
    Si,
    r_con,
    shifts,
)
from py3rijndael.paddings import PaddingBase


class Rijndael:
    def __init__(self, key: bytes, block_size: int = 16):

        if block_size not in (16, 24, 32):
            raise ValueError(f"Invalid block size: {block_size}")

        if len(key) not in (16, 24, 32):
            raise ValueError(f"Invalid key size: {len(key)}")

        self.block_size = block_size
        self.key = key

        if block_size == 32 or len(key) == 32:
            rounds = 14
        elif block_size == 16 and len(key) == 16:
            rounds = 10
        else:
            rounds = 12

        b_c = block_size // 4
        # encryption round keys
        k_e = [[0] * b_c for _ in range(rounds + 1)]
        # decryption round keys
        k_d = [[0] * b_c for _ in range(rounds + 1)]
        round_key_count = (rounds + 1) * b_c
        k_c = len(key) // 4

        # copy user material bytes into temporary ints
        tk = [
            key[i * 4] << 24
            | key[i * 4 + 1] << 16
            | key[i * 4 + 2] << 8
            | key[i * 4 + 3]
            for i in range(k_c)
        ]

        # copy values into round key arrays
        t = 0
        j = 0
        while j < k_c and t < round_key_count:
            k_e[t // b_c][t % b_c] = tk[j]
            k_d[rounds - (t // b_c)][t % b_c] = tk[j]
            j += 1
            t += 1
        r_con_pointer = 0
        while t < round_key_count:
            # extrapolate using phi (the round key evolution function)
            tt = tk[k_c - 1]
            tk[0] ^= (
                (S[(tt >> 16) & 0xFF] & 0xFF) << 24
                ^ (S[(tt >> 8) & 0xFF] & 0xFF) << 16
                ^ (S[tt & 0xFF] & 0xFF) << 8
                ^ (S[(tt >> 24) & 0xFF] & 0xFF)
                ^ (r_con[r_con_pointer] & 0xFF) << 24
            )
            r_con_pointer += 1
            if k_c != 8:
                for i in range(1, k_c):
                    tk[i] ^= tk[i - 1]
            else:
                for i in range(1, k_c // 2):
                    tk[i] ^= tk[i - 1]
                tt = tk[k_c // 2 - 1]
                tk[k_c // 2] ^= (
                    (S[tt & 0xFF] & 0xFF)
                    ^ (S[(tt >> 8) & 0xFF] & 0xFF) << 8
                    ^ (S[(tt >> 16) & 0xFF] & 0xFF) << 16
                    ^ (S[(tt >> 24) & 0xFF] & 0xFF) << 24
                )
                for i in range(k_c // 2 + 1, k_c):
                    tk[i] ^= tk[i - 1]
            # copy values into round key arrays
            j = 0
            while j < k_c and t < round_key_count:
                k_e[t // b_c][t % b_c] = tk[j]
                k_d[rounds - (t // b_c)][t % b_c] = tk[j]
                j += 1
                t += 1
        # inverse MixColumn where needed
        for r in range(1, rounds):
            for j in range(b_c):
                tt = k_d[r][j]
                k_d[r][j] = (
                    U1[(tt >> 24) & 0xFF]
                    ^ U2[(tt >> 16) & 0xFF]
                    ^ U3[(tt >> 8) & 0xFF]
                    ^ U4[tt & 0xFF]
                )
        self.Ke = k_e
        self.Kd = k_d

    def encrypt(self, source: bytes) -> bytes:

        if len(source) != self.block_size:
            raise ValueError(
                f"Wrong block length, expected {self.block_size} got {len(source)}"
            )

        k_e = self.Ke

        b_c = self.block_size // 4
        rounds = len(k_e) - 1
        if b_c == 4:
            s_c = 0
        elif b_c == 6:
            s_c = 1
        else:
            s_c = 2
        s1 = shifts[s_c][1][0]
        s2 = shifts[s_c][2][0]
        s3 = shifts[s_c][3][0]
        a = [0] * b_c
        # temporary work array
        t = [
            (
                source[i * 4] << 24
                | source[i * 4 + 1] << 16
                | source[i * 4 + 2] << 8
                | source[i * 4 + 3]
            )
            ^ k_e[0][i]
            for i in range(b_c)
        ]
        # apply round transforms
        for r in range(1, rounds):
            a = [
                (
                    T1[(t[i] >> 24) & 0xFF]
                    ^ T2[(t[(i + s1) % b_c] >> 16) & 0xFF]
                    ^ T3[(t[(i + s2) % b_c] >> 8) & 0xFF]
                    ^ T4[t[(i + s3) % b_c] & 0xFF]
                )
                ^ k_e[r][i]
                for i in range(b_c)
            ]
            t = a.copy()
        # last round is special
        result: list[int] = []
        for i in range(b_c):
            tt = k_e[rounds][i]
            result.append((S[(t[i] >> 24) & 0xFF] ^ (tt >> 24)) & 0xFF)
            result.append((S[(t[(i + s1) % b_c] >> 16) & 0xFF] ^ (tt >> 16)) & 0xFF)
            result.append((S[(t[(i + s2) % b_c] >> 8) & 0xFF] ^ (tt >> 8)) & 0xFF)
            result.append((S[t[(i + s3) % b_c] & 0xFF] ^ tt) & 0xFF)

        return bytes(result)

    def decrypt(self, cipher: bytes) -> bytes:
        if len(cipher) != self.block_size:
            raise ValueError(
                f"wrong block length, expected {self.block_size} got {len(cipher)}"
            )

        k_d = self.Kd
        b_c = self.block_size // 4
        rounds = len(k_d) - 1
        if b_c == 4:
            s_c = 0
        elif b_c == 6:
            s_c = 1
        else:
            s_c = 2
        s1 = shifts[s_c][1][1]
        s2 = shifts[s_c][2][1]
        s3 = shifts[s_c][3][1]
        # temporary work array
        t = [
            (
                cipher[i * 4] << 24
                | cipher[i * 4 + 1] << 16
                | cipher[i * 4 + 2] << 8
                | cipher[i * 4 + 3]
            )
            ^ k_d[0][i]
            for i in range(b_c)
        ]
        # apply round transforms
        for r in range(1, rounds):
            a = [
                (
                    T5[(t[i] >> 24) & 0xFF]
                    ^ T6[(t[(i + s1) % b_c] >> 16) & 0xFF]
                    ^ T7[(t[(i + s2) % b_c] >> 8) & 0xFF]
                    ^ T8[t[(i + s3) % b_c] & 0xFF]
                )
                ^ k_d[r][i]
                for i in range(b_c)
            ]
            t = a.copy()
        # last round is special
        result: list[int] = []
        for i in range(b_c):
            tt = k_d[rounds][i]
            result.append((Si[(t[i] >> 24) & 0xFF] ^ (tt >> 24)) & 0xFF)
            result.append((Si[(t[(i + s1) % b_c] >> 16) & 0xFF] ^ (tt >> 16)) & 0xFF)
            result.append((Si[(t[(i + s2) % b_c] >> 8) & 0xFF] ^ (tt >> 8)) & 0xFF)
            result.append((Si[t[(i + s3) % b_c] & 0xFF] ^ tt) & 0xFF)

        return bytes(result)


class RijndaelCbc(Rijndael):
    def __init__(
        self, key: bytes, iv: bytes, padding: PaddingBase, block_size: int = 16
    ):
        super().__init__(key=key, block_size=block_size)
        self.iv = iv
        self.padding = padding

    def encrypt(self, source: bytes) -> bytes:
        ppt = self.padding.encode(source)
        offset = 0

        ct = bytes()
        v = self.iv
        while offset < len(ppt):
            block = ppt[offset : offset + self.block_size]
            block = self.x_or_block(block, v)
            block = super().encrypt(block)
            ct += block
            offset += self.block_size
            v = block
        return ct

    def decrypt(self, cipher: bytes) -> bytes:
        assert len(cipher) % self.block_size == 0
        ppt = bytes()
        offset = 0
        v = self.iv
        while offset < len(cipher):
            block = cipher[offset : offset + self.block_size]
            decrypted = super().decrypt(block)
            ppt += self.x_or_block(decrypted, v)
            offset += self.block_size
            v = block
        pt = self.padding.decode(ppt)
        return pt

    def x_or_block(self, b1: bytes, b2: bytes) -> bytes:
        return bytes(b1[i] ^ b2[i] for i in range(self.block_size))
