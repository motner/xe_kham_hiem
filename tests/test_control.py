"""Host tests: python3 -m unittest discover -s tests -v (khong can ESP32)."""
import asyncio
import importlib
import json
import math
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'firmware'))
import config
from pid import PID
from robot import Robot
from wheel import Wheel
from web_server import WebServer, HTTPError


class MotorFake:
    def __init__(self): self.output = 0
    def set_output(self, x): self.output = x
    def stop(self): self.output = 0
    def close(self): self.stop()


class EncoderFake:
    def __init__(self):
        self.rpm = 0
        self.b = None
        self.pulses = 0
        self.counts_per_rev = 100
        self.no_pulse_seconds = 0
    def sample(self, dt): return True
    def close(self): pass


def make_wheel(name='test'):
    return Wheel(name, MotorFake(), EncoderFake(), {'pid': (.01, .02, 0), 'diameter_mm': 65}, config)


class PIDTests(unittest.TestCase):
    def test_saturation_does_not_wind_up(self):
        pid = PID(.1, .5, 0, limit=.35)
        for _ in range(1000):
            self.assertLessEqual(pid.update(100, 0, .05), .35)
        self.assertEqual(pid.integral, 0)
        self.assertEqual(pid.update(0, 100, .05), 0)

    def test_reset_and_bad_dt(self):
        pid = PID(.01, .02, .001)
        pid.update(10, 9, .05)
        pid.reset()
        self.assertEqual(pid.integral, 0)
        self.assertIsNone(pid.previous_measurement)
        for dt in (0, -1, float('nan')):
            with self.assertRaises(ValueError): pid.update(10, 0, dt)

    def test_tracks_simple_motor_plant(self):
        pid = PID(.006, .015, 0, limit=.8)
        rpm = 0
        for _ in range(1000):
            duty = pid.update(80, rpm, .05)
            rpm += (duty * 200 - rpm) * .1
        self.assertAlmostEqual(rpm, 80, delta=.1)


class WheelTests(unittest.TestCase):
    def test_ramp_and_stop(self):
        w = make_wheel(); w.set_target_rpm(100); w.update(.05)
        self.assertEqual(w.target, 5)
        self.assertGreater(w.motor.output, 0)
        w.stop(); self.assertEqual(w.motor.output, 0); self.assertEqual(w.pid.integral, 0)

    def test_reversal_waits_until_coast_and_low_rpm(self):
        w = make_wheel(); w.set_target_rpm(100); w.update(.05)
        w.encoder.rpm = 30; w.set_target_rpm(-100)
        for _ in range(12): w.update(.05); self.assertEqual(w.motor.output, 0)
        w.encoder.rpm = 0; w.update(.05)
        self.assertLess(w.motor.output, 0)

    def test_stop_does_not_forget_previous_direction(self):
        w=make_wheel(); w.set_target_rpm(100); w.update(.05); w.stop()
        w.set_target_rpm(-100); w.update(.05)
        self.assertEqual(w.motor.output, 0)

    def test_no_encoder_pulses_latches_fault(self):
        w = make_wheel(); w.set_target_rpm(100); w.encoder.no_pulse_seconds = 10
        for _ in range(60): w.update(.05)
        self.assertIn('encoder_or_stall', w.fault)
        self.assertEqual(w.motor.output, 0)
        w.set_target_rpm(50); w.update(.05); self.assertEqual(w.motor.output, 0)


class RobotTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.wheels = [make_wheel(name) for name in ('front_left','rear_left','rear_right','front_right')]
        self.robot = Robot(self.wheels, config, clock=lambda: self.now)
        self.session = self.robot.arm()
    def command(self, seq=0, throttle=1, steering=0, maximum=100):
        self.robot.command(self.session, seq, throttle, steering, maximum)

    def test_mix_and_stop(self):
        self.command(throttle=.5, steering=.5)
        self.assertEqual([w.requested for w in self.wheels], [100,100,0,0])
        self.command(seq=1,throttle=0,steering=0)
        self.assertTrue(all(w.motor.output == 0 for w in self.wheels))

    def test_normalization_respects_limit(self):
        self.command(throttle=1,steering=1)
        self.assertEqual(self.robot.left,100);self.assertEqual(self.robot.right,0)

    def test_deadman_rejects_delayed_command(self):
        self.command();self.robot.update(.05)
        self.now += config.COMMAND_TIMEOUT_MS + 1
        with self.assertRaises(ValueError): self.command(seq=1)
        self.assertIsNone(self.robot.session)
        self.assertTrue(all(w.motor.output == 0 for w in self.wheels))

    def test_stop_invalidates_session_and_old_release_cannot_stop_new(self):
        self.robot.release(self.session)
        with self.assertRaises(ValueError): self.command(seq=1)
        new = self.robot.arm();self.robot.release(self.session)
        self.assertEqual(self.robot.session,new)

    def test_bad_numbers_replay_and_multiple_controllers(self):
        self.command(seq=4)
        with self.assertRaises(ValueError):self.command(seq=3)
        with self.assertRaises(ValueError):self.robot.arm()
        for val in (float('nan'),float('inf'),2,None,True):
            with self.assertRaises(ValueError):self.command(seq=5,throttle=val)
        self.assertEqual(self.robot.sequence,4)

    def test_late_control_loop_stops_every_wheel(self):
        self.command();self.robot.update(.05)
        self.robot.update(1)
        self.assertEqual(self.robot.fault,'control_loop_late')
        self.assertTrue(all(w.motor.output == 0 for w in self.wheels))
        # Sau khi xe da dung, lan arm moi xoa loi tre vong lap thay vi chot den khi reboot.
        self.assertTrue(self.robot.arm())
        self.assertIsNone(self.robot.fault)
        self.robot.update(1)
        self.assertEqual(self.robot.fault,'control_loop_late')

    def test_stalled_wheel_can_retry_after_new_arm_but_other_faults_stay(self):
        wheel=self.wheels[0]
        wheel.fault='encoder_or_stall:'+wheel.name
        self.robot.stop()
        self.assertTrue(self.robot.arm())
        self.assertIsNone(wheel.fault)
        self.robot.release(self.robot.session)
        self.robot.fault='motor_stop_error'
        with self.assertRaises(ValueError):self.robot.arm()

    def test_low_target_wheel_gets_breakaway_duty_before_false_stall(self):
        wheel=make_wheel()
        wheel.set_target_rpm(8)
        for _ in range(5):wheel.update(.05)
        self.assertLess(wheel.motor.output,config.BREAKAWAY_DUTY)
        for _ in range(3):wheel.update(.05)
        self.assertGreaterEqual(wheel.motor.output,config.BREAKAWAY_DUTY)
        wheel.encoder.rpm=10
        wheel.update(.05)
        self.assertEqual(wheel.still_elapsed,0)
        self.assertIsNone(wheel.fault)

    def test_wheel_fault_stops_other_wheels(self):
        self.command();self.wheels[2].fault='bad_encoder';self.robot.update(.05)
        self.assertEqual(self.robot.fault,'bad_encoder')
        self.assertTrue(all(w.motor.output == 0 for w in self.wheels))

    def test_stall_test_mode_keeps_healthy_wheels_and_lease_running(self):
        with patch.object(config,'STOP_ALL_ON_ENCODER_STALL',False):
            self.wheels[0].encoder.no_pulse_seconds=10
            for seq in range(60):
                self.now+=50
                self.command(seq=seq)
                self.robot.update(.05)
            self.assertEqual(self.wheels[0].fault,'encoder_or_stall:front_left')
            self.assertEqual(self.wheels[0].motor.output,0)
            self.assertTrue(all(w.motor.output>0 for w in self.wheels[1:]))
            self.assertIsNone(self.robot.fault)
            self.assertEqual(self.robot.session,self.session)
            status=self.robot.status()
            self.assertTrue(status['motor_ready'])
            self.assertEqual(status['wheel_faults'],['encoder_or_stall:front_left'])
            self.assertFalse(status['stop_all_on_encoder_stall'])
            self.now+=config.COMMAND_TIMEOUT_MS+1
            self.robot.update(.05)
            self.assertIsNone(self.robot.session)
            self.assertTrue(all(w.motor.output==0 for w in self.wheels))

    def test_strict_mode_stops_all_on_encoder_stall(self):
        with patch.object(config,'STOP_ALL_ON_ENCODER_STALL',True):
            self.command()
            self.wheels[0].fault='encoder_or_stall:front_left'
            self.robot.update(.05)
            self.assertEqual(self.robot.fault,self.wheels[0].fault)
            self.assertIsNone(self.robot.session)
            self.assertTrue(all(w.motor.output==0 for w in self.wheels))

    def test_disabled_has_no_fake_readings(self):
        robot=Robot([],config)
        self.assertIsNone(robot.status()['wheels'])
        with self.assertRaises(ValueError):robot.arm()


