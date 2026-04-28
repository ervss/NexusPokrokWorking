import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "path";
import axios from "axios";
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..");
const FORBIDDEN_PATHS = [".env", ".pem", "id_rsa", ".ssh", "node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build", "secrets"];

const server = new Server(
  { name: "nexus-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "read_project_files",
      description: "Číta súbory z koreňa projektu (striktný allowlist).",
      inputSchema: {
        type: "object",
        properties: { relativePath: { type: "string" } },
        required: ["relativePath"],
      },
    },
    {
      name: "call_local_api",
      description: "Volá lokálne API (localhost:8000).",
      inputSchema: {
        type: "object",
        properties: {
          endpoint: { type: "string" },
          method: { type: "string", enum: ["GET", "POST"] },
          data: { type: "object" }
        },
        required: ["endpoint"],
      },
    }
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "read_project_files") {
    const targetPath = path.resolve(PROJECT_ROOT, args.relativePath);
    
    // Security checks
    if (!targetPath.startsWith(PROJECT_ROOT)) {
        return { content: [{ type: "text", text: "Access denied: Outside project root" }], isError: true };
    }
    const relativeToRoot = path.relative(PROJECT_ROOT, targetPath);
    if (FORBIDDEN_PATHS.some(p => relativeToRoot.split(path.sep).includes(p) || targetPath.endsWith(p))) {
        return { content: [{ type: "text", text: "Access denied: Forbidden path or file" }], isError: true };
    }

    try {
      const content = await fs.readFile(targetPath, "utf-8");
      return { content: [{ type: "text", text: content }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
    }
  }

  if (name === "call_local_api") {
    const url = `http://localhost:8000${args.endpoint.startsWith('/') ? '' : '/'}${args.endpoint}`;
    try {
      const response = await axios({
        method: args.method || "GET",
        url: url,
        data: args.data,
        timeout: 5000
      });
      return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: `API Error: ${err.message}` }], isError: true };
    }
  }

  throw new Error("Unknown tool");
});

const transport = new StdioServerTransport();
await server.connect(transport);
