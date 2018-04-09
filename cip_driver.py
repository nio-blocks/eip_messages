from pycomm.cip.cip_base import *


class CIPDriver(Base):

    def __init__(self):
        super(CIPDriver, self).__init__()

        self._buffer = {}
        self._get_template_in_progress = False
        self.__version__ = '0.2'

    def get_attribute_single(self, clss, inst, attr=None):
        self.clear()
        path = [0x20, clss, 0x24, inst]
        if attr != None:
            path.extend([0x30, attr])
        message_request = [
            bytes([0x0E]),  # get attribute single service
            bytes([len(path)]),  # the Request Path Size length in word
            bytes(path),  # the request path
        ]
        packet = build_common_packet_format(
            DATA_ITEM['Unconnected'],
            b''.join(message_request),
            ADDRESS_ITEM['UCMM'],)
        if not self.send_rr_data(packet):
            self._status = (6, "send_rr_data failed")
            logger.warning(self._status)
            raise DataError("send_rr_data failed")
        if self._status[0] == SUCCESS:
            # Unconnected Data Item Length
            data_length = unpack_uint(self._reply[38:40])
            # first 4 bytes indicate service and status
            reply_length = data_length - 4
            return self._reply[-reply_length:]
        else:
            return False

    def set_attribute_single(self, data, clss, inst, attr=None):
        self.clear()
        path = [0x20, clss, 0x24, inst]
        if attr != None:
            path.extend([0x30, attr])
        message_request = [
            bytes([0x10]),  # set attribute single service
            bytes([len(path)]),  # the Request Path Size length in word
            bytes(path),  # the request path
            bytes(data),  # data to write, two bytes per word
        ]
        packet = build_common_packet_format(
            DATA_ITEM['Unconnected'],
            b''.join(message_request),
            ADDRESS_ITEM['UCMM'],)
        if not self.send_rr_data(packet):
            self._status = (6, "send_rr_data failed")
            logger.warning(self._status)
            raise DataError("send_rr_data failed")
        if self._status[0] == SUCCESS:
            return True
        else:
            return False

    def _check_reply(self):
        """ check the reply message for error

        """
        self._more_packets_available = False
        try:
            if self._reply is None:
                self._status = (3, '{} without reply'.format(
                    REPLAY_INFO[unpack_dint(self._message[:2])]))
                return False
            # Get the type of command
            typ = unpack_uint(self._reply[:2])

            # Encapsulation status check
            if unpack_dint(self._reply[8:12]) != SUCCESS:
                self._status = (3, "{0} reply status:{1}".format(
                    REPLAY_INFO[typ],
                    SERVICE_STATUS[unpack_dint(self._reply[8:12])]))
                return False

            # Command Specific Status check
            if typ == unpack_uint(ENCAPSULATION_COMMAND["send_rr_data"]):
                status = unpack_usint(self._reply[42:43])
                if status != SUCCESS:
                    status_msg = "send_rr_data reply:{0} - Extend status:{1}"
                    self._status = (3, status_msg.format(
                        SERVICE_STATUS[status],
                        get_extended_status(self._reply, 42)))
                    return False
                else:
                    return True
            return True
        except Exception as e:
            raise DataError(e)