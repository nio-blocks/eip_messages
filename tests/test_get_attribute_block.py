from unittest.mock import patch
from nio import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..get_attribute_block import GetAttribute


class TestGetAttribute(NIOBlockTestCase):

    @patch(GetAttribute.__module__ + '.Driver')
    def test_defaults(self, mock_driver):
        """Signals pass through block unmodified."""
        drvr = mock_driver.return_value
        blk = GetAttribute()
        self.configure_block(blk, {})
        blk.start()
        drvr.open.assert_called_once_with('localhost')
        blk.process_signals([Signal()])
        drvr.get_attribute_single.assert_called_once_with(1, 1)
        blk.stop()
        drvr.close.assert_called_once_with()

    @patch(GetAttribute.__module__ + '.Driver')
    def test_configured_block(self, mock_driver):
        """Signals pass through block unmodified."""
        drvr = mock_driver.return_value
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
