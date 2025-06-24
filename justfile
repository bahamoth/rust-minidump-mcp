# Default recipe
help:
    @just --list

# Install Rust tools to the tools/ directory
install-tools:
    #!/usr/bin/env bash

    detect_target() {
        case "$(rustc -vV | grep 'host: ' | awk '{print $2}')" in
            *-apple-darwin*)
                echo "macos"
                ;;
            *-unknown-linux-gnu*)
                echo "linux"
                ;;
            *-pc-windows-msvc*)
                echo "windows"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    }

    set -euo pipefail
    echo "Installing minidump-stackwalk and dump_syms to tools/bin directory..."

    TARGET=$(detect_target)
    echo "Detected target architecture: $TARGET"

    # Create tools directory if it doesn't exist
    mkdir -p tools

    # Install minidump-stackwalk
    cargo install minidump-stackwalk --no-track --root=./minidumpmcp/tools
    mv ./minidumpmcp/tools/bin/minidump-stackwalk ./minidumpmcp/tools/bin/minidump-stackwalk-${TARGET}

    # Install dump_syms
    cargo install dump_syms --no-track --root=./minidumpmcp/tools
    mv ./minidumpmcp/tools/bin/dump_syms ./minidumpmcp/tools/bin/dump-syms-${TARGET}

    echo "Installation complete. Tools are available in the minidumpmcp/tools/bin directory."

# Build test crash generator
build-test-programs:
    cd test-programs && cargo build --release

# Build test programs for all platforms
build-test-programs-all:
    #!/usr/bin/env bash
    set -e
    
    cd test-programs
    
    TARGETS=(
        "x86_64-unknown-linux-gnu"
        "x86_64-pc-windows-gnu"
        "x86_64-apple-darwin"
        "aarch64-apple-darwin"
    )
    
    mkdir -p ../tests/testdata/binaries
    
    for target in "${TARGETS[@]}"; do
        echo "Building for $target..."
        
        if rustup target list --installed | grep -q "$target"; then
            cargo build --release --target "$target"
            
            if [[ "$target" == *"windows"* ]]; then
                ext=".exe"
            else
                ext=""
            fi
            
            cp "target/$target/release/crash-generator$ext" "../tests/testdata/binaries/crash-generator-$target$ext"
        else
            echo "Target $target not installed, skipping..."
        fi
    done

# Extract symbols from test binaries
extract-test-symbols:
    #!/usr/bin/env bash
    set -e
    
    detect_target() {
        case "$(rustc -vV | grep 'host: ' | awk '{print $2}')" in
            *-apple-darwin*)
                echo "macos"
                ;;
            *-unknown-linux-gnu*)
                echo "linux"
                ;;
            *-pc-windows-msvc*)
                echo "windows"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    }
    
    TARGET=$(detect_target)
    DUMP_SYMS="./minidumpmcp/tools/bin/dump-syms-${TARGET}"
    
    mkdir -p tests/testdata/symbols
    
    for binary in tests/testdata/binaries/crash-generator-*; do
        if [[ -f "$binary" && ! "$binary" =~ \.sym$ ]]; then
            echo "Extracting symbols from $binary..."
            "$DUMP_SYMS" "$binary" > "${binary}.sym" || echo "Failed to extract symbols from $binary"
        fi
    done

# Generate crash dumps for testing
generate-test-dumps:
    #!/usr/bin/env bash
    set -e
    
    CRASH_TYPES=("null" "stack-overflow" "divide-by-zero" "assert" "panic" "segfault")
    OUTPUT_DIR="tests/testdata/dumps"
    
    mkdir -p "$OUTPUT_DIR"
    
    echo "Generating crash dumps..."
    
    for crash_type in "${CRASH_TYPES[@]}"; do
        echo "Generating $crash_type dump..."
        ./test-programs/target/release/crash-generator "$crash_type" \
            --generate-dump \
            --output "$OUTPUT_DIR/$crash_type.dmp" || true
    done

# Complete test setup: build, extract symbols, generate dumps
setup-test-environment: build-test-programs extract-test-symbols generate-test-dumps
    echo "Test environment setup complete!"

