from unittest.mock import patch
from nio import Signal
from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from ..eip_set_attribute_block import CIPSetAttribute


class TestEIPSetAttribute(NIOBlockTestCase):

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_block_expressions(self, mock_driver):
        """Set an attribute value from the specified path, host, and value"""
        drvr = mock_driver.return_value
        config = {
            'host': 'dummyhost',
            'class_id': '{{ $class_id }}',
            'instance_num': '{{ $instance_num }}',
            'attribute_num': '{{ $attribute_num }}',
            'value': '{{ $value }}'}
        blk = EIPSetAttribute()
        self.configure_block(blk, config)
        blk.start()
        drvr.open.assert_called_once_with('dummyhost')
        incoming_signal = Signal({
            'class_id': 8,
            'instance_num': 6,
            'attribute_num': 7,
            'value': bytes([5, 3, 0, 9])})
        blk.process_signals([incoming_signal])
        drvr.set_attribute_single.assert_called_once_with(
            bytes([5, 3, 0, 9]), 8, 6, 7)
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(Signal({
            'host': 'dummyhost',
            'path': [8, 6, 7],
            'value': bytes([5, 3, 0, 9])}))

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_signal_lists(self, mock_driver):
        """Outgoing signal lists have the same length as incoming"""
        blk = EIPSetAttribute()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()] * 3)
        blk.stop()
        self.assertEqual(len(self.notified_signals[DEFAULT_TERMINAL]), 1)
        for signal_list in self.notified_signals[DEFAULT_TERMINAL]:
            self.assertEqual(len(signal_list), 3)

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_signal_enrichment(self, mock_driver):
        """Incoming signals are enriched new data"""
        drvr = mock_driver.return_value
        blk = EIPSetAttribute()
        self.configure_block(blk, {'enrich': {'exclude_existing': False}})
        blk.start()
        blk.process_signals([Signal({'foo': 'bar'})])
        blk.stop()
        self.assert_last_signal_notified(Signal({
            'foo': 'bar',
            'host': 'localhost',
            'path': [1, 1],
            'value': b'\x00\x00'}))

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_failure_to_set(self, mock_driver):
        """One of two requests fail"""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.side_effect = [False, True]
        drvr.get_status.return_value = (1, 'bad things')
        blk = EIPSetAttribute()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()] * 2)
        self.assertEqual(drvr.set_attribute_single.call_count, 2)
        blk.stop()
        self.assert_num_signals_notified(1)
