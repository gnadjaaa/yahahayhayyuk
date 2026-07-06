#!/usr/bin/env python3
"""
Generic solver untuk crackme binary dengan pola:
- main(argc, argv) baca argv[1]
- tiap char di-XOR sama key (biasanya 0x42)
- dibandingkan ke buffer constant yang di-load via beberapa instruksi
  `movabs`/`mov` (mov reg, imm64 / mov [mem], imm32 / mov [mem], imm16 / mov [mem], imm8)

Cara kerja:
1. objdump -d binary, ambil semua instruksi immediate-mov ke stack SEBELUM instruksi
   xor utama (biasanya `xor eax, 0x42` atau sejenisnya) muncul di fungsi main.
2. Susun byte-byte immediate itu sesuai urutan address (little-endian per chunk).
3. XOR semua byte dengan key yang ditemukan otomatis dari instruksi `xor eax, 0xXX`.
4. Print hasilnya sebagai candidate flag, lalu verifikasi otomatis ke binary.

Catatan: heuristik ini didesain untuk template crackme yang berulang di CTF ini
(pola: movabs rax,<imm64> / movabs rdx,<imm64> / mov [mem],imm32 / mov [mem],imm16 / mov [mem],imm8
diikuti loop yang nge-XOR input dengan key konstan).
"""

import re
import struct
import subprocess
import sys

def autosolver():
    def objdump(binary):
        out = subprocess.run(
            ["objdump", "-d", binary, "-M", "intel"],
            capture_output=True, text=True
        ).stdout
        return out


    def extract_main(asm_text):
        m = re.search(r"<main>:\n(.*?)\n\n", asm_text, re.S)
        if not m:
            m = re.search(r"<main>:\n(.*)", asm_text, re.S)
        return m.group(1)


    def find_xor_key(main_asm):
        m = re.search(r"xor\s+e\w\w,0x([0-9a-f]+)", main_asm)
        if m:
            return int(m.group(1), 16)
        return None


    def find_immediate_chunks(main_asm):
        """
        Ambil semua instruksi yang menulis immediate constant ke stack:
        movabs rax,0x...   (8 byte, harus dipasangkan ke 'mov QWORD PTR [..],rax' selanjutnya)
        mov QWORD PTR [..],0x...   (8 byte langsung kalau imm cukup kecil - biasanya tidak terjadi untuk imm64)
        mov DWORD PTR [..],0x...   (4 byte)
        mov WORD PTR [..],0x...    (2 byte)
        mov BYTE PTR [..],0x...    (1 byte)
        Mengembalikan list of (address:int, bytes)
        urut berdasarkan address instruksi.
        """
        chunks = []

        lines = main_asm.splitlines()
        pending = {} 

        line_re = re.compile(r"^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2}\s+)+\s*(.*)$")

        for line in lines:
            m = line_re.match(line)
            if not m:
                continue
            addr = int(m.group(1), 16)
            instr = m.group(2).strip()

            m2 = re.match(r"movabs\s+(r\w\w),0x([0-9a-f]+)", instr)
            if m2:
                reg, imm_hex = m2.group(1), m2.group(2)
                pending[reg] = struct.pack("<Q", int(imm_hex, 16))
                continue

            m3 = re.match(r"mov\s+QWORD PTR \[.*?\],(r\w\w)$", instr)
            if m3:
                reg = m3.group(1)
                if reg in pending:
                    chunks.append((addr, pending.pop(reg)))
                continue

            m4 = re.match(r"mov\s+DWORD PTR \[.*?\],0x([0-9a-f]+)", instr)
            if m4:
                chunks.append((addr, struct.pack("<I", int(m4.group(1), 16))))
                continue

            m5 = re.match(r"mov\s+WORD PTR \[.*?\],0x([0-9a-f]+)", instr)
            if m5:
                chunks.append((addr, struct.pack("<H", int(m5.group(1), 16))))
                continue

            m6 = re.match(r"mov\s+BYTE PTR \[.*?\],0x([0-9a-f]+)", instr)
            if m6:
                chunks.append((addr, struct.pack("<B", int(m6.group(1), 16))))
                continue

        chunks.sort(key=lambda x: x[0])
        return chunks


    def find_compare_length(main_asm):
        matches = re.findall(r"cmp\s+eax,0x([0-9a-f]+)\n\s+[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+jbe", main_asm)
        if matches:
            return int(matches[-1], 16) + 1  
        return None


    def main():
        if len(sys.argv) != 2:
            print(f"Usage: {sys.argv[0]} <path_to_crackme_binary>")
            sys.exit(1)

        binary = sys.argv[1]
        asm = objdump(binary)
        main_asm = extract_main(asm)

        key = find_xor_key(main_asm)
        if key is None:
            print("[-] Gak ketemu XOR key otomatis, cek manual ya.")
            sys.exit(1)
        print(f"[+] XOR key ditemukan: 0x{key:02x}")

        chunks = find_immediate_chunks(main_asm)
        if not chunks:
            print("[-] Gak ketemu chunk encoded constant, cek manual ya.")
            sys.exit(1)

        encoded = b"".join(data for _, data in chunks)
        print(f"[+] Encoded bytes (raw, {len(encoded)} byte): {encoded.hex()}")

        cmp_len = find_compare_length(main_asm)
        if cmp_len:
            print(f"[+] Panjang flag asli (dari cmp loop): {cmp_len}")
            encoded = encoded[:cmp_len]

        flag_bytes = bytes([b ^ key for b in encoded])
        try:
            flag = flag_bytes.decode()
        except UnicodeDecodeError:
            flag = None

        print(f"[+] Candidate flag bytes: {flag_bytes}")
        if flag:
            print(f"[+] Candidate flag: {flag}")

            # auto verify
            result = subprocess.run([binary, flag], capture_output=True, text=True)
            print(f"[+] Verifikasi run binary -> stdout: {result.stdout.strip()!r}")


    if __name__ == "__main__":
        main()