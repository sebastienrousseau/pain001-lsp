# pain001-lsp examples

Runnable, self-contained examples for the **pain001-lsp** language server.
Run any of them from the repository root:

```sh
python examples/<name>.py
```

| Example | Demonstrates |
|---------|--------------|
| [`01_lsp_helpers.py`](01_lsp_helpers.py) | The LSP diagnostics / completion / hover helpers (`compute_diagnostics`, `completion_items`, `hover_text`) |
| [`02_quick_fix.py`](02_quick_fix.py) | The "Add missing required fields" code action — `missing_required_fields` + `build_insert_text` |
| [`03_configure_message_type.py`](03_configure_message_type.py) | Overriding the default message type via `initializationOptions` (`{"messageType": "pain.001.001.11"}`) |

These helpers are exactly what the `pain001-lsp` server runs on each edit,
so you can call them directly to see the diagnostics, completion items,
hover text, and code actions an editor would receive.

Both `pain001-lsp` and its core dependency `pain001` must be installed
(Python 3.10+):

```sh
pip install pain001-lsp
```
