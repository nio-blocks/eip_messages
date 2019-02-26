EIPGetAttribute
============
Send a class 3 (unconnected) explicit message to an EtherNet/IP scanner device or controller requesting the value of a specified CIP Object class, instance, and attribute. Each instance of the block can handle connections to one target device only.

Properties
----------
- **Hostname**: The IP address or hostname of the target device.
- **Class ID**: The CIP class ID to get.
- **Instance**: The instance number of the CIP class.
- **Attribute**: (optional) The attribute number to get.

Example
-------
For every request processed, the output signal will contain the following attributes, plus any **Signal Enrichement** options. If the request was not successful the signal will be dropped.
  - *host* (string) The hostname of the target device.
  - *path* (array) The requested path, such as [`class_id`, `instance_num`, `attribute_num`].
  - *value* (bytes) The raw bytes sent in the request.

Commands
--------
None
