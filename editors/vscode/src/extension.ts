// Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
// Licensed under the Apache License, Version 2.0.
//
// VS Code client that launches the `pain001-lsp` language server (stdio)
// for payment-data JSON files. The server itself lives in Python:
// `pip install pain001-lsp`. The server is the same engine as the CLI
// and CI, so the editor never disagrees with the rest of the toolchain.

import { workspace, ExtensionContext } from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

let client: LanguageClient;

export function activate(_context: ExtensionContext): void {
  const config = workspace.getConfiguration("pain001");
  const command = config.get<string>("serverCommand", "pain001-lsp");
  const messageType = config.get<string>("messageType", "pain.001.001.09");

  const serverOptions: ServerOptions = {
    command,
    transport: TransportKind.stdio,
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "json" }],
    initializationOptions: { messageType },
    synchronize: {
      configurationSection: "pain001",
    },
  };

  client = new LanguageClient(
    "pain001-json",
    "Pain001 JSON Language Server",
    serverOptions,
    clientOptions,
  );
  client.start();
}

export function deactivate(): Thenable<void> | undefined {
  return client ? client.stop() : undefined;
}
