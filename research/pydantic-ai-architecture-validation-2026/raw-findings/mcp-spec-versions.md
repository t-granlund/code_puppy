# MCP Specification Versions (as of March 2026)

Source: https://github.com/modelcontextprotocol/modelcontextprotocol/tree/main/docs/specification

## Available Versions
1. **2024-11-05** — Original spec
2. **2025-03-26** — Added pagination, listChanged, tool annotations
3. **2025-06-18** — (not investigated in detail)
4. **2025-11-25** — Latest stable. Added: title, icons, outputSchema, structuredContent, resource_link
5. **draft** — Next revision. Minor changes only: extensions field, OpenTelemetry tracing

## Tools Spec Features (2025-11-25)

### Supported
- `tools/list` with cursor-based pagination
- `tools/call` for invocation
- `notifications/tools/list_changed` for dynamic updates
- Tool annotations (untrusted unless from trusted servers)
- `outputSchema` for structured tool results
- `structuredContent` return format
- `resource_link` return type
- Tool `title`, `description`, `icons` fields
- Tool name regex: `^[a-zA-Z0-9_.-]{1,128}$`

### NOT Supported (Relevant to Progressive Discovery)
- No `tools/search` endpoint
- No `tools/getSchema` endpoint
- No category/tag filtering on `tools/list`
- No lazy schema loading (schemas always included in list response)
- No tool priority/ordering hints
- No tool dependency declarations

## Draft Changelog (Exact Text)
```
Major changes: N/A

Minor changes:
- Add extensions field to ClientCapabilities and ServerCapabilities
  to support optional extensions beyond the core protocol.
- Document OpenTelemetry trace context propagation conventions for
  _meta keys (traceparent, tracestate, baggage) (SEP-414).

Other schema changes: N/A
```
