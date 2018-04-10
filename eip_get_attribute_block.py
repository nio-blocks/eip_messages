from .cip_driver import CIPDriver
from nio import Block
from nio.block.mixins.enrich.enrich_signals import EnrichSignals
from nio.properties import Property, IntProperty, StringProperty, \
                           VersionProperty


class EIPGetAttribute(EnrichSignals, Block):

    version = VersionProperty("0.1.1")
    host = StringProperty(title='Hostname', default='localhost')
    class_id = IntProperty(title='Class ID', default=1)
    instance_num = IntProperty(title='Instance', default=1)
    attribute_num = Property(title='Attribute', default=None, allow_none=True)

    def __init__(self):
        super().__init__()
        self.cnxn = None

    def configure(self, context):
        super().configure(context)
        self.cnxn = CIPDriver()
        self.cnxn.open(self.host())
        # each instance of CIPDriver can open connection to only 1 host
        # subsequent calls to open() are quietly ignored, and close()
        # does not take any args, so one host per block instance for now

    def process_signals(self, signals):
        outgoing_signals = []
        for signal in signals:
            path = [self.class_id(signal), self.instance_num(signal)]
            if self.attribute_num(signal) != None:
                path.append(int(self.attribute_num(signal)))
            value = self.cnxn.get_attribute_single(*path)
            if value:
                new_signal_dict = {}
                new_signal_dict['host'] = self.host()
                new_signal_dict['path'] = path
                new_signal_dict['value'] = value
                new_signal = self.get_output_signal(new_signal_dict, signal)
                outgoing_signals.append(new_signal)
            else:
                self.logger.error(
                    'get_attribute_single failed: {}\nhost: {}, path: {}'
                    .format(self.cnxn.get_status(), self.host(), path))
        self.notify_signals(outgoing_signals)

    def stop(self):
        self.cnxn.close()
        super().stop()
