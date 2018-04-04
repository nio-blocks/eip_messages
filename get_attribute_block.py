from pycomm.cip.cip_generic import Driver
from nio import Block
from nio.block.mixins.enrich.enrich_signals import EnrichSignals
from nio.properties import Property, IntProperty, StringProperty, \
                           VersionProperty


class GetAttribute(EnrichSignals, Block):

    version = VersionProperty('0.1.0')
    host = StringProperty(title='Hostname', default='localhost')
    class_id = IntProperty(title='Class ID', default=1)
    instance_num = IntProperty(title='Instance', default=1)
    attribute_num = Property(title='Attribute', default=None, allow_none=True)

    def __init__(self):
        super().__init__()
        self.cnxn = None

    def configure(self, context):
        super().configure(context)
        self.cnxn = Driver()
        self.cnxn.open(self.host())
        # each instance of Driver can open connection to only 1 host
        # subsequent calls to open() are quietly ignored, and close()
        # does not take any args, so one host per block instance for now

    def process_signals(self, signals):
        outgoing_signals = []
        for signal in signals:
            path = [self.class_id(signal), self.instance_num(signal)]
            if self.attribute_num(signal) != None:
                path.append(int(self.attribute_num(signal)))
            new_signal_dict = {}
            new_signal_dict['host'] = self.host()
            new_signal_dict['path'] = path
            new_signal_dict['value'] = self.cnxn.get_attribute_single(*path)
            new_signal = self.get_output_signal(new_signal_dict, signal)
            outgoing_signals.append(new_signal)
        self.notify_signals(outgoing_signals)

    def stop(self):
        super().stop()
        self.cnxn.close()
