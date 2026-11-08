"""Socket EIO must stop the lease, close its connection and leave HTTP usable."""
import asyncio
import errno
import json
import pathlib
import sys
import types
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'firmware'))
from http_transport import SocketStream
from web_server import WebServer, FileBody
import main


class ScriptedSocket:
    def __init__(self, reads=(), sends=()):
        self.reads, self.sends = list(reads), list(sends)
        self.output = bytearray()
        self.closed = False

    def recv(self, size):
        value = self.reads.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value

    def send(self, data):
        value = self.sends.pop(0) if self.sends else len(data)
        if isinstance(value, BaseException):
            raise value
        self.output.extend(data[:value])
        return value

    def close(self):
        self.closed = True


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.robot = types.SimpleNamespace(stop=Mock())
        self.web = WebServer(self.robot, types.SimpleNamespace(), b'<html>test</html>')

    async def asyncTearDown(self):
        await self.web.close()

    async def request_ping(self):
        port = self.web.server.listener.getsockname()[1]
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        try:
            writer.write(b'GET /api/ping HTTP/1.1\r\nHost: esp32\r\n\r\n')
            await writer.drain()
            response = await asyncio.wait_for(reader.read(), 1)
            head, body = response.split(b'\r\n\r\n', 1)
            self.assertIn(b'200 OK', head)
            self.assertEqual(json.loads(body)['message'], 'ESP32 online')
        finally:
            writer.close()
            await writer.wait_closed()

    async def test_partial_io_and_would_block_yield_without_losing_data(self):
        sock = ScriptedSocket([OSError(errno.EAGAIN), b'hello'],
                              [2, OSError(errno.EAGAIN), 3])
        stream = SocketStream(sock)
        self.assertEqual(await stream.read(20), b'hello')
        stream.write(b'hello')
        await stream.drain()
        self.assertEqual(sock.output, b'hello')
        stream.close()
        self.assertEqual(await stream.read(20), b'')
        self.assertTrue(sock.closed)

    async def test_peer_closed_during_write_fails_instead_of_spinning(self):
        stream = SocketStream(ScriptedSocket(sends=[0]))
        stream.write(b'hello')
        with self.assertRaises(OSError):
            await asyncio.wait_for(stream.drain(), .2)
        stream.close()

    async def test_read_and_write_eio_stop_control_and_http_keeps_working(self):
        await self.web.start('127.0.0.1', 0)
        for mode in ('read', 'write'):
            with self.subTest(mode=mode):
                sock = ScriptedSocket([OSError(errno.EIO)] if mode == 'read' else
                                      [b'GET /api/ping HTTP/1.1\r\n\r\n'],
                                      [OSError(errno.EIO)] if mode == 'write' else [])
                stream = SocketStream(sock)
                self.web.control_owner, self.web.control_session = 'owner', 'lease'
                await self.web.handle(stream, stream)
                self.robot.stop.assert_called_with('network_io_error')
                self.assertIsNone(self.web.control_owner)
                self.assertIsNone(self.web.control_session)
                self.assertTrue(sock.closed)
                self.assertEqual(self.web.active_clients, 0)
                await self.request_ping()

    async def test_listener_eio_rebuilds_listener_and_http_recovers(self):
        await self.web.start('127.0.0.1', 0)
        server = self.web.server
        port = server.listener.getsockname()[1]
        server.port = port
        original = server.listener
        fault_seen = asyncio.Event()
        callback = server.on_error

        def on_error(error):
            callback(error)
            fault_seen.set()

        class BrokenListener:
            def accept(self):raise OSError(errno.EIO)
            def close(self):original.close()

        server.on_error = on_error
        server.listener = BrokenListener()
        await asyncio.wait_for(fault_seen.wait(), 1)
        await asyncio.sleep(.3)
        self.robot.stop.assert_called_with('network_io_error')
        self.assertFalse(server.task.done())
        await self.request_ping()

    async def test_memory_error_while_accepting_does_not_kill_server(self):
        await self.web.start('127.0.0.1', 0)
        server = self.web.server
        original = server.listener
        raised = asyncio.Event()

        class FlakyListener:
            def accept(self):
                raised.set()
                server.listener = original
                raise MemoryError()
            def close(self):original.close()

        server.listener = FlakyListener()
        await asyncio.wait_for(raised.wait(), 1)
        await asyncio.sleep(.3)
        # Thieu RAM khong phai loi listener: giu nguyen listener, khong dung xe.
        self.assertNotIn(unittest.mock.call('network_io_error'), self.robot.stop.call_args_list)
        self.assertIs(server.listener, original)
        self.assertFalse(server.task.done())
        await self.request_ping()

    async def test_aborted_connection_while_accepting_keeps_listener_and_robot(self):
        await self.web.start('127.0.0.1', 0)
        server = self.web.server
        original = server.listener
        raised = asyncio.Event()

        class AbortingListener:
            def accept(self):
                raised.set()
                server.listener = original
                raise OSError(errno.ECONNABORTED, 'ECONNABORTED')
            def close(self):original.close()

        server.listener = AbortingListener()
        await asyncio.wait_for(raised.wait(), 1)
        await asyncio.sleep(.1)
        self.assertNotIn(unittest.mock.call('network_io_error'), self.robot.stop.call_args_list)
        self.assertIs(server.listener, original)
        await self.request_ping()

    async def test_low_memory_in_route_returns_503_without_stopping(self):
        await self.web.start('127.0.0.1', 0)
        port = self.web.server.listener.getsockname()[1]
        self.web.route = unittest.mock.Mock(side_effect=MemoryError('alloc'))
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b'GET /api/ping HTTP/1.1\r\nHost: x\r\n\r\n')
        await writer.drain()
        reply = await asyncio.wait_for(reader.read(), 2)
        writer.close()
        self.assertTrue(reply.startswith(b'HTTP/1.1 503'), reply[:40])
        self.assertNotIn(unittest.mock.call('server_error'), self.robot.stop.call_args_list)

    async def test_shutdown_closes_incomplete_requests(self):
        await self.web.start('127.0.0.1', 0)
        port = self.web.server.listener.getsockname()[1]
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        writer.write(b'GET /api/ping HTTP/1.1\r\n')
        await writer.drain()
        await asyncio.sleep(.03)
        await self.web.close()
        self.assertEqual(await asyncio.wait_for(reader.read(), 1), b'')
        self.assertFalse(self.web.server.clients)
        self.assertEqual(self.web.active_clients, 0)
        writer.close()
        await writer.wait_closed()

    async def test_large_page_streams_in_bounded_reads_and_closes_on_abort(self):
        payload=b'0123456789abcdef'*4096
        for abort in (False, True):
            with self.subTest(abort=abort), tempfile.TemporaryDirectory() as directory:
                path=pathlib.Path(directory)/'index.html'
                path.write_bytes(payload)
                body=FileBody(str(path))
                reads=[]
                opened=[]
                real_open=open

                class BoundedFile:
                    def __init__(self):self.file=real_open(path,'rb');opened.append(self.file)
                    def __enter__(self):return self
                    def __exit__(self,*args):self.file.close()
                    def read(self,size):
                        self.assert_size(size)
                        reads.append(size)
                        return self.file.read(size)
                    def assert_size(self,size):
                        if not 0<size<=1024:raise AssertionError('Unbounded HTML read')

                class Writer:
                    def __init__(self):self.data=bytearray();self.drains=0
                    def write(self,data):self.data.extend(data)
                    async def drain(self):
                        self.drains+=1
                        if abort and self.drains==3:raise OSError(errno.EPIPE)
                        await asyncio.sleep(0)

                writer=Writer()
                with patch('web_server.open',lambda *args:BoundedFile(),create=True):
                    if abort:
                        with self.assertRaises(OSError):await self.web.respond(writer,200,'text/html',body)
                    else:
                        await self.web.respond(writer,200,'text/html',body)
                        head,received=bytes(writer.data).split(b'\r\n\r\n',1)
                        self.assertEqual(received,payload)
                        self.assertIn(('Content-Length: '+str(len(payload))).encode(),head)
                self.assertTrue(reads)
                self.assertTrue(all(f.closed for f in opened))


