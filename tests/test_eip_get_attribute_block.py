from unittest.mock import patch
from nio import Signal
from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from ..eip_get_attribute_block import EIPGetAttribute


class TestEIPGetAttribute(NIOBlockTestCase):

    @patch(EIPGetAttribute.__module__ + '.CIPDriver')
    def test_block_expressions(self, mock_driver):
        """Get an attribute from the specified path and host"""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.return_value = 5309
        config = {
            'host': 'dummyhost',
            'class_id': '{{ $class_id }}',
            'instance_num': '{{ $instance_num }}',
            'attribute_num': '{{ $attribute_num }}'}
        blk = EIPGetAttribute()
        self.configure_block(blk, config)
        blk.start()
        drvr.open.assert_called_once_with('dummyhost')
        incoming_signal = Signal({
            'class_id': 8, 'instance_num': 6, 'attribute_num': 7})
        blk.process_signals([incoming_signal])
        drvr.get_attribute_single.assert_called_once_with(8, 6, 7)
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(Signal(
            {'host': 'dummyhost', 'path': [8, 6, 7], 'value': 5309}))

    @patch(EIPGetAttribute.__module__ + '.CIPDriver')
    def test_signal_lists(self, mock_driver):
        """Outgoing signal lists have the same length as incoming"""
        config = {}
        blk = EIPGetAttribute()
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals([Signal()] * 3)
        blk.stop()
        self.assertEqual(len(self.notified_signals[DEFAULT_TERMINAL]), 1)
        self.assertEqual(len(self.notified_signals[DEFAULT_TERMINAL][0]), 3)

    @patch(EIPGetAttribute.__module__ + '.CIPDriver')
    def test_signal_enrichment(self, mock_driver):
        """Incoming signals are enriched new data"""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.return_value = 42
        config = {'enrich': {'exclude_existing': False}}
        blk = EIPGetAttribute()
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals([Signal({'foo': 'bar'})])
        blk.stop()
        self.assert_last_signal_notified(Signal(
            {'foo': 'bar', 'host': 'localhost', 'path': [1, 1], 'value': 42}))

    @patch(EIPGetAttribute.__module__ + '.CIPDriver')
    def test_failure_to_get(self, mock_driver):
        """One of two requests fail but the connection is alive."""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.side_effect = [False, 255]
        drvr.get_status.return_value = (1, 'bad things')
        config = {}
        blk = EIPGetAttribute()
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals([Signal()] * 2)
        blk.stop()
        self.assertEqual(drvr.get_attribute_single.call_count, 2)
        self.assertEqual(drvr.get_status.call_count, 1)
        self.assert_num_signals_notified(1)

    @patch(EIPGetAttribute.__module__ + '.CIPDriver')
    def test_reconnect(self, mock_driver):
        """Reconnect before retrying when the connection has died."""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.side_effect = [Exception, 255]
        drvr.get_status.side_effect = Exception
        blk = EIPGetAttribute()
        config = {
            'retry_options': {
                'multiplier': 0, # don't wait while testing
            },
        }
        self.configure_block(blk, config)
        self.assertEqual(drvr.open.call_count, 1)
        blk.start()
        blk.process_signals([Signal()])
        self.assertEqual(drvr.get_attribute_single.call_count, 2)
        self.assertEqual(drvr.close.call_count, 1)
        self.assertEqual(drvr.open.call_count, 2)
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertEqual(drvr.close.call_count, 2)
