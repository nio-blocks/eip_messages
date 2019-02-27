eip_messages
===

Blocks in this Collection
---
[EIPGetAttribute](docs/eip_get_attribute_block.md)
[EIPSetAttribute](docs/eip_set_attribute_block.md)

Dependencies
---
[pycomm3](https://github.com/bpaterni/pycomm/tree/pycomm3)

When installing `requirements.txt`, pip will attempt to install the pycomm3 fork and if a conflict is found it will prompt for resolution. If the wrong fork is installed, the block will fail to configure raising `pycomm.cip.cip_base.CommError: must be str, not bytes`.