class MainCleanupTests(unittest.TestCase):
    def test_scheduler_failure_also_releases_listener_without_async_cleanup(self):
        robot, server = Mock(), Mock()

        class Pause:
            def __await__(self):yield None

        async def interrupted_run(robot, resources):
            resources['server']=server
            await Pause()

        def failed_scheduler(coro):
            coro.send(None)
            coro.close()
            raise OSError(errno.EIO)

        with patch.object(main,'build_robot',return_value=robot), \
             patch.object(main,'run',interrupted_run), \
             patch.object(main.asyncio,'run',side_effect=failed_scheduler), \
             patch.object(main.asyncio,'new_event_loop'):
            with self.assertRaises(OSError):main.main()
        robot.close.assert_called_once()
        server.close_nowait.assert_called_once()

    def test_scheduler_exception_cannot_skip_motor_cleanup(self):
        for error in (OSError(errno.EIO), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                robot = Mock()

                def failed_scheduler(coro):
                    # The coroutine's own finally block never gets to execute.
                    coro.close()
                    raise error

                with patch.object(main, 'build_robot', return_value=robot), \
                     patch.object(main.asyncio, 'run', side_effect=failed_scheduler), \
                     patch.object(main.asyncio, 'new_event_loop') as new_loop:
                    with self.assertRaises(type(error)):
                        main.main()
                robot.close.assert_called_once()
                new_loop.assert_called_once()


class JsonBufferTests(unittest.TestCase):
    def setUp(self):
        from web_server import JsonBuffer
        self.buffer = JsonBuffer(64)

    def test_output_is_valid_json(self):
        data = {'a': 1, 'b': [1.5, None], 'c': {'d': 'x'}}
        self.assertEqual(json.loads(bytes(self.buffer.encode(data))), data)

    def test_busy_until_released_then_reusable(self):
        self.assertIsNotNone(self.buffer.encode({'a': 1}))
        self.assertIsNone(self.buffer.encode({'a': 2}))
        self.buffer.release()
        self.assertEqual(json.loads(bytes(self.buffer.encode({'a': 2}))), {'a': 2})

    def test_too_large_returns_none_and_stays_free(self):
        self.assertIsNone(self.buffer.encode({'a': 'x' * 100}))
        self.assertFalse(self.buffer.busy)
        self.assertIsNotNone(self.buffer.encode({'a': 1}))


if __name__ == '__main__':
    unittest.main()
