#!/usr/bin/env python3
# ==========================================
# Tool Name : picoCTF Automation & Helper Tool
# Author    : @gnadjaaa_ (Instagram)
# ==========================================

import sys
import os
import socket
import urllib.request
import urllib.parse
import base64
import hashlib

def banner():
    print("=" * 50)
    print("          picoCTF AUTOMATION & HELPER TOOL          ")
    print("             Created by: @gnadjaaa_                 ")
    print("=" * 50)

# ==========================================
# 1. PENGECEK IP (IP & NETWORK CHECKER)
# ==========================================
def menu_ip_checker():
    print("\n[+] Kategori: Pengecek IP & Domain")
    target = input("Masukkan Domain / IP target (cth: jupiter.challenges.picoctf.org): ").strip()
    if not target:
        return
    
    try:
        # Resolusi DNS ke IP
        ip_addr = socket.gethostbyname(target)
        print(f"[*] Target Domain: {target}")
        print(f"[*] IP Address   : {ip_addr}")
        
        # Cek IP Publik kita sendiri (berguna jika pakai VPN saat CTF)
        print("[*] Mengecek IP Publik Anda...")
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as response:
            my_ip = response.read().decode('utf-8')
            print(f"[*] IP Publik Anda: {my_ip}")
    except Exception as e:
        print(f"[-] Gagal melakukan pengecekan: {e}")

# ==========================================
# 2. WEB EXPLOITATION (BRUTE FORCE COOKIE/DIR)
# ==========================================
def menu_web_exploit():
    print("\n[+] Kategori: Web Exploitation (Basic URL/Cookie Brute Force)")
    url = input("Masukkan URL Target (cth: http://example.com/): ").strip()
    param_name = input("Masukkan Nama Cookie/Parameter yang mau di-brute force (cth: auth_level): ").strip()
    
    print("[*] Memulai simulasi brute force nilai 0 - 20 (Sering keluar di picoCTF Cookie/Web)...")
    for i in range(21):
        try:
            req = urllib.request.Request(url)
            # Mengubah cookie untuk setiap iterasi
            req.add_header('Cookie', f'{param_name}={i}')
            
            with urllib.request.urlopen(req, timeout=3) as response:
                content = response.read().decode('utf-8', errors='ignore')
                # Mencari pola flag picoCTF dalam respon web
                if "picoCTF" in content or "flag" in content.lower():
                    print(f"[===>] FLAG/PETUNJUK DITEMUKAN pada nilai {param_name}={i} !")
                    # Menampilkan potongan teks di sekitar kata picoCTF
                    idx = content.find("picoCTF")
                    if idx != -1:
                        print(f"[!] Konten: {content[idx:idx+100]}")
                    else:
                        print(f"[!] Konten: Menemukan kata 'flag'")
                    return
                else:
                    print(f"[-] Mencoba nilai {i}... Bukan ini.")
        except Exception as e:
            print(f"[-] Error pada nilai {i}: {e}")
    print("[-] Brute force selesai. Tidak ada kecocokan otomatis (Coba cek manual).")

# ==========================================
# 3. KRIPTOGRAFI (CRYPTO DECODER - CUSTOM SHIFT)
# ==========================================
def menu_crypto():
    print("\n[+] Kategori: Cryptography Decoder")
    print("1. Base64 Decode")
    print("2. Caesar Cipher (Custom Shift / ROT)")
    print("3. MD5 / SHA256 Hash Generator")
    pilihan = input("Pilih jenis crypto (1-3): ").strip()
    
    teks = input("Masukkan teks/cipher yang ingin diproses: ").strip()
    
    if pilihan == "1":
        try:
            decoded = base64.b64decode(teks).decode('utf-8', errors='ignore')
            print(f"[+] Hasil Base64 Decode: {decoded}")
        except Exception as e:
            print(f"[-] Gagal decode Base64: {e}")
            
    elif pilihan == "2":
        try:
            shift_input = input("Masukkan jumlah shift/pergeseran (0-25) ATAU ketik 'all' untuk brute force: ").strip().lower()
            
            def caesar_decrypt(cipher_text, shift_val):
                result = ""
                for char in cipher_text:
                    if char.isalpha():
                        start = ord('A') if char.isupper() else ord('a')
                        decrypted_char = chr((ord(char) - start - shift_val) % 26 + start)
                        result += decrypted_char
                    else:
                        result += char
                return result

            if shift_input == 'all':
                print("\n[*] Menampilkan semua kemungkinan pergeseran (Brute Force):")
                print("-" * 40)
                for s in range(26):
                    print(f"Shift {s:2d} (ROT-{s:2d}): {caesar_decrypt(teks, s)}")
                print("-" * 40)
            else:
                shift_val = int(shift_input)
                if 0 <= shift_val <= 25:
                    print(f"[+] Hasil Dekripsi (Shift {shift_val}): {caesar_decrypt(teks, shift_val)}")
                else:
                    print("[-] Angka shift harus di antara 0 sampai 25.")
        except ValueError:
            print("[-] Input tidak valid. Masukkan angka atau ketik 'all'.")
        
    elif pilihan == "3":
        md5_hash = hashlib.md5(teks.encode()).hexdigest()
        sha256_hash = hashlib.sha256(teks.encode()).hexdigest()
        print(f"[+] MD5    : {md5_hash}")
        print(f"[+] SHA256 : {sha256_hash}")

