from .cip_driver import CIPDriver
from nio import Block
from nio.block.mixins import EnrichSignals, Retry
from nio.properties import Property, IntProperty, StringProperty, \
                           VersionProperty


class EIPGetAttribute(EnrichSignals, Retry, Block):

    version = VersionProperty('0.2.0')
    host = StringProperty(title='Hostname', default='localhost')
    class_id = IntProperty(title='Class ID', default=1)
    instance_num = IntProperty(title='Instance', default=1)
    attribute_num = Property(title='Attribute', default=None, allow_none=True)

    def __init__(self):
        super().__init__()
        self.cnxn = None

    def before_retry(self, *args, **kwargs):
        self._disconnect()
        self._connect()

    def configure(self, context):
        super().configure(context)
        try:
            self._connect()
        except Exception:
            self.cnxn = None
            msg = 'Unable to connect to {}'.format(self.host())
            self.logger.exception(msg)

    def process_signals(self, signals):
        host = self.host()
        outgoing_signals = []
        if self.cnxn is None:
            try:
                msg = 'Connecting to {}'.format(host)
                self.logger.warning(msg)
                self._connect()
            except Exception as exc:
                self.cnxn = None
                msg = 'Unable to connect to {}'.format(host)
                self.logger.error(msg)
                raise exc
        for signal in signals:
            path = [self.class_id(signal), self.instance_num(signal)]
            if self.attribute_num(signal) is not None:
                path.append(int(self.attribute_num(signal)))
            try:
                value = self.execute_with_retry(self._make_request, path)
            except Exception as exc:
                value = False
                self.cnxn = None
                msg = 'get_attribute_single failed, host: {}, path: {}'
                self.logger.error(msg.format(host, path))
                raise exc
            if value:
                new_signal_dict = {}
                new_signal_dict['host'] = host
                new_signal_dict['path'] = path
                new_signal_dict['value'] = value
                new_signal = self.get_output_signal(new_signal_dict, signal)
                outgoing_signals.append(new_signal)
            else:
                if self.cnxn is None:
                    msg = 'Connection to {} failed.'.format(host)
                else:
                    status = self.cnxn.get_status()
                    msg = 'get_attribute_single failed, {}, host: {}, path: {}'
                    msg = msg.format(status, host, path)
                self.logger.error(msg)
        self.notify_signals(outgoing_signals)

    def stop(self):
        self._disconnect()
        super().stop()

    def _connect(self):
        # each instance of CIPDriver can open connection to only 1 host
        # subsequent calls to open() are quietly ignored, and close()
        # does not take any args, so one host per block instance for now
        self.cnxn = CIPDriver()
        self.cnxn.open(self.host())

    def _disconnect(self):
        if self.cnxn is not None:
            self.cnxn.close()
            self.cnxn = None

    def _make_request(self, path):
        return self.cnxn.get_attribute_single(*path)
