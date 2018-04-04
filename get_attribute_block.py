from pycomm.cip.cip_generic import Driver
from nio import Block, Signal
from nio.properties import Property, IntProperty, StringProperty, \
                           VersionProperty


class GetAttribute(Block):

    version = VersionProperty('0.1.0')
    host = StringProperty(title='Hostname', default='localhost')
    class_id = IntProperty(title='Class ID', default=1)
    instance_num = IntProperty(title='Instance', default=1)
    attribute_num = Property(title='Attribute', default=None, allow_none=True)

    def __init__(self):
        super().__init__()
        self.cnxn = Driver()

    def configure(self, context):
        super().configure(context)
        self.cnxn.open(self.host())

    def process_signals(self, signals):
        outgoing_signals = []
        for signal in signals:
            path = [self.class_id(signal), self.instance_num(signal)]
            if self.attribute_num(signal) != None:
                path.append(int(self.attribute_num(signal)))
            new_signal = Signal()
            new_signal.host = self.host()
            new_signal.path = path
            new_signal.value = self.cnxn.get_attribute_single(*path)
            outgoing_signals.append(new_signal)
        self.notify_signals(outgoing_signals)

    def stop(self):
        super().stop()
        self.cnxn.close()
