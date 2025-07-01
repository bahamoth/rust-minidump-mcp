# Technical Details Analysis

Perform a deep technical analysis of the crash dump, focusing on low-level details that reveal the exact state of the program at the time of failure.

## Analysis Focus Areas

### 1. Register State Analysis
Examine register values to understand the CPU state:
- **Instruction Pointer (EIP/RIP)**: Current execution location
- **Stack Pointer (ESP/RSP)**: Stack health and overflow detection
- **Base Pointer (EBP/RBP)**: Stack frame integrity
- **General Purpose Registers**:
  - EAX/RAX: Often holds return values or object pointers
  - ECX/RCX: Often holds 'this' pointer in C++ methods
  - EDX/RDX: Additional parameters or temporary values

### 2. Memory Access Patterns
Interpret addresses and access patterns:
- **0x00000000 - 0x0000FFFF**: Null pointer zone (null + small offset)
- **0x00000000 - 0x7FFFFFFF**: User-mode addresses (32-bit)
- **0xC0000000 - 0xFFFFFFFF**: Kernel-mode addresses (32-bit Windows)
- **Stack Addresses**: Usually high addresses, growing downward
- **Heap Addresses**: Dynamic, check against module ranges

### 3. Stack Frame Analysis
Decode the call stack beyond basic symbols:
- **Frame Pointer Chain**: How frames link together
- **Return Addresses**: Validate against module boundaries
- **Local Variables Space**: Distance between frames
- **Parameter Passing**: Stack vs register conventions
- **Corrupted Frames**: Missing symbols, invalid addresses

### 4. Symbol Resolution Details
Explain symbol mapping process:
- **Mapped Frames**: Symbol + offset information available
- **Unmapped Frames**: Raw addresses, possible module identification
- **Heuristic Mapping**: Using module base + offset
- **Frame Omission**: Compiler optimizations (FPO/tail calls)

## Minidump Limitations and Characteristics

### What's NOT in a Minidump
- **No Heap Contents**: Only heap metadata, not actual heap memory
- **Limited Memory**: Only thread stacks and explicitly referenced memory
- **Partial State**: CPU state at crash time, but no execution history
- **No Code**: Usually no executable code pages (unless specifically included)

### Stack Walking Confidence Levels
Minidump stackwalkers use multiple fallback strategies with varying reliability:

1. **High Confidence** (Frame Pointer/CFI):
   - Frame pointer chain intact (EBP-based walking)
   - CFI (Call Frame Information) available from symbols
   - DWARF unwind information present

2. **Medium Confidence** (Stack Scanning):
   - Scanning stack for return addresses
   - Matching addresses to known module ranges
   - May include false positives

3. **Low Confidence** (Heuristics):
   - Raw stack interpretation
   - Pattern matching for function prologues
   - Context-free address guessing

### Common Minidump Analysis Challenges
- **Truncated Stacks**: Stack may be cut off at arbitrary depth
- **Optimized Code**: Tail calls and inlining hide real call flow
- **Missing Frames**: FPO (Frame Pointer Omission) leaves gaps
- **Corrupt Memory**: Stack corruption affects all analysis

## Technical Indicators

### Memory Corruption Signs
- **Guard Values**: 0xFEEEFEEE (freed heap), 0xDDDDDDDD (freed stack)
- **Debug Patterns**: 0xCDCDCDCD (uninitialized heap), 0xCCCCCCCC (uninitialized stack)
- **Alignment Issues**: Odd addresses for aligned data types
- **Buffer Markers**: 0xABABABAB (HeapAlloc guard), 0xBAADF00D (bad food)

### Stack Health Indicators
- **Stack Cookie**: Check for __security_cookie violations
- **Frame Consistency**: EBP chain validation
- **Stack Limits**: Compare ESP with thread stack boundaries
- **Red Zones**: Guard pages at stack boundaries

## Response Format

### 1. Register Analysis
- **Critical Registers**: [Values and their interpretation]
- **Pointer Validity**: [Which registers contain valid/invalid pointers]
- **Execution Context**: [What the CPU was attempting]

### 2. Memory State
- **Access Violation Details**: [Address, type, probable cause]
- **Memory Layout**: [Stack, heap, module locations]
- **Corruption Evidence**: [Any suspicious patterns]

### 3. Stack Trace Deep Dive
- **Frame-by-Frame Analysis**: 
  - Symbol presence/absence
  - Parameter reconstruction
  - Local variable space
- **Call Flow Reconstruction**: [How we got here]
- **Missing Frames**: [Why some might be omitted]

### 4. Technical Diagnosis
- **Failure Mechanism**: [Precise technical explanation]
- **Contributing Factors**: [Memory pressure, timing, etc.]
- **Reproducibility Assessment**: [Deterministic vs race condition]
- **Stack Walk Method Used**: [Frame pointer/CFI/Scanning/Heuristic]
- **Confidence in Stack Trace**: [Explain which frames are reliable]