# ==========================================
# 4. CONTEKAN COMMAND LINUX (CHEATSHEET)
# ==========================================
def menu_linux_commands():
    print("\n" + "="*60)
    print("      CONTEKAN COMMAND LINUX PENTING UNTUK CTF (PICOCTF)      ")
    print("="*60)
    
    cheatsheet = """
    1. GENERAL SKILLS & FILE ANALYSIS:
       file <nama_file>      -> Cek jenis asli file (meski ekstensinya diubah).
       strings <nama_file>   -> Cari teks berwujud teks biasa di dalam file binary.
       strings file | grep picoCTF -> Cara cepat temukan flag di file besar.
       grep -r "pico" .      -> Cari kata 'pico' di semua file di folder saat ini secara rekursif.
       cat nama_file         -> Melihat isi file teks.
       
    2. NETWORKING & NETCAT (NC):
       nc <host> <port>      -> Konek ke server soal (paling sering dipakai di picoCTF).
       nc -lvnp <port>       -> Membuka listener untuk menerima reverse shell.
       
    3. FORENSICS (EKSTRAKSI DATA):
       binwalk -e <file>     -> Ekstrak file tersembunyi di dalam file lain (steganography).
       exiftool <file>       -> Melihat metadata tersembunyi pada gambar/dokumen.
       tar -xf <file.tar>    -> Ekstrak file kompresi .tar
       unzip <file.zip>      -> Ekstrak file .zip
       
    4. PERMISSIONS & EXECUTABLES (PWN/REV):
       chmod +x <file>       -> Beri izin eksekusi pada file script/binary (.sh / .elf).
       ./<file_binary>       -> Menjalankan file binary Linux secara langsung.
       ldd <file_binary>     -> Cek library dynamic (.so) yang dibutuhkan aplikasi.
       
    5. DATA CONVERSION / TRICKS:
       echo "teks" | base64   -> Encode teks ke base64 lewat terminal.
       echo "bY=..." | base64 -d -> Decode base64 lewat terminal.
       xxd <file>            -> Melihat hex dump dari suatu file.
    """
    print(cheatsheet)
    print("="*60)

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    while True:
        banner()
        print("1. Pengecek IP / Domain Target")
        print("2. Web Exploitation (Cookie/Parameter Brute Force)")
        print("3. Cryptography (Base64, Custom Caesar/ROT, Hashing)")
        print("4. Tampilkan Semua Command Linux Berguna (Cheat Sheet)")
        print("5. Keluar")
        
        pilihan = input("\nPilih opsi (1-5): ").strip()
        
        if pilihan == "1":
            menu_ip_checker()
        elif pilihan == "2":
            menu_web_exploit()
        elif pilihan == "3":
            menu_crypto()
        elif pilihan == "4":
            menu_linux_commands()
        elif pilihan == "5":
            print(f"[*] Keluar dari program. Dibuat oleh @gnadjaaa_. Semoga sukses CTF-nya!")
            sys.exit(0)
        else:
            print("[-] Pilihan tidak valid.")
            
        input("\nTekan Enter untuk kembali ke menu utama...")
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()