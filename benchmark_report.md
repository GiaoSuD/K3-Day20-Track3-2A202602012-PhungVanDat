# Benchmark Report: Single-Agent vs Multi-Agent

## Query
What is GraphRAG?

## Results Summary

| Metric | Single-Agent Baseline | Multi-Agent |
|--------|----------------------|--------------|
| Total Time | 8.67s | 29.49s |
| Tokens In | 31 | N/A (see trace) |
| Tokens Out | 646 | N/A (see trace) |
| Est. Cost | $0.0004 | N/A |
| Iterations | 1 | 3 |
| Route | direct | researcher → analyst → writer |

## Analysis

### Single-Agent Approach
- **Pros**: Simpler, faster for simple queries, lower overhead
- **Cons**: One agent handles everything, harder to debug, less specialized

### Multi-Agent Approach
- **Pros**: Specialized roles, better separation of concerns, easier to debug
- **Cons**: More overhead, more complex, higher latency

## Conclusion
Single-agent is faster for this query.
Multi-agent is cheaper.

---
*Report generated automatically*
