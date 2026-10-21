# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered by `make demo` (VHS: https://github.com/charmbracelet/vhs), which
# runs it under `poetry run` so the commands resolve to this checkout. It
# shows the helpers the server runs on every edit and the quick fix it
# offers, run against the sample records in examples/.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 640
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type "python examples/01_lsp_helpers.py"
Enter
Wait@60s /\$$/
Sleep 3s

Type "python examples/02_quick_fix.py"
Enter
Wait@60s /\$$/
Sleep 4s
