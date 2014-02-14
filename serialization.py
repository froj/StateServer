from struct import *


class PIDConfig:
    hash = b'02020208'

    def __init__(self):
        self.kp = None  # float32
        self.ki = None  # float32
        self.kd = None  # float32

    @staticmethod
    def buffer_valid(buf):
        return True

    @classmethod
    def deserialize(cls, buf):
        if not PIDConfig.buffer_valid(buf):
            return None
        obj = cls()
        obj._deserialize(buf)
        return obj

    def _deserialize(self, buf):
        self.kp, = unpack_from('>f', buf, 0)
        self.ki, = unpack_from('>f', buf, 4)
        self.kd, = unpack_from('>f', buf, 8)

    def serialize(self):
        buf = []
        buf.append(pack('>f', self.kp))
        buf.append(pack('>f', self.ki))
        buf.append(pack('>f', self.kd))
        return b''.join(buf)
