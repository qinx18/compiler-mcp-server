---
name: Vectorization Expert
trigger_type: keyword
keywords:
  - vectorization
  - SIMD
  - loop optimization
  - dependency analysis
---

# Vectorization Analysis Expertise

When working on vectorization-related features:

## Key Files

- `analyze_loop_carried_dependencies()` - Core dependency detection logic
- `_check_iteration_overlap()` - Determines if array accesses conflict
- `_generate_suggestions()` - Creates optimization recommendations

## Common Vectorization Blockers

1. **Loop-carried dependencies**: When iteration i+1 depends on results from iteration i
2. **Pointer aliasing**: When compiler can't prove arrays don't overlap
3. **Non-contiguous memory access**: Strided or random access patterns
4. **Complex control flow**: Conditional statements within loops

## Testing Patterns

- Basic dependency: `a[i] = a[i-1] + b[i]`
- S1113 pattern: `a[i] = a[N/2-i] + b[i]`
- Aliasing: Two pointers that might point to same memory
- Reduction: `sum += a[i]`

## Improvement Opportunities

- Enhance symbolic analysis for complex index expressions
- Add support for more transformation types (loop fusion, tiling)
- Implement cost models for vectorization decisions
