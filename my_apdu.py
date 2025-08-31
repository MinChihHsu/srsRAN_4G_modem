#!/usr/bin/env python3
import socket
import json
import subprocess
import threading
import queue
import time
import re
import os

SOCK = "/tmp/aka_proxy.sock"


class ModemProxy:
    def __init__(self):
        self.q = queue.Queue()

        # Writer: su shell (專門用來送 echo 指令)
        self.writer = subprocess.Popen(
            ["adb", "shell", "su"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        # Reader: tail -f /dev/umts_router
        self.reader = subprocess.Popen(
            ["adb", "shell", "su", "-c", "tail -f /dev/umts_router"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        # Reader thread
        self.thread = threading.Thread(target=self._reader_thread, daemon=True)
        self.thread.start()

    def _reader_thread(self):
        for line in self.reader.stdout:
            line = line.strip()
            if line:
                print("<<", line)  # debug
                self.q.put(line)

    def send_raw(self, cmd: str):
        """把指令送到 writer shell"""
        print(">>", cmd)
        self.writer.stdin.write(cmd + "\n")
        self.writer.stdin.flush()

    def send_apdu(self, apdu_hex: str, timeout=2.0):
        # 清空 queue
        while not self.q.empty():
            self.q.get_nowait()

        self.send_raw("echo -e 'AT+CSUS=2\\r' > /dev/umts_router")

        # 1. SELECT MF
        #self.send_raw("echo -e 'AT+CSIM=7,\"00A40004023F00\"\\r' > /dev/umts_router")
        self.send_raw("echo -e 'AT+CSIM=12,\"00A4040007A0000000871002\"\\r' > /dev/umts_router")
        #time.sleep(0.2)

        # 2. SELECT ADF USIM
        #self.send_raw("echo -e 'AT+CSIM=21,\"00A4040410A0000000871002FF49FFFF89040B00FF\"\\r' > /dev/umts_router")
        #self.send_raw("echo -e 'AT+CSIM=21,\"00A4040410A0000000871002FF33FF018900000100\"\\r' > /dev/umts_router")
        #time.sleep(0.2)

        # 3. AUTHENTICATE
        self.send_raw(f"echo -e 'AT+CSIM=39,\"{apdu_hex}\"\\r' > /dev/umts_router")

        # 4. Flush (AT)
        #time.sleep(0.5)
        self.send_raw("echo -e 'AT\\r' > /dev/umts_router")

        # 收集回應
        lines = []
        csim_count = 0
        csim_resp = None
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                line = self.q.get(timeout=0.2)
                lines.append(line)
                if line.startswith("+CSIM: 110,"):
                    csim_resp = line
                    break
                    #csim_count += 1
                    #print(f"found csim #{csim_count}")
                    #if csim_count == 3:   # 第三個就是 AUTH
                        #csim_resp = line
                #if "OK" in line or "ERROR" in line:
                    #break
            except queue.Empty:
                pass

        if not csim_resp:
            raise RuntimeError(f"No +CSIM AUTH response. Got: {lines}")

        m = re.search(r'"([0-9A-Fa-f]+)"', csim_resp)
        if m:
            return bytes.fromhex(m.group(1))
        else:
            raise RuntimeError(f"Parse failed: {csim_resp}")


def build_authenticate_apdu(rand: bytes, autn: bytes) -> bytes:
    if len(rand) != 16 or len(autn) != 16:
        raise ValueError("RAND/AUTN must be 16 bytes each")
    data = bytearray([0x10]) + rand + bytearray([0x10]) + autn
    return bytes([0x00, 0x88, 0x00, 0x81, len(data)]) + data


def parse_authenticate_resp(resp: bytes):
    """
    支援兩種常見編碼：
    A) DB-容器：DB | L | [ RES_len | RES | CK_len | CK | IK_len | IK ]
       (可選) E0 | L | AUTS
    B) TLV：   DB|L|RES   DC|L|CK   DD|L|IK   (可選) E0|L|AUTS
    """
    res = b""
    ck  = b""
    ik  = b""
    auts = b""

    print("Get authenticate resp --------")

    i = 0
    n = len(resp)
    print(i, n)
    while i + 1 < n:
        print(i)
        tag = resp[i]
        L   = resp[i+1]
        res   = resp[i+2:i+2+L]
        print(f"tag={tag:02X} L={L:02X} res={res.hex()}")
        print("tag int = ", int(tag))
        print("tag type = ", type(tag))
        print("compare: ", (tag == 0xDB))
        if tag == 0xDB:
            print("I entered")
            # 嘗試解析「DB-容器」格式：連續三段 LV
            j = i+2+L
            print(j)
            cklen = resp[j]; j += 1
            print(cklen)
            ck   = resp[j:j+cklen]; j += cklen
            iklen = resp[j]; j += 1
            ik   = resp[j:j+iklen]; j += iklen
            
            break
        elif tag == 0xDC:
            ck = bytes(v)
        elif tag == 0xDD:
            ik = bytes(v)
        elif tag == 0xE0:
            auts = bytes(v)

        # 移動到下一個 DO
        i += 2 + L

    return res, ck, ik, auts

def handle_req(modem: ModemProxy, data: str) -> str:
    req  = json.loads(data)
    rand = bytes(req["rand"])
    autn = bytes(req["autn"])

    print("received rand/autn:", rand.hex(), autn.hex())

    apdu = build_authenticate_apdu(rand, autn)
    raw  = modem.send_apdu(apdu.hex().upper())

    res_b, ck_b, ik_b, auts_b = parse_authenticate_resp(raw)

    print("res: ", res_b.hex())
    print("ck: ", ck_b.hex())
    print("ik: ", ik_b.hex())
    print("auts: ", auts_b.hex())

    reply = {
        "res":  list(res_b),
        "ck":   list(ck_b),
        "ik":   list(ik_b),
        "auts": list(auts_b),
    }
    return json.dumps(reply) + "\n"

def main():
    if os.path.exists(SOCK):
        os.unlink(SOCK)

    modem = ModemProxy()
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(SOCK)
    s.listen(5)
    print(f"aka modem proxy listening on {SOCK}")

    while True:
        conn, _ = s.accept()
        try:
            data = conn.recv(4096).decode()
            reply = handle_req(modem, data)
            try:
                conn.send(reply.encode())
            except BrokenPipeError:
                print("Client disconnected early")
        except Exception as e:
            try:
                conn.send((json.dumps({"error": str(e)}) + "\n").encode())
            except:
                pass
        finally:
            conn.close()


if __name__ == "__main__":
    main()

