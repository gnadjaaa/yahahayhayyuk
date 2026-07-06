#!/usr/bin/env python3
"""
SCTF26 - Predictable Future
Z3 Solver dengan peningkatan constraint twist secara otomatis
"""

from z3 import *
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import struct
import re
import time

# ==================== MT19937 Tempering ====================

def temper(y):
    y = y ^ (y >> 11)
    y = y ^ ((y << 7) & 0x9D2C5680)
    y = y ^ ((y << 15) & 0xEFC60000)
    y = y ^ (y >> 18)
    return y & 0xFFFFFFFF

def untemper(y):
    y = y ^ (y >> 18)
    y = y ^ ((y << 15) & 0xEFC60000)
    y = y ^ ((y << 7) & 0x9D2C5680)
    y = y ^ ((y << 7) & 0x9D2C5680)
    y = y ^ ((y << 7) & 0x9D2C5680)
    y = y ^ ((y << 7) & 0x9D2C5680)
    y = y ^ (y >> 11)
    y = y ^ (y >> 22)
    return y & 0xFFFFFFFF

# ==================== MT19937 Class ====================

class MT19937:
    def __init__(self):
        self.mt = [0] * 624
        self.index = 624

    def set_state(self, state):
        self.mt = state[:]
        self.index = 624

    def twist(self):
        for i in range(624):
            y = (self.mt[i] & 0x80000000) + (self.mt[(i+1) % 624] & 0x7fffffff)
            self.mt[i] = self.mt[(i + 397) % 624] ^ (y >> 1)
            if y & 1:
                self.mt[i] ^= 0x9908B0DF
        self.index = 0

    def extract_number(self):
        if self.index >= 624:
            self.twist()
        y = self.mt[self.index]
        self.index += 1
        return temper(y)

# ==================== Z3 Recovery dengan jumlah constraint variabel ====================

def recover_state_with_z3(lsbs, num_twist_constraints):
    """
    Recover state using Z3 with a given number of twist constraints
    """
    print(f"[*] Trying with {num_twist_constraints} twist constraints...")
    solver = Solver()
    # solver.set(timeout=60000)  # 60 second timeout
    
    # Create variables
    mt = [BitVec(f'mt_{i}', 32) for i in range(624)]
    
    # Tempering function in Z3
    def temper_z3(y):
        y = y ^ (y >> 11)
        y = y ^ ((y << 7) & 0x9D2C5680)
        y = y ^ ((y << 15) & 0xEFC60000)
        y = y ^ (y >> 18)
        return y
    
    # Add LSB constraints for first 624 outputs
    for i in range(624):
        tempered = temper_z3(mt[i])
        solver.add((tempered & 0xFF) == lsbs[i])
    
    # MT19937 constants
    n, m = 624, 397
    a = 0x9908B0DF
    lower_mask = 0x7FFFFFFF
    upper_mask = 0x80000000
    
    # Add twist constraints for indices 0..num_twist_constraints-1
    for i in range(num_twist_constraints):
        y = (mt[i] & upper_mask) | (mt[(i+1) % n] & lower_mask)
        result = mt[(i + m) % n] ^ (y >> 1)
        result = If((y & 1) == 1, result ^ a, result)
        solver.add(mt[i] == result)
    
    start = time.time()
    if solver.check() == sat:
        elapsed = time.time() - start
        print(f"[+] Z3 found solution in {elapsed:.2f}s")
        model = solver.model()
        state = [model.eval(mt[i]).as_long() for i in range(624)]
        return state
    else:
        print("[!] Z3 unsat")
        return None

# ==================== Verifikasi State ====================

def verify_state(state, lsbs, num_check=100):
    """
    Verifikasi state dengan memeriksa beberapa output berikutnya
    """
    mt = MT19937()
    mt.set_state(state)
    
    # Skip 624 outputs
    for _ in range(624):
        mt.extract_number()
    
    # Check next 'num_check' outputs
    for i in range(num_check):
        if i >= len(lsbs) - 624:
            break
        predicted = mt.extract_number()
        expected_lsb = lsbs[624 + i]
        if (predicted & 0xFF) != expected_lsb:
            print(f"[!] Verification failed at offset {i}: predicted LSB {predicted & 0xFF}, expected {expected_lsb}")
            return False
    print(f"[+] State verified successfully! (checked {num_check} outputs)")
    return True

# ==================== Decrypt Flag ====================

def decrypt_flag(key_bytes):
    encrypted = bytes.fromhex("38c9e92b118434a05e9bffd3605602061268d420ab9bda37849b6fc99ff85c81564a6a4476b6b144ccea81714e243ecac0b32b8cdc0a40afb37cb610c48a16e80")
    
    try:
        cipher = AES.new(key_bytes[:16], AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted)
        try:
            flag = unpad(decrypted, AES.block_size)
            return flag.decode('utf-8')
        except ValueError:
            decoded = decrypted.decode('utf-8', errors='ignore')
            match = re.search(r'SCTF\{[^}]+\}', decoded)
            if match:
                return match.group()
            return None
    except Exception as e:
        print(f"[!] Decryption error: {e}")
        return None

# ==================== Main ====================

def main():
    print("\n" + "="*70)
    print("  SCTF26 - Predictable Future - Auto Solver")
    print("="*70 + "\n")
    
    # Read LSBs
    try:
        with open('predictable.txt', 'r') as f:
            lsbs = [int(line.strip()) for line in f.readlines() if line.strip()]
        print(f"[+] Loaded {len(lsbs)} LSB values")
    except FileNotFoundError:
        print("[!] Error: predictable.txt not found!")
        return
    
    if len(lsbs) < 624:
        print(f"[!] Need at least 624 LSB values, got {len(lsbs)}")
        return
    
    # Coba dengan jumlah twist constraints yang meningkat
    twist_counts = [30, 50, 75, 100, 150, 200, 300, 400, 500, 624]
    
    state = None
    for count in twist_counts:
        state = recover_state_with_z3(lsbs, count)
        if state is None:
            continue
        
        # Verify
        if verify_state(state, lsbs, min(100, len(lsbs)-624)):
            break
        else:
            print(f"[*] Verification failed with {count} constraints, trying more...")
            state = None
    
    if state is None:
        print("\n[!] Could not recover valid state with any constraint count.")
        print("[!] Try increasing twist_counts or using a different approach.")
        return
    
    # Predict next 4 outputs
    print("\n[*] Predicting next 4 outputs...")
    mt = MT19937()
    mt.set_state(state)
    for _ in range(624):
        mt.extract_number()
    
    next_outputs = []
    for i in range(4):
        val = mt.extract_number()
        next_outputs.append(val)
        print(f"    Output {i+1}: 0x{val:08x}")
    
    # Build AES key
    key_bytes = b''
    for val in next_outputs:
        key_bytes += struct.pack('<I', val)
    
    print(f"\n[+] AES Key (hex): {key_bytes.hex()}")
    
    # Decrypt flag
    print("\n[*] Decrypting flag...")
    flag = decrypt_flag(key_bytes)
    
    if flag:
        print("\n" + "="*70)
        print(f"🏁 FLAG: {flag}")
        print("="*70)
    else:
        print("\n[!] Could not decrypt flag. The key might be incorrect.")
        print("[!] Try manual verification of the recovered state.")

if __name__ == "__main__":
    main()