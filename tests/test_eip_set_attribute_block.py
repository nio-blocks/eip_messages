from unittest.mock import patch, Mock
from nio import Signal
from nio.block.terminals import DEFAULT_TERMINAL
from nio.testing.block_test_case import NIOBlockTestCase
from ..eip_set_attribute_block import EIPSetAttribute


class CustomException(Exception):

    pass


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
        """One of two requests fail but the connection is alive."""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.side_effect = [False, 255]
        drvr.get_status.return_value = (1, 'bad things')
        config = {}
        blk = EIPSetAttribute()
        self.configure_block(blk, config)
        blk.start()
        blk.process_signals([Signal()] * 2)
        blk.stop()
        self.assertEqual(drvr.set_attribute_single.call_count, 2)
        self.assertEqual(drvr.get_status.call_count, 1)
        self.assert_num_signals_notified(1)

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_reconnect(self, mock_driver):
        """Reconnect before retrying when the connection has died."""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.side_effect = [Exception, 255]
        drvr.get_status.side_effect = Exception
        blk = EIPSetAttribute()
        config = {
            'retry_options': {
                'multiplier': 0, # don't wait while testing
            },
        }
        self.configure_block(blk, config)
        self.assertEqual(drvr.open.call_count, 1)
        blk.start()
        blk.process_signals([Signal()])
        self.assertEqual(drvr.set_attribute_single.call_count, 2)
        self.assertEqual(drvr.close.call_count, 1)
        self.assertEqual(drvr.open.call_count, 2)
        blk.stop()
        self.assert_num_signals_notified(1)
        self.assertEqual(drvr.close.call_count, 2)

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_connection_fails(self, mock_driver):
        """The block can start even if the initial connection fails."""
        drvr = mock_driver.return_value
        drvr.open.side_effect = CustomException
        blk = EIPSetAttribute()
        config = {}
        self.configure_block(blk, config)
        self.assertEqual(drvr.open.call_count, 1)
        self.assertEqual(drvr.open.call_args[0], ('localhost', ))
        self.assertIsNone(blk.cnxn)
        # start processing signals and try (and fail) to reopen connection
        blk.start()
        with self.assertRaises(CustomException):
            blk.process_signals([Signal()])
        self.assertEqual(drvr.open.call_count, 2)
        # still no connection
        drvr.set_attribute_single.assert_not_called()
        self.assertIsNone(blk.cnxn)
        blk.stop()
        # no connection so nothing to close
        drvr.close.assert_not_called()
        self.assert_num_signals_notified(0)

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_reconnection(self, mock_driver):
        """Processing signals reopens the connection."""
        drvr = mock_driver.return_value
        drvr.open.side_effect = [CustomException, Mock()]
        blk = EIPSetAttribute()
        config = {}
        self.configure_block(blk, config)
        self.assertEqual(drvr.open.call_count, 1)
        self.assertEqual(drvr.open.call_args[0], ('localhost', ))
        self.assertIsNone(blk.cnxn)
        # start processing signals and reopen connection
        blk.start()
        blk.process_signals([Signal()])
        self.assertEqual(drvr.open.call_count, 2)
        self.assertEqual(blk.cnxn, drvr)
        self.assertEqual(drvr.set_attribute_single.call_count, 1)
        blk.stop()
        self.assertEqual(drvr.close.call_count, 1)
        self.assertIsNone(blk.cnxn)
        self.assert_num_signals_notified(1)

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_reconnection_fails(self, mock_driver):
        """When out of retries, reset the connection."""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.side_effect = CustomException
        blk = EIPSetAttribute()
        config = {
            'retry_options': {
                'max_retry': 0,  # do not retry
            },
        }
        self.configure_block(blk, config)
        blk.start()
        self.assertEqual(blk.cnxn, drvr)
        with self.assertRaises(CustomException):
            blk.process_signals([Signal()])
        self.assertIsNone(blk.cnxn)
        self.assertEqual(drvr.get_status.call_count, 0)
        blk.stop()

    @patch(EIPSetAttribute.__module__ + '.CIPDriver')
    def test_retry_connection_before_retry_request(self, mock_driver):
        """When a request fails, the connection is retried first."""
        drvr = mock_driver.return_value
        drvr.set_attribute_single.side_effect = [
            CustomException, CustomException, 42]
        blk = EIPSetAttribute()
        config = {
            'retry_options': {
                'max_retry': 2,  # make three total attempts
                'multiplier': 0, # don't wait while testing
            },
        }
        self.configure_block(blk, config)
        self.assertEqual(drvr.open.call_count, 1)
        self.assertEqual(blk.cnxn, drvr)
        blk.start()
        blk.process_signals([Signal()])
        self.assertEqual(drvr.set_attribute_single.call_count, 3)
        # Before each retry to set_attribute_single() the connection is 
        # retried and set_attribute_single works on the third attempt
        self.assertEqual(drvr.close.call_count, 2)
        self.assertEqual(drvr.open.call_count, 3)
        blk.stop()
        self.assertEqual(drvr.close.call_count, 3)
        self.assert_last_signal_notified(Signal(
            {'host': 'localhost', 'path': [1, 1], 'value': b'\x00\x00'}))