class PinFake:
    IN=0;OUT=1;IRQ_RISING=1
    def __init__(self, pin, mode, value=0): self.pin=pin;self.level=value
    def value(self,*args):
        if args:self.level=args[0]
        return self.level
    def irq(self,**kwargs):self.handler=kwargs.get('handler')


class EncoderTests(unittest.TestCase):
    def test_rising_edges_rpm_rollover_and_signed_counts(self):
        from encoder import Encoder
        machine=types.SimpleNamespace(Pin=PinFake,disable_irq=lambda:0,enable_irq=lambda x:None)
        with patch.dict(sys.modules,{'machine':machine}):
            e=Encoder(1,None,100,filter_tau=0)
            for _ in range(15):e._irq(None)
            e.sample(.1);self.assertAlmostEqual(e.rpm,90);self.assertEqual(e.pulses,15)
            e.count=e.previous_count=e.MASK-2;e.travel_count=e.previous_travel=e.MASK-2
            for _ in range(5):e._irq(None)
            e.sample(.1);self.assertAlmostEqual(e.rpm,30);self.assertEqual(e.pulses,20)
            e2=Encoder(1,2,100,filter_tau=0);e2.b.level=0
            for _ in range(10):e2._irq(None)
            e2.sample(.1);self.assertAlmostEqual(e2.rpm,-60);self.assertEqual(e2.pulses,10)
            e2.close();self.assertIsNone(e2.a.handler)

    def test_edges_closer_than_min_interval_are_rejected(self):
        import encoder
        machine=types.SimpleNamespace(Pin=PinFake,disable_irq=lambda:0,enable_irq=lambda x:None)
        now=[0]
        fake_time=types.SimpleNamespace(ticks_us=lambda:now[0],ticks_diff=lambda a,b:a-b)
        with patch.dict(sys.modules,{'machine':machine}), patch.object(encoder,'time',fake_time):
            e=encoder.Encoder(1,None,20,filter_tau=0,min_interval_us=4000)
            for t in (0,100,1500,3999,4000,4050,9000,12000,15000):
                now[0]=t;e._irq(None)
            # Canh that 0, 4000, 9000 (12000 chi cach 3000), 15000 cach 9000 la 6000.
            self.assertEqual(e.travel_count,4)
            self.assertEqual(e.rejected,5)


class ConfigTests(unittest.TestCase):
    def test_default_does_not_touch_gpio(self):
        import main
        with patch.object(config, 'HARDWARE_ENABLED', False), patch.dict(sys.modules,{'machine':None}):
            robot=main.build_robot()
            self.assertFalse(robot.ready)
    def test_enabled_requires_complete_config(self):
        with patch.object(config,'HARDWARE_ENABLED',True), patch.object(config,'LOGIN_PASSWORD',''):
            with self.assertRaisesRegex(ValueError,'LOGIN_PASSWORD'):config.validate_hardware()
            with patch.object(config,'LOGIN_PASSWORD','test-password'), patch.object(config,'WHEELS',[
                dict(w, pid=None) for w in config.WHEELS
            ]):
                with self.assertRaisesRegex(ValueError,'pid='):config.validate_hardware()


class Reader:
    def __init__(self,data):self.data=data
    async def read(self,n):
        await asyncio.sleep(0)
        out,self.data=self.data[:min(n,7)],self.data[min(n,7):]
        return out
class Writer:
    def __init__(self):self.data=bytearray();self.closed=False
    def write(self,data):self.data.extend(data)
    async def drain(self):await asyncio.sleep(0)
    def close(self):self.closed=True
    async def wait_closed(self):pass


class WebTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cfg=types.SimpleNamespace(LOGIN_USERNAME='admin',LOGIN_PASSWORD='test-password')
        self.now=1000
        self.robot=Robot([make_wheel(str(i)) for i in range(4)],config,clock=lambda:self.now)
        self.server=WebServer(self.robot,self.cfg,b'<html>dashboard</html>')
        self.headers={b'content-type':b'application/json'}
        result=self.post(b'/api/login',{'username':'admin','password':'test-password'})
        self.token=json.loads(result[2])['token']
        self.headers[b'authorization']=('Bearer '+self.token).encode()
    def post(self,path,data):return self.server.route(b'POST',path,self.headers,json.dumps(data).encode())
    async def test_boot_report_public_and_available_after_auth_is_lost(self):
        self.server.boot_info.details={'reason':'brownout','brownout':True,'cause':1,'raw_cause':3}
        public=json.loads(self.server.route(b'GET',b'/api/ping',{},b'')[2])
        self.assertTrue(public['boot']['brownout'])
        self.assertNotIn('wheels',public)
        self.assertNotIn('token',public)
        self.assertNotIn('test-password',json.dumps(public))
        status=json.loads(self.server.route(b'GET',b'/api/status',self.headers,b'')[2])
        self.assertEqual(public['boot']['id'],status['boot']['id'])
        writer=Writer()
        await self.server.handle(Reader(b'GET /api/status HTTP/1.1\r\nHost: esp32\r\n\r\n'),writer)
        head,body=bytes(writer.data).split(b'\r\n\r\n',1)
        self.assertIn(b'401 Unauthorized',head)
        self.assertTrue(json.loads(body)['boot']['brownout'])
        self.assertIsNone(self.robot.session)

    async def test_api_arm_control_stop_and_auth(self):
        _,_,body=self.post(b'/api/arm',{})
        session=json.loads(body)['session']
        self.post(b'/api/control',{'session':session,'sequence':1,'throttle':.5,'steering':0,'max_rpm':80})
        self.assertEqual(self.robot.left,40)
        self.post(b'/api/stop',{'session':session});self.assertIsNone(self.robot.session)
        with self.assertRaises(HTTPError) as ctx:self.server.route(b'POST',b'/api/arm',{},b'{}')
        self.assertEqual(ctx.exception.status,401)
        status=json.loads(self.server.route(b'GET',b'/api/status',self.headers,b'')[2])
        self.assertNotIn('session',status);self.assertNotIn('token',status);self.assertNotIn('LOGIN_PASSWORD',status)
    async def test_login_is_required_for_every_control_endpoint(self):
        for headers in ({}, {b'x-control-key':b'old-key'}, {b'authorization':b'Bearer invented'}):
            for method,path in ((b'GET',b'/api/status'),(b'POST',b'/api/arm'),(b'POST',b'/api/control'),(b'POST',b'/api/stop'),(b'POST',b'/api/logout')):
                with self.assertRaises(HTTPError) as ctx:
                    self.server.route(method,path,headers,b'{}')
                self.assertEqual(ctx.exception.status,401)
        self.assertIsNone(self.robot.session)

    async def test_login_rejects_wrong_credentials_without_arming(self):
        for data in ({}, {'username':'wrong','password':'test-password'}, {'username':'admin','password':'wrong'}, {'username':['admin'],'password':123}):
            with self.assertRaises(HTTPError) as ctx:self.post(b'/api/login',data)
            self.assertEqual(ctx.exception.status,401)
        self.assertIsNone(self.robot.session)
        self.assertEqual(len(self.token),48)
        self.assertEqual(len(self.server.logins),1)

    async def test_logout_stops_owner_and_revokes_token(self):
        session=json.loads(self.post(b'/api/arm',{})[2])['session']
        self.post(b'/api/control',{'session':session,'sequence':1,'throttle':.5,'steering':0,'max_rpm':80})
        self.robot.update(.05)
        self.assertTrue(any(w.motor.output for w in self.robot.wheels))
        self.post(b'/api/logout',{})
        self.assertIsNone(self.robot.session)
        self.assertTrue(all(w.motor.output==0 for w in self.robot.wheels))
        with self.assertRaises(HTTPError) as ctx:self.post(b'/api/arm',{})
        self.assertEqual(ctx.exception.status,401)

    async def test_other_login_cannot_command_or_stop_owner(self):
        session=json.loads(self.post(b'/api/arm',{})[2])['session']
        other=json.loads(self.post(b'/api/login',{'username':'admin','password':'test-password'})[2])['token']
        original=self.headers[b'authorization']
        self.headers[b'authorization']=('Bearer '+other).encode()
        for path,data in ((b'/api/control',{'session':session,'sequence':1,'throttle':1,'steering':0,'max_rpm':80}),(b'/api/stop',{'session':session})):
            with self.assertRaises(HTTPError) as ctx:self.post(path,data)
            self.assertEqual(ctx.exception.status,403)
        self.post(b'/api/logout',{})
        self.assertEqual(self.robot.session,session)
        self.headers[b'authorization']=original
        self.post(b'/api/stop',{'session':session})
        self.assertIsNone(self.robot.session)

    async def test_login_remains_valid_after_long_inactivity(self):
        self.now+=365*24*60*60*1000
        status=json.loads(self.server.route(b'GET',b'/api/status',self.headers,b'')[2])
        self.assertFalse(status['armed'])
        self.assertIn(self.token,self.server.logins)
        self.post(b'/api/arm',{})
        self.assertIsNotNone(self.robot.session)

    async def test_server_restart_requires_login_again(self):
        restarted=WebServer(self.robot,self.cfg,b'<html>dashboard</html>')
        with self.assertRaises(HTTPError) as ctx:
            restarted.route(b'GET',b'/api/status',self.headers,b'')
        self.assertEqual(ctx.exception.status,401)

    async def test_status_does_not_extend_motor_lease(self):
        self.post(b'/api/arm',{})
        self.now+=config.COMMAND_TIMEOUT_MS+1
        self.server.route(b'GET',b'/api/status',self.headers,b'')
        self.assertIsNone(self.robot.session)
        self.assertIn(self.token,self.server.logins)

    async def test_login_limit_replaces_idle_session_without_stopping_driver(self):
        session=json.loads(self.post(b'/api/arm',{})[2])['session']
        first_other=None
        for _ in range(self.server.MAX_LOGINS+2):
            token=json.loads(self.post(b'/api/login',{'username':'admin','password':'test-password'})[2])['token']
            if first_other is None:first_other=token
        self.assertEqual(len(self.server.logins),self.server.MAX_LOGINS)
        self.assertIn(self.token,self.server.logins)
        self.assertNotIn(first_other,self.server.logins)
        self.assertEqual(self.robot.session,session)
        status=json.loads(self.server.route(b'GET',b'/api/status',self.headers,b'')[2])
        self.assertTrue(status['armed'])

    async def test_fragmented_http_response_and_cleanup(self):
        writer=Writer()
        await self.server.handle(Reader(b'GET / HTTP/1.1\r\nHost: esp32\r\n\r\n'),writer)
        self.assertIn(b'200 OK',writer.data);self.assertTrue(writer.data.endswith(b'<html>dashboard</html>'))
        self.assertTrue(writer.closed);self.assertEqual(self.server.active_clients,0)
    async def test_overload_closes_micropython_streams_and_server_recovers(self):
        class MicroPythonWriter(Writer):
            # MicroPython Stream.close() is a no-op; wait_closed closes its socket.
            def close(self):pass
            async def wait_closed(self):self.closed=True
        self.server.active_clients=4
        rejected=[]
        for _ in range(20):
            writer=MicroPythonWriter();rejected.append(writer)
            await self.server.handle(Reader(b''),writer)
        self.assertTrue(all(w.closed for w in rejected))
        self.assertEqual(self.server.active_clients,4)
        self.server.active_clients=0
        writer=MicroPythonWriter()
        await self.server.handle(Reader(b'GET /api/ping HTTP/1.1\r\n\r\n'),writer)
        self.assertIn(b'200 OK',writer.data)
        self.assertTrue(writer.closed)
        self.assertEqual(self.server.active_clients,0)

    async def test_aborted_responses_release_slots_and_sockets(self):
        class AbortedWriter(Writer):
            def close(self):pass
            async def drain(self):raise OSError('client disconnected')
            async def wait_closed(self):self.closed=True
        for _ in range(20):
            writer=AbortedWriter()
            await self.server.handle(Reader(b'GET /api/ping HTTP/1.1\r\n\r\n'),writer)
            self.assertTrue(writer.closed)
            self.assertEqual(self.server.active_clients,0)
        self.assertIsNone(self.robot.session)
    async def test_limits_duplicate_headers_and_json_errors(self):
        for request,status in [(b'GET / HTTP/1.1\r\nContent-Length: 900\r\n\r\n',413),
                               (b'GET / HTTP/1.1\r\nX: a\r\nX: b\r\n\r\n',400),
                               (b'GET / HTTP/1.1\r\nX: '+b'a'*4100,431)]:
            writer=Writer();await self.server.handle(Reader(request),writer)
            self.assertIn(('HTTP/1.1 '+str(status)).encode(),writer.data)
        with self.assertRaises(HTTPError):self.post(b'/api/control',[])
    async def test_slow_reader_does_not_block_other_coroutines(self):
        class SlowReader:
            async def read(self,n):await asyncio.sleep(10)
        task=asyncio.create_task(self.server.read_request(SlowReader()))
        ticks=0
        for _ in range(5):
            await asyncio.sleep(.001);ticks+=1
        task.cancel()
        try:await task
        except asyncio.CancelledError:pass
        self.assertEqual(ticks,5)


if __name__=='__main__':unittest.main()
