---
name: Add Vectorization Test Case
trigger_type: task
description: Guide for adding new vectorization test cases
---

# Steps to Add a New Test Case

1. **Create test file in examples/**
   - Name it descriptively (e.g., `strided_access.c`)
   - Include the problematic pattern
   - Add comments explaining the issue

2. **Update test mode in solution_for_s1113.py**
   - Add new test code string
   - Run analysis on it
   - Verify expected results

3. **Document in README**
   - Add to examples section
   - Explain why it fails vectorization
   - Show the suggested transformation

4. **Enhance analyzer if needed**
   - If pattern isn't detected correctly
   - Update DependencyAnalyzer class
   - Add new CompilationStatus if appropriate

5. **Test thoroughly**
   - Run: `python solution_for_s1113.py --mode test`
   - Verify all existing tests still pass
   - Check new pattern is analyzed correctly
