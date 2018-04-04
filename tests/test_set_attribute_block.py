from unittest.mock import patch
from nio import Signal
from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from ..set_attribute_block import SetAttribute


class TestSetAttribute(NIOBlockTestCase):

    @patch(SetAttribute.__module__ + '.Driver')
    def test_default_block(self, mock_driver):
        """Set an attribute using the default values"""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.return_value = True
        blk = SetAttribute()
        self.configure_block(blk, {})
        blk.start()
        drvr.open.assert_called_once_with('localhost')
        blk.process_signals([Signal()])
        drvr.set_attribute_single.assert_called_once_with(b'\x00\x00', 1, 1)
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(Signal(
            {'host': 'localhost', 'path': [1, 1], 'value': b'\x00\x00'}))

    @patch(SetAttribute.__module__ + '.Driver')
    def test_failure_to_set(self, mock_driver):
        """One of two requests fail"""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.side_effect = [False, True]
        drvr.get_status.return_value = (1, 'bad things')
        blk = SetAttribute()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()] * 2)
        self.assertEqual(drvr.set_attribute_single.call_count, 2)
        blk.stop()
        self.assert_num_signals_notified(1)

    @patch(SetAttribute.__module__ + '.Driver')
    def test_block_expressions(self, mock_driver):
        """Set an attribute value from the specified path, host, and value"""
        drvr = mock_driver.return_value
        config = {
            'class_id': '{{ $class_id }}',
            'instance_num': '{{ $instance_num }}',
            'attribute_num': '{{ $attribute_num }}',
            'value': '{{ $value }}'}
        blk = SetAttribute()
        self.configure_block(blk, config)
        blk.start()
        incoming_signal = Signal({
            'class_id': 8,
            'instance_num': 6,
            'attribute_num': 7,
            'value': bytes([5, 3, 0, 9])})
        blk.process_signals([incoming_signal])
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(Signal({
            'host': 'localhost',
            'path': [8, 6, 7],
            'value': bytes([5, 3, 0, 9])}))

    @patch(SetAttribute.__module__ + '.Driver')
    def test_signal_lists(self, mock_driver):
        """Outgoing signal lists have the same length as incoming"""
        blk = SetAttribute()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()] * 3)
        blk.stop()
        self.assertEqual(len(self.notified_signals[DEFAULT_TERMINAL]), 1)
        for signal_list in self.notified_signals[DEFAULT_TERMINAL]:
            self.assertEqual(len(signal_list), 3)

    @patch(SetAttribute.__module__ + '.Driver')
    def test_signal_enrichment(self, mock_driver):
        """Incoming signals are enriched new data"""
        drvr = mock_driver.return_value
        blk = SetAttribute()
        self.configure_block(blk, {'enrich': {'exclude_existing': False}})
        blk.start()
        blk.process_signals([Signal({'foo': 'bar'})])
        blk.stop()
        self.assert_last_signal_notified(Signal({
            'foo': 'bar',
            'host': 'localhost',
            'path': [1, 1],
            'value': b'\x00\x00'}))