"""HTTP nho, gioi han request; stream bat dong bo de PID tiep tuc chay."""
import asyncio
import json
import os
import binascii
import errno
from boot_info import BootInfo
from http_transport import SocketServer


class HTTPError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


class FileBody:
    def __init__(self, path):
        self.path = path
        self.size = os.stat(path)[6]

    def __len__(self):
        return self.size


class WebServer:
    MAX_LOGINS = 4

    def __init__(self, robot, config, html):
        self.robot, self.config, self.html = robot, config, html
        self.active_clients = 0
        self.server = None
        self.logins = {}
        self.login_order = 0
        self.control_owner = None
        self.control_session = None
        self.boot_info = BootInfo()

    async def start(self, host='0.0.0.0', port=80):
        self.server = SocketServer(self.handle, host, port, 4, self.transport_error)
        self.server.start()
        await asyncio.sleep(0)

    def transport_error(self, error):
        self.robot.stop('network_io_error')
        self.control_owner = self.control_session = None
        print('HTTP I/O error:', error)

    def close_nowait(self):
        if self.server:
            self.server.close()

    async def close(self):
        self.close_nowait()
        if self.server:
            await self.server.wait_closed()

    async def read_request(self, reader):
        data = b''
        while b'\r\n\r\n' not in data:
            chunk = await reader.read(128)
            if not chunk:
                raise HTTPError(400, 'incomplete_headers')
            data += chunk
            if len(data) > 4096:
                raise HTTPError(431, 'headers_too_large')
        head, body = data.split(b'\r\n\r\n', 1)
        lines = head.split(b'\r\n')
        parts = lines[0].split()
        if len(parts) != 3 or parts[2] not in (b'HTTP/1.1', b'HTTP/1.0'):
            raise HTTPError(400, 'bad_request')
        headers = {}
        for line in lines[1:]:
            if b':' not in line:
                raise HTTPError(400, 'bad_header')
            key, value = line.split(b':', 1)
            key = key.strip().lower()
            if key in headers:
                raise HTTPError(400, 'duplicate_header')
            headers[key] = value.strip()
        if b'transfer-encoding' in headers:
            raise HTTPError(400, 'chunked_not_supported')
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            raise HTTPError(400, 'bad_length')
        if length < 0 or length > 512:
            raise HTTPError(413, 'body_too_large')
        while len(body) < length:
            chunk = await reader.read(length - len(body))
            if not chunk:
                raise HTTPError(400, 'incomplete_body')
            body += chunk
        return parts[0], parts[1].split(b'?', 1)[0], headers, body[:length]

    def forget_login(self, token):
        self.logins.pop(token, None)
        if self.control_owner == token:
            self.robot.release(self.control_session)
            self.control_owner = self.control_session = None

    def authenticate(self, headers):
        value = headers.get(b'authorization', b'')
        try:
            token = value[7:].decode('ascii') if value.startswith(b'Bearer ') else ''
        except UnicodeError:
            token = ''
        if not token or token not in self.logins:
            raise HTTPError(401, 'login_required')
        self.login_order += 1
        self.logins[token] = self.login_order
        return token

    def login(self, data):
        if (not self.config.LOGIN_USERNAME or not self.config.LOGIN_PASSWORD
                or data.get('username') != self.config.LOGIN_USERNAME
                or data.get('password') != self.config.LOGIN_PASSWORD):
            raise HTTPError(401, 'invalid_credentials')
        if len(self.logins) >= self.MAX_LOGINS:
            # Gioi han RAM; chi thay the phien it dung khong dang giu xe.
            candidates = [key for key in self.logins if key != self.control_owner]
            if not candidates:
                raise HTTPError(429, 'too_many_logins')
            oldest = min(candidates, key=lambda key: self.logins[key])
            self.forget_login(oldest)
        token = binascii.hexlify(os.urandom(24)).decode()
        self.login_order += 1
        self.logins[token] = self.login_order
        return {'token': token, 'username': self.config.LOGIN_USERNAME,
                'boot': self.boot_info.snapshot()}

    def route(self, method, path, headers, body):
        if method == b'GET' and path == b'/':
            return 200, 'text/html; charset=utf-8', self.html
        if method == b'GET' and path == b'/api/status':
            self.authenticate(headers)
            self.robot.check_timeout()
            result = self.robot.status()
            result['boot'] = self.boot_info.snapshot()
            return 200, 'application/json', json.dumps(result).encode()
        if method == b'GET' and path == b'/api/ping':
            return 200, 'application/json', json.dumps({
                'message': 'ESP32 online', 'boot': self.boot_info.snapshot()}).encode()
        if path not in (b'/api/login', b'/api/logout', b'/api/arm', b'/api/control', b'/api/stop'):
            raise HTTPError(404, 'not_found')
        if method != b'POST':
            raise HTTPError(405, 'use_post')
        token = self.authenticate(headers) if path != b'/api/login' else None
        if headers.get(b'content-type', b'').split(b';', 1)[0] != b'application/json':
            raise HTTPError(415, 'use_application_json')
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError('expected_object')
        except (ValueError, TypeError):
            raise HTTPError(400, 'invalid_json')
        try:
            if path == b'/api/login':
                result = self.login(data)
            elif path == b'/api/logout':
                self.forget_login(token)
                result = {'ok': True}
            elif path == b'/api/arm':
                result = {'session': self.robot.arm()}
                self.control_owner = token
                self.control_session = result['session']
            elif path == b'/api/control':
                if token != self.control_owner:
                    raise HTTPError(403, 'not_control_owner')
                self.robot.command(data.get('session'), data.get('sequence'),
                                   data.get('throttle'), data.get('steering'), data.get('max_rpm'))
                result = {'ok': True}
            else:
                if token != self.control_owner:
                    raise HTTPError(403, 'not_control_owner')
                self.robot.release(data.get('session'))
                result = {'ok': True}
        except ValueError as error:
            raise HTTPError(409, str(error))
        return 200, 'application/json', json.dumps(result).encode()

    async def respond(self, writer, status, content_type, body):
        reason = {200: 'OK', 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found',
                  405: 'Method Not Allowed', 408: 'Request Timeout', 409: 'Conflict',
                  413: 'Payload Too Large', 415: 'Unsupported Media Type',
                  429: 'Too Many Requests', 431: 'Request Header Fields Too Large', 500: 'Internal Server Error',
                  503: 'Service Unavailable'}.get(status, 'Error')
        header = ('HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n'
                  'Cache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n'
                  'Connection: close\r\n\r\n') % (status, reason, content_type, len(body))
        writer.write(header.encode())
        await writer.drain()
        if isinstance(body, FileBody):
            with open(body.path, 'rb') as page:
                while True:
                    chunk = page.read(1024)
                    if not chunk:
                        break
                    writer.write(chunk)
                    await writer.drain()
        else:
            for offset in range(0, len(body), 1024):
                writer.write(body[offset:offset + 1024])
                await writer.drain()

    async def close_client(self, writer):
        try:
            writer.close()
            # MicroPython Stream.close() does not close the socket itself.
            await asyncio.wait_for(writer.wait_closed(), 0.2)
        except (OSError, asyncio.TimeoutError):
            pass

    async def handle(self, reader, writer):
        if self.active_clients >= 4:
            await self.close_client(writer)
            return
        self.active_clients += 1
        try:
            try:
                request = await asyncio.wait_for(self.read_request(reader), 2)
                status, content_type, body = self.route(*request)
            except HTTPError as error:
                status, content_type, body = error.status, 'application/json', json.dumps({
                    'error': error.message, 'boot': self.boot_info.snapshot()}).encode()
            except asyncio.TimeoutError:
                status, content_type, body = 408, 'application/json', b'{"error":"request_timeout"}'
            except OSError:
                raise
            except Exception as error:
                self.robot.stop('server_error')
                print('HTTP error:', error)
                status, content_type, body = 500, 'application/json', b'{"error":"server_error"}'
            await asyncio.wait_for(self.respond(writer, status, content_type, body), 2)
        except (OSError, asyncio.TimeoutError) as error:
            if isinstance(error, OSError) and error.args and error.args[0] == errno.EIO:
                self.transport_error(error)
        finally:
            try:
                await self.close_client(writer)
            finally:
                self.active_clients -= 1
