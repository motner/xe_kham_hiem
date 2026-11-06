"""HTTP sockets nonblocking; socket errors stay inside tasks, outside asyncio's poller."""
import asyncio
import errno
import socket


WOULD_BLOCK = (errno.EAGAIN, getattr(errno, 'EWOULDBLOCK', errno.EAGAIN),
               getattr(errno, 'EINPROGRESS', errno.EAGAIN))
# Trinh duyet huy ket noi truoc khi accept: chuyen binh thuong, listener van tot.
ACCEPT_RETRY = WOULD_BLOCK + (getattr(errno, 'ECONNABORTED', errno.EAGAIN),)
ACCEPT_IDLE_S = 0.025  # Moi lan accept khong co gi la mot exception: khong hoi qua day.


def collect_garbage():
    try:
        import gc
        gc.collect()
    except ImportError:
        pass


async def pause():
    await asyncio.sleep(0.01)


class SocketStream:
    def __init__(self, sock):
        self.sock = sock
        self.closed = False
        self.buffer = b''

    async def read(self, size):
        while not self.closed:
            try:
                return self.sock.recv(size)
            except OSError as error:
                if not error.args or error.args[0] not in WOULD_BLOCK:
                    raise
            await pause()
        return b''

    def write(self, data):
        if self.closed:
            raise OSError(errno.EPIPE)
        # Khong sao chep khi buffer rong: moi lan ghep can mot doan RAM lien moi.
        self.buffer = self.buffer + data if self.buffer else data

    async def drain(self):
        data = memoryview(self.buffer)
        offset = 0
        while offset < len(data):
            if self.closed:
                raise OSError(errno.EPIPE)
            try:
                sent = self.sock.send(data[offset:])
                if sent == 0:
                    raise OSError(errno.EPIPE)
                offset += sent
            except OSError as error:
                if not error.args or error.args[0] not in WOULD_BLOCK:
                    raise
                await pause()
        self.buffer = b''
        # Yield even when a complete chunk fits in the socket send buffer.
        await asyncio.sleep(0)

    def close(self):
        if not self.closed:
            self.closed = True
            self.buffer = b''
            self.sock.close()

    async def wait_closed(self):
        self.close()


class SocketServer:
    def __init__(self, callback, host, port, backlog, on_error):
        self.callback = callback
        self.host, self.port, self.backlog = host, port, backlog
        self.on_error = on_error
        self.listener = None
        self.clients = {}
        self.task = None
        self.closed = False

    def open_listener(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.setblocking(False)
            listener.bind((self.host, self.port))
            listener.listen(self.backlog)
        except BaseException:
            listener.close()
            raise
        self.listener = listener

    def start(self):
        self.open_listener()
        self.task = asyncio.create_task(self.serve())

    async def handle_client(self, stream):
        try:
            await self.callback(stream, stream)
        finally:
            try:
                stream.close()
            except OSError:
                pass
            self.clients.pop(stream, None)

    def close_clients(self):
        for stream, task in tuple(self.clients.items()):
            task.cancel()
            try:
                stream.close()
            except OSError:
                pass

    async def serve(self):
        while not self.closed:
            try:
                if self.listener is None:
                    self.open_listener()
                sock, _ = self.listener.accept()
            except Exception as error:
                if (isinstance(error, OSError) and error.args
                        and error.args[0] in ACCEPT_RETRY):
                    await asyncio.sleep(ACCEPT_IDLE_S)
                    continue
                if isinstance(error, MemoryError):
                    # Thieu RAM khong phai loi listener: don RAM va thu lai.
                    collect_garbage()
                    await asyncio.sleep(0.25)
                    continue
                # A failed listener is rebuilt without resetting Wi-Fi or rearming.
                if self.on_error:
                    self.on_error(error)
                self.close_clients()
                if self.listener:
                    try:
                        self.listener.close()
                    except OSError:
                        pass
                    self.listener = None
                await asyncio.sleep(0.25)
                continue
            try:
                sock.setblocking(False)
                if len(self.clients) >= self.backlog:
                    sock.close()
                else:
                    stream = SocketStream(sock)
                    self.clients[stream] = asyncio.create_task(self.handle_client(stream))
            except Exception as error:
                # MemoryError etc. must not kill the accept task: HTTP would stay dead
                # while the PID loop keeps running.
                try:
                    sock.close()
                except OSError:
                    pass
                if self.on_error and not isinstance(error, MemoryError):
                    self.on_error(error)
                collect_garbage()
                await asyncio.sleep(0.25)
                continue
            await asyncio.sleep(0)

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.task:
            self.task.cancel()
        self.close_clients()
        if self.listener:
            try:
                self.listener.close()
            except OSError:
                pass
            self.listener = None

    async def wait_closed(self):
        if self.task:
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        for task in tuple(self.clients.values()):
            try:
                await task
            except (asyncio.CancelledError, OSError):
                pass


async def start_server(callback, host, port, backlog=4, on_error=None):
    server = SocketServer(callback, host, port, backlog, on_error)
    try:
        server.start()
        await asyncio.sleep(0)
    except BaseException:
        server.close()
        raise
    return server
