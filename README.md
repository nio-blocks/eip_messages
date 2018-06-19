EIPGetAttribute
============
Send a class 3 (unconnected) explicit message to an EtherNet/IP scanner device or controller requesting the value of a specified CIP Object class, instance, and attribute. Each instance of the block can handle connections to one target device only.

Properties
----------
- **host**: The IP address or hostname of the target device.
- **class_id**: The CIP class ID to request.
- **instance_num**: The instance number of the CIP class.
- **attribute_num**: (optional) The attribute number to request.
- **enrich**: Signal Enrichment
  - *exclude_existing*: If checked (true), the attributes of the incoming signal will be excluded from the outgoing signal. If unchecked (false), the attributes of the incoming signal will be included in the outgoing signal.
  - *enrich_field*: (hidden) The attribute on the signal to store the results from this block. If this is empty, the results will be merged onto the incoming signal. This is the default operation. Having this field allows a block to 'save' the results of an operation to a single field on an incoming signal and notify the enriched signal.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: A list of signals of equal length to input signals.
  - *host* (string) the address of the target device.
  - *path* (array) The requested path, such as [`class_id`, `instance_num`, `attribute_num`].
  - *value* (bytes) The raw bytes returned from the request.

Commands
--------
None

Dependencies
------------
[pycomm3](https://github.com/bpaterni/pycomm/tree/pycomm3)  
When installing `requirements.txt`, pip will attempt to install the pycomm3 fork and if a conflict is found it will prompt for resolution. If the wrong fork is installed, the block will fail to configure raising `pycomm.cip.cip_base.CommError: must be str, not bytes`.


***


EIPSetAttribute
============
Send a class 3 (unconnected) explicit message to an EtherNet/IP scanner device or controller setting the value of a specified CIP Object class, instance, and attribute. Each instance of the block can handle connections to one target device only.

Properties
----------
- **host**: The IP address or hostname of the target device.
- **class_id**: The CIP class ID to request.
- **instance_num**: The instance number of the CIP class.
- **attribute_num**: (optional) The attribute number to set.
- **value**: Raw bytes to set as the attribute value.
- **enrich**: Signal Enrichment
  - *exclude_existing*: If checked (true), the attributes of the incoming signal will be excluded from the outgoing signal. If unchecked (false), the attributes of the incoming signal will be included in the outgoing signal.
  - *enrich_field*: (hidden) The attribute on the signal to store the results from this block. If this is empty, the results will be merged onto the incoming signal. This is the default operation. Having this field allows a block to 'save' the results of an operation to a single field on an incoming signal and notify the enriched signal.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: A list of signals of equal length to input signals.
  - *host* (string) the address of the target device.
  - *path* (array) The requested path, such as [`class_id`, `instance_num`, `attribute_num`].
  - *value* (bytes) The raw bytes sent in the request.

Commands
--------
None

Dependencies
------------
[pycomm3](https://github.com/bpaterni/pycomm/tree/pycomm3)  
When installing `requirements.txt`, pip will attempt to install the pycomm3 fork and if a conflict is found it will prompt for resolution. If the wrong fork is installed, the block will fail to configure raising `pycomm.cip.cip_base.CommError: must be str, not bytes`.

