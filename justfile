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

