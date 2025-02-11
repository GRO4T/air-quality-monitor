import time
import struct
from typing import NamedTuple

from serial import Serial


START_OF_FRAME = bytearray(b"\x42\x4d")
SENSOR_RESPONSE_TIME_IN_SECONDS = 10


class Particles(NamedTuple):
    v_03um: int
    v_05um: int
    v_10um: int
    v_25um: int
    v_50um: int
    v_100um: int


class ParticulateMatter(NamedTuple):
    v_1_0: int
    v_2_5: int
    v_10_0: int


class SensorError(RuntimeError):
    pass


class Measurement(NamedTuple):
    pm_standard: ParticulateMatter
    pm_atmospheric: ParticulateMatter
    particles: Particles


_Frame = bytearray


class Sensor:
    def __init__(self, serial_port: Serial):
        self._port = serial_port

    @property
    def port(self) -> Serial:
        return self._port

    def get_measurement(self) -> Measurement:
        self._wait_for_frame()
        frame = self._read_frame()
        self._verify_checksum(frame)
        return self._parse(frame)

    def _wait_for_frame(self):
        wait_time = 0
        sof_idx = 0
        start = time.time()

        while wait_time < SENSOR_RESPONSE_TIME_IN_SECONDS:
            wait_time += time.time() - start
            start = time.time()
            byte = self._port.read(1)
            if not byte:
                continue
            if ord(byte) == START_OF_FRAME[sof_idx]:
                sof_idx += 1
                if sof_idx == len(START_OF_FRAME):
                    return
            elif sof_idx > 0:
                sof_idx = 0

        raise SensorError(
            f"No frame received for {SENSOR_RESPONSE_TIME_IN_SECONDS} sec"
        )

    def _read_frame(self) -> _Frame:
        frame = _Frame()

        data = self._port.read(2)
        frame_len = struct.unpack(">H", data)[0]
        frame += data

        data = self._port.read(frame_len)
        if len(data) != frame_len:
            raise SensorError(
                f"Expected a frame of size {frame_len}. Got {len(data)} bytes"
            )
        frame += data

        return frame

    def _verify_checksum(self, frame: _Frame):
        checksum = sum(START_OF_FRAME) + sum(frame[:-2])
        expected_checksum = struct.unpack(">H", frame[-2:])[0]
        if checksum != expected_checksum:
            raise SensorError(f"Invalid checksum: {checksum} != {expected_checksum}")

    def _parse(self, frame: _Frame) -> Measurement:
        data = struct.unpack(">" + "H" * (len(frame[2:]) // 2), frame[2:])

        return Measurement(
            pm_standard=ParticulateMatter(*data[0:3]),
            pm_atmospheric=ParticulateMatter(*data[3:6]),
            particles=Particles(*data[6:12]),
        )
