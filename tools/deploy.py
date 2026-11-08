"""Nap firmware len ESP32 qua USB: bien dich module sang .mpy de bo nho Wi-Fi khong bi lan.

Bien dich tren board (.py) ton nhieu RAM lam heap Python no ra va khong tra lai.
config.py va main.py giu dang nguon de de sua. Dong Thonny truoc khi chay.

    pip install pyserial mpy-cross==1.29.0.post2   # dung phien ban MicroPython tren board
    python3 tools/deploy.py [/dev/ttyUSB0]
"""
import hashlib
import os
import subprocess
import sys
import tempfile
import time

import serial

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ONLY = ('config.py', 'main.py')


class Board:
    def __init__(self, port):
        self.rx = b''
        self.s = serial.Serial(port, 115200, timeout=0.2)
        time.sleep(1)
        for _ in range(3):
            self.s.write(b'\x03')
            time.sleep(0.2)
        self.s.reset_input_buffer()
        self.s.write(b'\r\x01')
        self._until(b'raw REPL; CTRL-B to exit\r\n>', 5)
        self.s.write(b'\x04')  # Khoi dong mem trong raw REPL: khong chay main.py.
        self._until(b'raw REPL; CTRL-B to exit\r\n>', 15)

    def _until(self, marker, timeout):
        # Giu phan doc lo: mot lan read co the chua nhieu marker lien nhau.
        data, self.rx = self.rx, b''
        end = time.time() + timeout
        while marker not in data:
            if time.time() > end:
                raise TimeoutError('khong thay %r' % marker)
            data += self.s.read(256)
        head, self.rx = data.split(marker, 1)
        return head

    def run(self, code, timeout=20):
        code = code.encode()
        for i in range(0, len(code), 128):
            self.s.write(code[i:i + 128])
            time.sleep(0.01)
        self.s.write(b'\x04')
        self._until(b'OK', 5)
        out = self._until(b'\x04', timeout)
        err = self._until(b'\x04', 5)
        self._until(b'>', 2)
        if err.strip():
            raise RuntimeError(err.decode('utf-8', 'replace'))
        return out.decode('utf-8', 'replace')

    def put(self, data, path):
        self.run("f=open(%r,'wb')" % (path + '.tmp'))
        for i in range(0, len(data), 256):
            self.run('f.write(bytes.fromhex(%r))' % data[i:i + 256].hex())
        self.run("f.close()\nimport os\ntry:\n    os.remove(%r)\nexcept OSError:\n    pass\nos.rename(%r,%r)" % (path, path + '.tmp', path))
        got = self.run("import hashlib,binascii\nh=hashlib.sha256()\nf=open(%r,'rb')\nwhile True:\n    d=f.read(512)\n    if not d: break\n    h.update(d)\nf.close()\nprint(binascii.hexlify(h.digest()).decode())" % path, 60).strip()
        if got != hashlib.sha256(data).hexdigest():
            raise RuntimeError('doc lai khong khop: ' + path)
        print('nap + doc lai khop', path, len(data))

    def remove(self, path):
        self.run("import os\ntry:\n    os.remove(%r)\nexcept OSError:\n    pass" % path)


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyUSB0'
    source_dir = os.path.join(ROOT, 'firmware')
    modules = sorted(f for f in os.listdir(source_dir) if f.endswith('.py') and f not in SOURCE_ONLY)
    board = None
    with tempfile.TemporaryDirectory() as tmp:
        compiled = []
        for name in modules:  # Bien dich het truoc: loi cu phap thi chua dung vao board.
            target = os.path.join(tmp, name[:-3] + '.mpy')
            subprocess.run([sys.executable, '-m', 'mpy_cross', '-o', target, os.path.join(source_dir, name)], check=True)
            compiled.append((name, target))
        board = Board(port)
        try:
            for name, target in compiled:
                board.put(open(target, 'rb').read(), '/' + name[:-3] + '.mpy')
                board.remove('/' + name)  # .py duoc uu tien hon .mpy khi import.
            for name in SOURCE_ONLY:
                board.put(open(os.path.join(source_dir, name), 'rb').read(), '/' + name)
            board.put(open(os.path.join(source_dir, 'web', 'index.html'), 'rb').read(), '/web/index.html')
            board.put(open(os.path.join(ROOT, 'tools', 'calibrate_track.py'), 'rb').read(), '/calibrate_track.py')
            board.s.write(b"import machine\nmachine.reset()\n\x04")
            time.sleep(0.3)
        finally:
            board.s.close()
    print('Da nap xong, board dang khoi dong lai.')


if __name__ == '__main__':
    main()
