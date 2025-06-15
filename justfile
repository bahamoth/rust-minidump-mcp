# Default recipe
help:
    @just --list

# Install Rust tools to the tools/ directory
install-tools:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Installing minidump-stackwalk and dump_syms to tools/bin directory..."

    # Create tools directory if it doesn't exist
    mkdir -p tools

    # Install minidump-stackwalk
    cargo install minidump-stackwalk --root=./tools

    # Install dump_syms
    cargo install dump_syms --root=./tools

    echo "Installation complete. Tools are available in the tools/bin directory."

