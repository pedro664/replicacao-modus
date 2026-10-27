"""Fase (a.1–a.3) para datasets em pcap: extrai, por pacote IPv4, os atributos do MODUS.

Lê só cabeçalhos (funciona com pcaps truncados): o tamanho do pacote é o orig_len do
registro pcap, ou seja, o tamanho original no fio.

  python src/pcap_to_npz.py data/ctu13/capture20110818-2.truncated.pcap data/ctu13/c11_packets.npz
"""

import struct
import sys

import numpy as np


def _pcap_records(f, gh):
    """Pcap clássico: gera (timestamp, orig_len, bytes capturados)."""
    magic = gh[:4]
    end = "<" if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1") else ">"
    nano = magic in (b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\x3c\x4d")
    gh += f.read(16)  # cabeçalho global tem 24 bytes; 8 já lidos
    if struct.unpack(end + "I", gh[20:24])[0] != 1:
        raise ValueError("linktype não suportado (esperado Ethernet)")
    rec = struct.Struct(end + "IIII")
    while (h := f.read(16)) and len(h) == 16:
        sec, frac, incl, orig = rec.unpack(h)
        yield sec + frac / (1e9 if nano else 1e6), orig, f.read(incl)


def _pcapng_records(f, gh):
    """Pcapng: lê blocos IDB (linktype/resolução) e EPB/SPB (pacotes)."""
    end = "<"
    tsres = {}
    first = True
    while True:
        h = gh if first else f.read(8)
        first = False
        if len(h) < 8:
            return
        btype, blen = struct.unpack(end + "II", h[:8])
        if btype == 0x0A0D0D0A:  # Section Header: define a ordem de bytes
            bom = f.read(4)
            end = "<" if bom == b"\x4d\x3c\x2b\x1a" else ">"
            blen = struct.unpack(end + "I", h[4:8])[0]
            f.read(blen - 12)
            tsres = {}
            continue
        body = f.read(blen - 8)[:-4]
        if btype == 1:  # Interface Description
            linktype = struct.unpack(end + "H", body[:2])[0]
            if linktype != 1:
                raise ValueError(f"linktype {linktype} não suportado (esperado Ethernet)")
            res, o = 1e-6, 8
            while o + 4 <= len(body):
                code, ln = struct.unpack(end + "HH", body[o:o + 4])
                if code == 0:
                    break
                if code == 9:  # if_tsresol
                    v = body[o + 4]
                    res = 2.0 ** -(v & 0x7F) if v & 0x80 else 10.0 ** -v
                o += 4 + ((ln + 3) & ~3)
            tsres[len(tsres)] = res
        elif btype == 6:  # Enhanced Packet
            iface, hi, lo, cap, orig = struct.unpack(end + "IIIII", body[:20])
            yield ((hi << 32) | lo) * tsres.get(iface, 1e-6), orig, body[20:20 + cap]
        elif btype == 3:  # Simple Packet (sem timestamp)
            orig = struct.unpack(end + "I", body[:4])[0]
            yield float("nan"), orig, body[4:]


ARP_PROTO, OTHER_PROTO = 256, 257  # códigos para quadros sem camada IP


def parse(path: str, all_frames: bool = False) -> dict:
    """Extrai atributos por pacote. all_frames=False mantém só IPv4 (CTU-13);
    True mantém também IPv6, ARP e outros quadros, com portas 0 (Edge-IIoT)."""
    with open(path, "rb") as f:
        gh = f.read(8)
        if gh[:4] == b"\x0a\x0d\x0d\x0a":
            records = _pcapng_records(f, gh)
        elif gh[:4] in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1", b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
            records = _pcap_records(f, gh)
        else:
            raise ValueError("formato desconhecido (nem pcap nem pcapng)")
        ts, sport, dport, length, proto, src, dst = [], [], [], [], [], [], []
        total = skipped = 0
        for t, orig, buf in records:
            total += 1
            off, etype = 14, int.from_bytes(buf[12:14], "big") if len(buf) >= 14 else 0
            while etype in (0x8100, 0x88A8) and len(buf) >= off + 4:  # VLAN
                etype = int.from_bytes(buf[off + 2:off + 4], "big")
                off += 4
            sp = dp = 0  # imputação de zeros na ausência de porta (como no artigo)
            s_ip = d_ip = 0
            if etype == 0x0800 and len(buf) >= off + 20:
                p = buf[off + 9]
                l4 = off + (buf[off] & 0x0F) * 4
                s_ip = int.from_bytes(buf[off + 12:off + 16], "big")
                d_ip = int.from_bytes(buf[off + 16:off + 20], "big")
            elif not all_frames:
                skipped += 1
                continue
            elif etype == 0x86DD and len(buf) >= off + 40:
                p, l4 = buf[off + 6], off + 40
            else:
                p, l4 = (ARP_PROTO if etype == 0x0806 else OTHER_PROTO), None
            if p in (6, 17) and l4 is not None and len(buf) >= l4 + 4:
                sp, dp = struct.unpack(">HH", buf[l4:l4 + 4])
            ts.append(t)
            sport.append(sp)
            dport.append(dp)
            length.append(orig)
            proto.append(p)
            src.append(s_ip)
            dst.append(d_ip)
    print(f"{total} pacotes no pcap; {total - skipped} mantidos; {skipped} descartados (não-IPv4)")
    return {"ts": np.array(ts), "sport": np.array(sport, np.uint16), "dport": np.array(dport, np.uint16),
            "length": np.array(length, np.uint32), "proto": np.array(proto, np.uint16),
            "src": np.array(src, np.uint32), "dst": np.array(dst, np.uint32)}


if __name__ == "__main__":
    # uso: pcap_to_npz.py entrada.pcap saida.npz [--all-frames]
    np.savez(sys.argv[2], **parse(sys.argv[1], all_frames="--all-frames" in sys.argv[3:]))
    print("salvo", sys.argv[2])
