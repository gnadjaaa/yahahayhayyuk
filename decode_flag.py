#!/usr/bin/env python3
keys = [0x42, 0x02, 0x06, 0x40, 0x20, 0x55, 0xFF]
files = input("Masukkan nama file binary target: ").strip()

with open(files,'rb') as f:
    data = f.read()

for k in keys:
    out = bytes(b ^ k for b in data)
    try:
        s = out.decode('utf-8', errors='replace')
    except Exception:
        s = repr(out[:200])
    print(f"key=0x{k:02x} ->\n{s[:500]}\n---\n")
