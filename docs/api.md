<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Python API reference

The standalone server's importable Python surface (used by the runnable
examples and any tooling that wires the pure helpers in-process without
going through the LSP transport).

```{eval-rst}
.. automodule:: pain001_lsp
   :members:
   :undoc-members:
```

## Server module

```{eval-rst}
.. automodule:: pain001_lsp.server
   :members:
   :undoc-members:
   :show-inheritance:
```

The helpers below live in their own modules and are imported into
`pain001_lsp.server`, so `from pain001_lsp.server import corpus_list`
(or any of them) keeps working.

## CSV diagnostics

```{eval-rst}
.. automodule:: pain001_lsp._csv
   :members: compute_diagnostics_csv
```

## Formatting and outline

```{eval-rst}
.. automodule:: pain001_lsp._layout
   :members: formatting, document_symbol
```

## Corpus commands

```{eval-rst}
.. automodule:: pain001_lsp._corpus
   :members: corpus_list, corpus_get, corpus_list_command, corpus_get_command
```

## Faces commands

```{eval-rst}
.. automodule:: pain001_lsp._faces
   :members: faces_list, faces_project
```
