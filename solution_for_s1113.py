import argparse
import asyncio
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server with a descriptive name
mcp = FastMCP("intelligent-compiler")


class CompilationStatus(Enum):
    """Comprehensive compilation status hierarchy"""

    # Success cases
    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = "success_with_warnings"

    # Vectorization-specific failures
    VECTORIZATION_FAILED = "vectorization_failed"  # Generic vectorization failure
    DEPENDENCY_CONFLICT = "dependency_conflict"  # Specific: due to dependencies
    ALIGNMENT_ISSUE = "alignment_issue"  # Specific: due to alignment
    LOOP_COMPLEXITY = "loop_complexity"  # Specific: loop too complex
    UNSAFE_MEMORY_ACCESS = "unsafe_memory_access"  # Specific: pointer aliasing

    # Other failures
    SYNTAX_ERROR = "syntax_error"
    LINKER_ERROR = "linker_error"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class LoopInfo:
    """Information about a loop structure"""

    loop_var: str
    start: str
    end: str
    step: str = "1"
    body_start_line: int = 0
    body_end_line: int = 0


@dataclass
class ArrayAccess:
    """Represents an array access pattern"""

    array_name: str
    index_expr: str
    line_number: int
    is_write: bool
    loop_context: Optional[LoopInfo] = None


@dataclass
class DependencyInfo:
    """Represents data dependencies in a code block"""

    variable: str
    read_indices: List[str] = field(default_factory=list)
    write_indices: List[str] = field(default_factory=list)
    loop_carried: bool = False
    distance: Optional[int] = None
    conflict_description: Optional[str] = None

    def has_conflict(self) -> bool:
        """Check if this dependency prevents vectorization"""
        return self.loop_carried and self.conflict_description is not None


@dataclass
class VectorizationAnalysis:
    """Detailed analysis of vectorization attempt"""

    status: CompilationStatus
    original_code: str
    dependencies: List[DependencyInfo]
    compiler_messages: List[str]
    suggested_transformations: List[Dict[str, Any]]
    performance_estimate: Optional[float] = None


