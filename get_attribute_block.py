from pycomm.cip.cip_generic import Driver
from nio import Block
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
        self.conn = Driver()

    def configure(self, context):
        super().configure(context)
        self.conn.open(self.host())

    def process_signals(self, signals):
        path = [self.class_id(), self.instance_num()]
        if self.attribute_num() != None:
            path.append(int(self.attribute_num()))
        for signal in signals:
            self.conn.get_attribute_single(*path)
        self.notify_signals(signals)

    def stop(self):
        super().stop()
        self.conn.close()
