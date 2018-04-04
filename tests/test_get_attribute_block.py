from unittest.mock import patch
from nio import Signal
from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from ..get_attribute_block import GetAttribute


class TestGetAttribute(NIOBlockTestCase):

    @patch(GetAttribute.__module__ + '.Driver')
    def test_defaults(self, mock_driver):
        """Default block behavior"""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.return_value = 42
        blk = GetAttribute()
        self.configure_block(blk, {})
        blk.start()
        drvr.open.assert_called_once_with('localhost')
        blk.process_signals([Signal()])
        drvr.get_attribute_single.assert_called_once_with(1, 1)
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(
            Signal({'host': 'localhost', 'path': [1, 1], 'value': 42}))

    @patch(GetAttribute.__module__ + '.Driver')
    def test_configured_block(self, mock_driver):
        """Get an attribute from the specified path and host"""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.return_value = 5309
        config = {
            'host': 'dummyhost',
            'class_id': 8,
            'instance_num': 6,
            'attribute_num': 7}
        blk = GetAttribute()
        self.configure_block(blk, config)
        blk.start()
        drvr.open.assert_called_once_with(config['host'])
        blk.process_signals([Signal()])
        drvr.get_attribute_single.assert_called_once_with(
            config['class_id'],
            config['instance_num'],
            config['attribute_num'])
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(
            Signal({'host': 'dummyhost', 'path': [8, 6, 7], 'value': 5309}))

    @patch(GetAttribute.__module__ + '.Driver')
    def test_block_expressions(self, mock_driver):
        """Get an attribute from the specified path and host"""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.return_value = 5309
        config = {
            'class_id': '{{ $class_id }}',
            'instance_num': '{{ $instance_num }}',
            'attribute_num': '{{ $attribute_num }}'}
        blk = GetAttribute()
        self.configure_block(blk, config)
        blk.start()
        incoming_signal = Signal({
            'class_id': 8, 'instance_num': 6, 'attribute_num': 7})
        blk.process_signals([incoming_signal])
        blk.stop()
        drvr.close.assert_called_once_with()
        self.assert_last_signal_notified(
            Signal({'host': 'localhost', 'path': [8, 6, 7], 'value': 5309}))

    @patch(GetAttribute.__module__ + '.Driver')
    def test_signal_lists(self, mock_driver):
        """Outgoing signal lists have the same length as incoming"""
        blk = GetAttribute()
        self.configure_block(blk, {})
        blk.start()
        blk.process_signals([Signal()] * 3)
        blk.stop()
        self.assertEqual(len(self.notified_signals[DEFAULT_TERMINAL]), 1)
        for signal_list in self.notified_signals[DEFAULT_TERMINAL]:
            self.assertEqual(len(signal_list), 3)

    @patch(GetAttribute.__module__ + '.Driver')
    def test_signal_enrichment(self, mock_driver):
        """Incoming signals are enriched new data"""
        drvr = mock_driver.return_value
        drvr.get_attribute_single.return_value = 42
        blk = GetAttribute()
        self.configure_block(blk, {'enrich': {'exclude_existing': False}})
        blk.start()
        blk.process_signals([Signal({'foo': 'bar'})])
        blk.stop()
        self.assert_last_signal_notified(Signal(
            {'foo': 'bar', 'host': 'localhost', 'path': [1, 1], 'value': 42}))
