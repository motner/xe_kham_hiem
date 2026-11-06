"""Mapping GPIO va vi tri banh theo anh va xac nhan cua nguoi dung."""
import copy
import importlib
import pathlib
import sys
import types
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'firmware'))
import config


class WiringTests(unittest.TestCase):
    def setUp(self):
        self.wheels = copy.deepcopy(config.WHEELS)
        for wheel, channel, encoder in zip(self.wheels, ('upper_a','lower_a','lower_b','upper_b'), (39,34,35,36)):
            wheel.update(motor_channel=channel,encoder_a=encoder,counts_per_rev=100,diameter_mm=65,pid=(.01,.02,0))

    def validate(self):
        with patch.multiple(config,HARDWARE_ENABLED=True,LOGIN_USERNAME='admin',LOGIN_PASSWORD='test-password',WHEELS=self.wheels):
            config.validate_hardware()

    def test_schematic_channels(self):
        self.assertEqual(config.MOTOR_CHANNELS, {
            'upper_a': {'in1':27,'in2':26,'pwm':14},
            'upper_b': {'in1':25,'in2':33,'pwm':32},
            'lower_a': {'in1':17,'in2':16,'pwm':22},
            'lower_b': {'in1':4,'in2':21,'pwm':19}})
        self.assertEqual(config.ENCODER_PINS,(39,34,35,36))
        self.assertEqual((config.SERVO_PIN,config.ULTRASONIC_TRIGGER_PIN,config.ULTRASONIC_ECHO_PIN),(23,13,18))
        self.assertEqual([w['name'] for w in config.WHEELS], ['front_left','rear_right','rear_left','front_right'])
        self.assertEqual([w['motor_channel'] for w in config.WHEELS], ['upper_a','lower_a','lower_b','upper_b'])
        self.assertEqual([w['encoder_a'] for w in config.WHEELS], [39,34,35,36])
        self.validate()

    def test_duplicate_motor_and_encoder_rejected(self):
        self.wheels[1]['motor_channel']='upper_a'
        with self.assertRaisesRegex(ValueError,'motor_channel'):self.validate()
        self.wheels[1]['motor_channel']='upper_b';self.wheels[1]['encoder_a']=39
        with self.assertRaisesRegex(ValueError,'GPIO'):self.validate()

    def test_reserved_pins_and_output_only_rules(self):
        for pin in (config.SERVO_PIN,config.ULTRASONIC_TRIGGER_PIN,config.ULTRASONIC_ECHO_PIN,34):
            channels=copy.deepcopy(config.MOTOR_CHANNELS);channels['upper_a']['pwm']=pin
            with patch.object(config,'MOTOR_CHANNELS',channels):
                with self.assertRaises(ValueError):self.validate()

    def test_constructor_uses_channel_lookup(self):
        import main
        calls=[]
        class Motor:
            def __init__(self,*args):calls.append(args)
            def stop(self):pass
            def close(self):pass
        class Encoder:
            def __init__(self,*args):self.args=args
            def close(self):pass
        with patch.multiple(config,SCANNER_ENABLED=False,HARDWARE_ENABLED=True,LOGIN_USERNAME='admin',LOGIN_PASSWORD='test-password',WHEELS=self.wheels),patch.dict(sys.modules,{'motor':types.SimpleNamespace(Motor=Motor),'encoder':types.SimpleNamespace(Encoder=Encoder)}):
            robot=main.build_robot()
            self.assertEqual([args[:3] for args in calls],[(27,26,14),(17,16,22),(4,21,19),(25,33,32)])
            self.assertEqual([w.encoder.args[0] for w in robot.wheels],[39,34,35,36])
            robot.close()

    def test_wifi_power_save_required_for_hardware(self):
        with patch.dict(sys.modules,{'network':types.SimpleNamespace()}):
            wifi=importlib.import_module('wifi')
        class Wlan:
            PM_NONE=0
            def config(self,**kwargs):self.params=kwargs
        wlan=Wlan();wifi.disable_power_save(wlan,config)
        self.assertEqual(wlan.params,{'pm':0})
        with patch.object(config,'HARDWARE_ENABLED',True):
            with self.assertRaisesRegex(RuntimeError,'power save'):
                wifi.disable_power_save(object(),config)


if __name__=='__main__':unittest.main()
