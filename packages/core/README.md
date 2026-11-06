# liuyao calculation core

Bundled in the `shunshi-liuyao-mcp` distribution. Import `shunshi_liuyao` without starting the MCP server.

See the root README for installation, input conventions and capability limits, and SOURCE.md for calculation provenance.

```python
from datetime import datetime
from shunshi_liuyao import cast
print(cast(method="manual", when=datetime(2026, 8, 20, 20, 20), lines=[1]*6, moving=[1]))
```