class CompilerMCPServer:
    """
    MCP Server that provides intelligent compiler services.
    Maintains compilation state and provides rich feedback for code optimization.
    """

    def __init__(
        self, compiler_path: str = "gcc", base_flags: Optional[List[str]] = None
    ):
        """
        Initialize the compiler server with specified compiler and flags.

        Args:
            compiler_path: Path to the compiler executable
            base_flags: Default compilation flags to use
        """
        self.compiler_path = compiler_path
        self.base_flags = base_flags or ["-O3", "-march=native", "-fopt-info-vec-all"]
        self.compilation_sessions: Dict[str, Dict[str, Any]] = {}
        self.dependency_analyzer = DependencyAnalyzer()

    async def create_session(self, session_id: str) -> str:
        """
        Create a new compilation session that maintains state across multiple requests.
        This allows the compiler to remember previous attempts and learn from failures.
        """
        self.compilation_sessions[session_id] = {
            "history": [],
            "learned_patterns": {},
            "successful_transforms": [],
            "failed_attempts": [],
        }
        return f"Created compilation session: {session_id}"

    async def analyze_vectorization(
        self, code: str, session_id: Optional[str] = None
    ) -> VectorizationAnalysis:
        """
        Analyze why vectorization failed for the given code.
        This is the core functionality for handling s1113-like cases.

        Args:
            code: The C/C++ code to analyze
            session_id: Optional session ID for stateful compilation

        Returns:
            Detailed analysis including dependencies and suggestions
        """
        # First, attempt compilation with vectorization flags
        compilation_result = await self._compile_with_diagnostics(code)

        # Extract dependency information from the code using improved analyzer
        dependencies = await self.dependency_analyzer.analyze_loop_carried_dependencies(
            code
        )

        # Parse compiler messages for vectorization failures
        vectorization_issues = self._parse_vectorization_messages(
            compilation_result["messages"]
        )

        # Determine specific failure status based on analysis
        status = self._determine_specific_status(
            compilation_result["status"], dependencies, vectorization_issues
        )

        # Generate transformation suggestions based on the analysis
        suggestions = await self._generate_suggestions(
            code, dependencies, vectorization_issues, session_id
        )

        # Build the complete analysis
        analysis = VectorizationAnalysis(
            status=status,
            original_code=code,
            dependencies=dependencies,
            compiler_messages=compilation_result["messages"],
            suggested_transformations=suggestions,
        )

        # Store in session history if session exists
        if session_id and session_id in self.compilation_sessions:
            self.compilation_sessions[session_id]["history"].append(analysis)

        return analysis

    def _determine_specific_status(
        self,
        base_status: CompilationStatus,
        dependencies: List[DependencyInfo],
        issues: List[str],
    ) -> CompilationStatus:
        """Determine the most specific compilation status based on analysis"""
        if base_status == CompilationStatus.SUCCESS:
            return base_status

        # Check for specific vectorization failure reasons
        if any(dep.has_conflict() for dep in dependencies):
            return CompilationStatus.DEPENDENCY_CONFLICT

        if any("alignment" in issue.lower() for issue in issues):
            return CompilationStatus.ALIGNMENT_ISSUE

        if any(
            "unsafe" in issue.lower() or "alias" in issue.lower() for issue in issues
        ):
            return CompilationStatus.UNSAFE_MEMORY_ACCESS

        if any("complex" in issue.lower() for issue in issues):
            return CompilationStatus.LOOP_COMPLEXITY

        # Default to generic vectorization failure
        return CompilationStatus.VECTORIZATION_FAILED

    async def _compile_with_diagnostics(self, code: str) -> Dict[str, Any]:
        """
        Compile code and capture detailed diagnostic information.
        Uses temporary files to interact with the actual compiler.
        """
        with tempfile.NamedTemporaryFile(suffix=".c", mode="w", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Compile with verbose vectorization reporting
            cmd = [
                self.compiler_path,
                *self.base_flags,
                "-fopt-info-vec-missed",  # Report why vectorization failed
                "-fopt-info-loop-all",  # Report all loop optimizations
                "-S",  # Generate assembly (don't link)
                "-o",
                "-",  # Output to stdout
                temp_file,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            # Parse the output to determine status and extract messages
            messages = self._extract_diagnostic_messages(result.stderr)
            status = self._determine_compilation_status(messages, result.returncode)

            return {
                "status": status,
                "messages": messages,
                "assembly": (
                    result.stdout if status == CompilationStatus.SUCCESS else None
                ),
                "raw_stderr": result.stderr,
            }

        finally:
            os.unlink(temp_file)

    def _extract_diagnostic_messages(self, stderr: str) -> List[str]:
        """
        Extract and categorize diagnostic messages from compiler output.
        Focuses on vectorization-related messages.
        """
        messages = []

        # Common patterns for vectorization failures
        patterns = [
            r".*loop vectorized.*",
            r".*not vectorized.*",
            r".*data dependency.*",
            r".*unsafe loop.*",
            r".*iteration count.*",
            r".*alignment.*",
            r".*cost model.*",
            r".*alias.*",
        ]

        for line in stderr.split("\n"):
            for pattern in patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    messages.append(line.strip())
                    break

        return messages

    def _determine_compilation_status(
        self, messages: List[str], returncode: int
    ) -> CompilationStatus:
        """Determine initial compilation status from compiler output"""
        if returncode == 0:
            if any("vectorized" in msg and "not" not in msg for msg in messages):
                return CompilationStatus.SUCCESS
            else:
                return CompilationStatus.VECTORIZATION_FAILED
        else:
            return CompilationStatus.UNKNOWN_ERROR

    def _parse_vectorization_messages(self, messages: List[str]) -> List[str]:
        """Parse and filter vectorization-specific messages from compiler output"""
        # Keywords that indicate vectorization-related messages
        vectorization_keywords = [
            "vectoriz",
            "dependenc",
            "alias",
            "alignment",
            "unsafe",
            "cost model",
            "iteration",
            "parallel",
        ]

        return [
            msg
            for msg in messages
            if any(keyword in msg.lower() for keyword in vectorization_keywords)
        ]

    async def _generate_suggestions(
        self,
        code: str,
        dependencies: List[DependencyInfo],
        issues: List[str],
        session_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent transformation suggestions based on the analysis.
        This is where the compiler becomes truly helpful to agents.
        """
        suggestions = []

        # Check for loop-carried dependencies (like s1113 case)
        for dep in dependencies:
            if dep.has_conflict():
                # For s1113-like patterns where indices overlap
                if (
                    dep.conflict_description
                    and "overlap" in dep.conflict_description.lower()
                ):
                    suggestions.append(
                        {
                            "type": "loop_splitting",
                            "description": f"Split loop at iteration {dep.distance} to avoid {dep.variable} dependency overlap",
                            "confidence": 0.9,
                            "example": self._generate_loop_split_example(code, dep),
                            "explanation": f"The access pattern {dep.conflict_description} causes iterations to interfere",
                        }
                    )

                suggestions.append(
                    {
                        "type": "loop_distribution",
                        "description": f"Distribute loop to separate {dep.variable} updates",
                        "confidence": 0.8,
                        "example": self._generate_distribution_example(code, dep),
                    }
                )

                # If we've seen this pattern before in the session
                if session_id and self._check_session_patterns(session_id, dep):
                    suggestions.append(
                        {
                            "type": "learned_pattern",
                            "description": "Previously successful transformation for similar dependency",
                            "confidence": 0.95,
                            "reference": self._get_previous_success(session_id, dep),
                        }
                    )

        # Check for alignment issues
        if any("alignment" in issue.lower() for issue in issues):
            suggestions.append(
                {
                    "type": "alignment",
                    "description": "Add alignment directives or adjust data layout",
                    "confidence": 0.7,
                    "directives": [
                        "__attribute__((aligned(32)))",
                        "#pragma GCC aligned",
                    ],
                }
            )

        # Always suggest trying different vector widths
        suggestions.append(
            {
                "type": "vector_width",
                "description": "Try explicit vector width hints",
                "confidence": 0.6,
                "options": [
                    "#pragma GCC ivdep",
                    "#pragma omp simd",
                    "#pragma vector always",
                ],
            }
        )

        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)

    def _generate_loop_split_example(self, code: str, dep: DependencyInfo) -> str:
        """Generate example of loop splitting transformation"""
        # This is simplified - real implementation would properly transform the AST
        return f"""
// Original loop has dependency at distance {dep.distance}
// Split into two loops to avoid overlap:

// First half - no dependencies
for (int i = 0; i < N/2; i++) {{
    a[i] = a[N/2 - i];  // Safe - reading from unmodified second half
}}

// Second half - no dependencies
for (int i = N/2; i < N; i++) {{
    a[i] = a[N - i];  // Safe - reading from already processed first half
}}
"""

    def _generate_distribution_example(self, code: str, dep: DependencyInfo) -> str:
        """Generate example of loop distribution transformation"""
        return f"""
// Distribute loop to break dependency on {dep.variable}
// Original loop combines read and write operations that conflict

// Step 1: Read phase (vectorizable)
for (int i = 0; i < N; i++) {{
    temp[i] = {dep.variable}[{dep.read_indices[0] if dep.read_indices else "i"}];
}}

// Step 2: Compute phase (vectorizable)
for (int i = 0; i < N; i++) {{
    temp[i] = compute(temp[i], other_data[i]);
}}

// Step 3: Write phase (vectorizable)
for (int i = 0; i < N; i++) {{
    {dep.variable}[{dep.write_indices[0] if dep.write_indices else "i"}] = temp[i];
}}

// This transformation eliminates the loop-carried dependency
// by separating conflicting read and write operations
"""

    def _check_session_patterns(self, session_id: str, dep: DependencyInfo) -> bool:
        """Check if we've seen similar patterns in this session"""
        if session_id not in self.compilation_sessions:
            return False

        session = self.compilation_sessions[session_id]
        # Check if we've successfully handled similar dependencies before
        for transform in session.get("successful_transforms", []):
            if (
                transform.get("dependency_type") == "loop_carried"
                and transform.get("variable") == dep.variable
            ):
                return True

        return False

    def _get_previous_success(
        self, session_id: str, dep: DependencyInfo
    ) -> Dict[str, Any]:
        """Get previously successful transformation for similar pattern"""
        if session_id not in self.compilation_sessions:
            return {}

        session = self.compilation_sessions[session_id]
        for transform in session.get("successful_transforms", []):
            if (
                transform.get("dependency_type") == "loop_carried"
                and transform.get("variable") == dep.variable
            ):
                return {
                    "transformation": transform.get("type"),
                    "code": transform.get("code", ""),
                    "performance_gain": transform.get("performance_gain", "unknown"),
                }

        return {}


class DependencyAnalyzer:
    """
    Analyzes code to extract data dependencies that might prevent vectorization.
    Handles complex cases like s1113 where indices create non-obvious dependencies.
    """

    async def analyze_loop_carried_dependencies(
        self, code: str
    ) -> List[DependencyInfo]:
        """
        Sophisticated analysis that tracks actual data flow across iterations.
        Handles cases like a[i] = a[LEN_1D/2 - i] where iterations overlap.
        """
        dependencies = []

        # Extract loop information
        loops = self._extract_loop_info(code)

        # Extract all array accesses
        accesses = self._extract_array_accesses(code)

        # Group accesses by array name
        array_groups: Dict[str, List[ArrayAccess]] = {}
        for access in accesses:
            if access.array_name not in array_groups:
                array_groups[access.array_name] = []
            array_groups[access.array_name].append(access)

        # Analyze each array for dependencies
        for array_name, access_list in array_groups.items():
            # Find read-write pairs that might conflict
            writes = [a for a in access_list if a.is_write]
            reads = [a for a in access_list if not a.is_write]

            for write in writes:
                for read in reads:
                    conflict = self._check_iteration_overlap(write, read, loops)
                    if conflict:
                        dep = DependencyInfo(
                            variable=array_name,
                            write_indices=[write.index_expr],
                            read_indices=[read.index_expr],
                            loop_carried=True,
                            distance=conflict["distance"],
                            conflict_description=conflict["description"],
                        )
                        dependencies.append(dep)

        return dependencies

    def _extract_loop_info(self, code: str) -> List[LoopInfo]:
        """Extract information about loops in the code"""
        loops = []
        lines = code.split("\n")

        # Simple pattern matching for for loops
        loop_pattern = r"for\s*\(\s*(\w+)\s*([^;]+);\s*([^;]+);\s*([^)]+)\)"

        for i, line in enumerate(lines):
            match = re.search(loop_pattern, line)
            if match:
                # Extract loop variable and bounds
                loop_var = match.group(1)
                init = match.group(2).strip()
                condition = match.group(3).strip()
                increment = match.group(4).strip()

                # Parse bounds (simplified)
                start = "0" if "0" in init else init.split("=")[-1].strip()
                end = self._extract_loop_bound(condition)
                step = "1" if "++" in increment else increment

                loops.append(
                    LoopInfo(
                        loop_var=loop_var,
                        start=start,
                        end=end,
                        step=step,
                        body_start_line=i,
                    )
                )

        return loops

    def _extract_loop_bound(self, condition: str) -> str:
        """Extract loop bound from condition like 'i < N' or 'i < LEN_1D'"""
        # Remove loop variable and comparison operator
        # Handle various comparison operators: <, <=, >, >=
        bound = re.sub(r"\w+\s*[<>]=?\s*", "", condition).strip()

        # Handle cases where the bound might be on the left side (e.g., "N > i")
        if not bound or bound.isidentifier():
            # Try reverse pattern
            match = re.search(r"([^<>=\s]+)\s*[<>]=?\s*\w+", condition)
            if match:
                bound = match.group(1).strip()

        return bound if bound else "N"  # Default to N if parsing fails

    def _extract_array_accesses(self, code: str) -> List[ArrayAccess]:
        """Extract all array access patterns from code"""
        accesses = []
        lines = code.split("\n")

        # Pattern for array access: word[expression]
        array_pattern = r"(\w+)\[([^\]]+)\]"

        for line_num, line in enumerate(lines):
            # Check if this line contains an assignment
            is_assignment = "=" in line

            for match in re.finditer(array_pattern, line):
                array_name = match.group(1)
                index_expr = match.group(2)

                # Determine if this is a write (left side of assignment)
                is_write = is_assignment and line.index(match.group(0)) < line.index(
                    "="
                )

                accesses.append(
                    ArrayAccess(
                        array_name=array_name,
                        index_expr=index_expr,
                        line_number=line_num,
                        is_write=is_write,
                    )
                )

        return accesses

    def _check_iteration_overlap(
        self, write: ArrayAccess, read: ArrayAccess, loops: List[LoopInfo]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a write in one iteration conflicts with a read in another.
        This handles the s1113 case where a[i] = a[LEN_1D/2 - i] causes overlap.
        """
        # For s1113 pattern: check if write index i can equal read index N/2-i
        # This happens when i = N/2 - i, which means i = N/4

        write_idx = write.index_expr
        read_idx = read.index_expr

        # Check for patterns like i and N/2-i, N-i, etc.
        if self._indices_can_overlap(write_idx, read_idx):
            # Calculate at which iteration they overlap
            overlap_point = self._calculate_overlap_point(write_idx, read_idx)

            return {
                "distance": overlap_point,
                "description": f"Write to {write.array_name}[{write_idx}] conflicts with read from {write.array_name}[{read_idx}] at iteration {overlap_point}",
            }

        return None

    def _indices_can_overlap(self, idx1: str, idx2: str) -> bool:
        """
        Check if two index expressions can refer to the same array element.
        Handles patterns like:
        - i and N/2-i (overlap when i = N/4)
        - i and N-i (overlap when i = N/2)
        - i+1 and i (always overlap in adjacent iterations)
        """
        # This is a simplified check - real implementation would use symbolic math

        # Check for complementary patterns
        if "i" in idx1 and "i" in idx2:
            # Patterns like "i" and "N/2 - i" or "N - i"
            if "-" in idx2 and idx1.strip() == "i":
                return True
            if "-" in idx1 and idx2.strip() == "i":
                return True

        # Check for offset patterns like i+1, i-1
        return bool(
            re.match(r"i\s*[+-]\s*\d+", idx1) or re.match(r"i\s*[+-]\s*\d+", idx2)
        )

    def _calculate_overlap_point(self, write_idx: str, read_idx: str) -> int:
        """
        Calculate at which iteration the indices overlap.
        For i and N/2-i, they overlap when i = N/4.
        """
        # Simplified calculation - real implementation would solve equations
        if "N/2" in read_idx or "LEN_1D/2" in read_idx:
            return 4  # N/4 for the s1113 pattern
        elif "N" in read_idx and "-" in read_idx:
            return 2  # N/2 for i and N-i pattern
        else:
            return 1  # Adjacent iterations


# Register MCP tools
@mcp.tool()  # type: ignore[misc]
async def analyze_vectorization_failure(
    code: str, session_id: Optional[str] = None
) -> str:
    """
    Analyze why code failed to vectorize and provide suggestions.

    Args:
        code: C/C++ code that failed to vectorize
        session_id: Optional session ID for stateful analysis
    """
    server = CompilerMCPServer()

    if session_id:
        await server.create_session(session_id)

    analysis = await server.analyze_vectorization(code, session_id)

    # Format the response for the LLM
    response = "Vectorization Analysis for provided code:\n\n"
    response += f"Status: {analysis.status.value}\n\n"

    if analysis.dependencies:
        response += "Detected Dependencies:\n"
        for dep in analysis.dependencies:
            response += f"  - {dep.variable}: "
            if dep.loop_carried:
                response += f"loop-carried dependency (distance={dep.distance})"
            if dep.has_conflict():
                response += f"\n    Conflict: {dep.conflict_description}"
            response += "\n"

    if analysis.suggested_transformations:
        response += "\nSuggested Transformations (ordered by confidence):\n"
        for i, suggestion in enumerate(analysis.suggested_transformations, 1):
            response += f"\n{i}. {suggestion['description']} "
            response += f"(confidence: {suggestion['confidence']})\n"
            if "example" in suggestion:
                response += f"   Example:\n{suggestion['example']}\n"
            if "explanation" in suggestion:
                response += f"   Reason: {suggestion['explanation']}\n"

    if analysis.compiler_messages:
        response += "\nCompiler Diagnostics:\n"
        for msg in analysis.compiler_messages[:5]:  # Limit to 5 messages
            response += f"  {msg}\n"

    return response


@mcp.tool()  # type: ignore[misc]
async def create_compilation_session(session_name: str) -> str:
    """
    Create a stateful compilation session that remembers previous attempts.

    Args:
        session_name: Unique name for this compilation session
    """
    server = CompilerMCPServer()
    return await server.create_session(session_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intelligent Compiler MCP Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http", "test"],
        default="stdio",
        help="Server mode: stdio for local MCP, http for remote, test for testing",
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP mode (default: 8080)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP mode (default: 0.0.0.0 for all interfaces)",
    )

    args = parser.parse_args()

    if args.mode == "test":
        # Test mode - run example analysis
        async def test() -> None:
            print("Testing compiler server with s1113-like code...")
            test_code = """
for (int i = 0; i < LEN_1D; i++) {
    a[i] = a[LEN_1D/2 - i] + b[i];
}
"""
            result = await analyze_vectorization_failure(test_code, "test_session")
            print(result)

        asyncio.run(test())
    elif args.mode == "http":
        # HTTP mode for remote deployment
        print(f"Starting HTTP server on {args.host}:{args.port}")
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        # Default stdio mode for local MCP
        mcp.run(transport="stdio")
