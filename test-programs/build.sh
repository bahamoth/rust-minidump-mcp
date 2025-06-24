#!/bin/bash
set -e

echo "Building crash-generator for multiple platforms..."

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
        
        echo "Extracting symbols for $target..."
        ../minidumpmcp/tools/bin/dump_syms-$(uname | tr '[:upper:]' '[:lower:]') \
            "target/$target/release/crash-generator$ext" \
            > "../tests/testdata/binaries/crash-generator-$target.sym" || true
    else
        echo "Target $target not installed, skipping..."
    fi
done

echo "Build complete!"