from .cip_driver import CIPDriver
from nio import Block
from nio.block.mixins import EnrichSignals, Retry
from nio.properties import IntProperty, ObjectProperty, Property, \
    PropertyHolder, StringProperty, VersionProperty


class ObjectPath(PropertyHolder):

    class_id = IntProperty(title='Class ID', default=1, order=0)
    instance_num = IntProperty(title='Instance', default=1, order=1)
    attribute_num = Property(
        title='Attribute', default=None, allow_none=True, order=2)


class EIPSetAttribute(EnrichSignals, Retry, Block):

    host = StringProperty(title='Hostname', default='localhost', order=0)
    path = ObjectProperty(ObjectPath, title='CIP Object Path',  order=1)
    value = Property(
        title='Value(s) to Write', default='{{ bytes([0, 0]) }}', order=2)
    version = VersionProperty('0.2.0')

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
            path = [
                self.path().class_id(signal), self.path().instance_num(signal)]
            if self.path().attribute_num(signal) != None:
                path.append(int(self.path().attribute_num(signal)))
            write_value = self.value(signal)
            try:
                value = self.execute_with_retry(
                    self._make_request, write_value, path)
            except Exception as exc:
                value = False
                self.cnxn = None
                msg = 'set_attribute_single failed, host: {}, path: {}'
                self.logger.error(msg.format(host, path))
                raise exc
            if value:
                new_signal_dict = {}
                new_signal_dict['host'] = host
                new_signal_dict['path'] = path
                new_signal_dict['value'] = write_value
                new_signal = self.get_output_signal(new_signal_dict, signal)
                outgoing_signals.append(new_signal)
            else:
                if self.cnxn is None:
                    msg = 'Connection to {} failed.'.format(host)
                else:
                    status = self.cnxn.get_status()
                    msg = (
                        'set_attribute_single failed: {}\n'
                        'host: {}, path: {}, value: {}')
                    msg = msg.format(status, host, path, write_value)
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

    def _make_request(self, value, path):
        return self.cnxn.set_attribute_single(value, *path)

