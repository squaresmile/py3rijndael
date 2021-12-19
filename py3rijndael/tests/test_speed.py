import base64
import unittest
import time
from pathlib import Path

from py3rijndael import RijndaelCbc, Pkcs7Padding


class RijndaelCbcTestSpeed(unittest.TestCase):
    def test_rijndael_cbc(self) -> None:
        key = "qBS8uRhEIBsr8jr8vuY9uUpGFefYRL2HSTtrKhaI1tk="
        iv = "kByhT6PjYHzJzZfXvb8Aw5URMbQnk6NM+g3IV5siWD4="
        rijndael_cbc = RijndaelCbc(
            key=base64.b64decode(key),
            iv=base64.b64decode(iv),
            padding=Pkcs7Padding(32),
            block_size=32,
        )
        with open(Path(__file__).parent / "lorem_ipsum.txt", "rb") as f:
            plain_text = f.read()

        TIMES = 100
        start_time = time.perf_counter()
        for _ in range(TIMES):
            cipher = rijndael_cbc.encrypt(plain_text)
            plain_text = rijndael_cbc.decrypt(cipher)
        end_time = time.perf_counter()
        print(f"\n{TIMES} encryptions in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":  # pragma: nocover
    unittest.main()
