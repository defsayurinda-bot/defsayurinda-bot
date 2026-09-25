"""Perbarui bagian otomatis README profil dari isi repo situs defsayurinda.github.io.

Bagian yang ditulis ulang ada di antara penanda:
  <!-- ALAT:MULAI -->      ... <!-- ALAT:SELESAI -->       tabel alat dari registri konten/alat.json
  <!-- CATATAN:MULAI -->   ... <!-- CATATAN:SELESAI -->    catatan belajar (konten/catatan), terbaru di atas
  <!-- AKTIVITAS:MULAI --> ... <!-- AKTIVITAS:SELESAI -->  commit terbaru di main

Hanya memakai pustaka bawaan Python. Token GITHUB_TOKEN dipakai bila ada (batas permintaan
lebih longgar); repo sumbernya public, jadi skrip juga jalan tanpa token.

Jalankan dari akar repo profil:  python3 .github/scripts/perbarui_readme.py
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

PEMILIK, REPO = "defsayurinda", "defsayurinda.github.io"
API = f"https://api.github.com/repos/{PEMILIK}/{REPO}"
SITUS = f"https://{PEMILIK}.github.io/"
BULAN = "Jan Feb Mar Apr Mei Jun Jul Agu Sep Okt Nov Des".split()
README = Path(__file__).resolve().parents[2] / "README.md"


def ambil(url, json_=True):
    kepala = {"User-Agent": "perbarui-readme-profil"}
    if json_:
        kepala["Accept"] = "application/vnd.github+json"
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        kepala["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=kepala), timeout=30) as r:
        isi = r.read().decode("utf-8")
    return json.loads(isi) if json_ else isi


def tanggal(iso):
    d = datetime.strptime(iso[:10], "%Y-%m-%d")
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


STATUS = {"asli": "Sumber asli", "sekunder": "Sumber sekunder", "belum": "Belum terverifikasi"}


def bagian_alat():
    """Tabel alat dari registri konten/alat.json di repo situs."""
    reg = json.loads(ambil(f"https://raw.githubusercontent.com/{PEMILIK}/{REPO}/main/konten/alat.json", json_=False))
    baris = [f"| [{a['judul_pendek']}]({SITUS}{a['halaman']}) | {a['deskripsi']} | {STATUS.get(a['status'], a['status'])} |"
             for a in reg["alat"]]
    return "| Alat | Isi | Status sumber |\n|---|---|---|\n" + "\n".join(baris)


def bagian_catatan():
    berkas = sorted((f for f in ambil(f"{API}/contents/konten/catatan") if f["name"].endswith(".md")),
                    key=lambda f: f["name"], reverse=True)
    baris = []
    for f in berkas:
        judul_md = ambil(f["download_url"], json_=False).splitlines()[0].lstrip("# ").strip()
        nomor, _, judul = judul_md.partition(" — ")
        baris.append(f"- **{nomor}** · [{judul or judul_md}]({SITUS}catatan/{f['name'].removesuffix('.md')}/)")
    return "\n".join(baris)


def bagian_aktivitas(jumlah=5):
    baris = []
    for c in ambil(f"{API}/commits?sha=main&per_page=30"):
        pesan = c["commit"]["message"].splitlines()[0]
        if pesan.startswith("Merge "):
            continue
        baris.append(f"- {tanggal(c['commit']['author']['date'])} · [{pesan}]({c['html_url']})")
        if len(baris) == jumlah:
            break
    return "\n".join(baris)


def ganti(teks, nama, isi):
    pola = re.compile(rf"(<!-- {nama}:MULAI -->)(.*?)(<!-- {nama}:SELESAI -->)", re.S)
    if not pola.search(teks):
        sys.exit(f"Penanda {nama} tidak ditemukan di README.md")
    return pola.sub(lambda m: f"{m.group(1)}\n{isi}\n{m.group(3)}", teks)


def main():
    lama = README.read_text(encoding="utf-8")
    baru = lama
    for nama, fungsi in (("ALAT", bagian_alat), ("CATATAN", bagian_catatan), ("AKTIVITAS", bagian_aktivitas)):
        baru = ganti(baru, nama, fungsi())
    if baru == lama:
        print("README sudah terbaru.")
        return
    README.write_text(baru, encoding="utf-8")
    print("README diperbarui.")


if __name__ == "__main__":
    main()
