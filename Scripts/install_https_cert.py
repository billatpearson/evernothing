"""
install_https_cert.py — Generate a valid localhost HTTPS certificate for EverNothing.

Fixes the "NET::ERR_CERT_COMMON_NAME_INVALID" / "not valid" warnings by
creating a self-signed certificate with proper Subject Alternative Name
(SAN) fields covering every address you'd hit it from:

    - localhost
    - 127.0.0.1
    - ::1
    - the machine's hostname
    - every non-loopback IPv4 on this host (LAN access from phones etc.)

Writes:
    Startup/cert.pem
    Startup/key.pem

Usage:
    python Scripts/install_https_cert.py                # generate + write files
    python Scripts/install_https_cert.py --trust        # also install to
                                                        # Windows Trusted Root
                                                        # (requires admin elevation)
    python Scripts/install_https_cert.py --days 825     # shorter validity
    python Scripts/install_https_cert.py --force        # overwrite existing

After generating, restart the server with Startup\\test_and_restart.bat.
"""
import argparse
import datetime
import ipaddress
import os
import socket
import subprocess
import sys

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
except ImportError:
    print("ERROR: 'cryptography' is not installed. Run: pip install cryptography")
    sys.exit(1)


_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
CERT_PATH = os.path.join(_ROOT, 'Startup', 'cert.pem')
KEY_PATH  = os.path.join(_ROOT, 'Startup', 'key.pem')


def local_ip_addresses():
    """Return every non-loopback IPv4 address on this host."""
    ips = set()
    hostname = socket.gethostname()
    try:
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ':' in ip:
                continue  # skip IPv6 for now (::1 is added explicitly)
            if ip.startswith('127.'):
                continue
            ips.add(ip)
    except socket.gaierror:
        pass
    # Fallback: open a dummy UDP socket to discover the default route IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(('8.8.8.8', 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(ips)


def build_san(extra_hosts):
    hostname = socket.gethostname()
    dns_names = {'localhost', hostname, hostname + '.local'}
    for h in extra_hosts:
        dns_names.add(h)

    ip_addresses = {
        ipaddress.ip_address('127.0.0.1'),
        ipaddress.ip_address('::1'),
    }
    for ip in local_ip_addresses():
        try:
            ip_addresses.add(ipaddress.ip_address(ip))
        except ValueError:
            pass

    entries = [x509.DNSName(d) for d in sorted(dns_names)]
    entries += [x509.IPAddress(ip) for ip in sorted(ip_addresses, key=str)]
    return x509.SubjectAlternativeName(entries), dns_names, ip_addresses


def generate(days, extra_hosts):
    print(f"Generating RSA 4096-bit key...")
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

    san, dns_names, ip_addresses = build_san(extra_hosts)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME,         u'EverNothing Local Dev'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME,   u'EverNothing'),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Local Development'),
    ])

    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=days))
        .add_extension(san, critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=True, data_encipherment=False,
                key_agreement=False, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    return key, cert, dns_names, ip_addresses


def write_files(key, cert, force):
    for path in (CERT_PATH, KEY_PATH):
        if os.path.exists(path) and not force:
            print(f"ERROR: {path} already exists. Re-run with --force to overwrite.")
            sys.exit(2)

    os.makedirs(os.path.dirname(CERT_PATH), exist_ok=True)
    with open(CERT_PATH, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(KEY_PATH, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    # Tighten key file permissions on Windows via icacls when available
    if sys.platform == 'win32':
        try:
            user = os.environ.get('USERNAME', '')
            subprocess.run(
                ['icacls', KEY_PATH, '/inheritance:r', '/grant:r', f'{user}:F'],
                capture_output=True, check=False,
            )
        except FileNotFoundError:
            pass


def install_trust_windows(cert):
    """Install the cert into Windows Trusted Root (requires admin)."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.crt', delete=False) as tf:
        tf.write(cert.public_bytes(serialization.Encoding.PEM))
        crt_path = tf.name
    try:
        # LocalMachine\Root requires admin. CurrentUser\Root does not but
        # only trusts for this user. We try CurrentUser first — good enough
        # for a dev box and does not need elevation.
        print("Installing cert into CurrentUser\\Root (browser trust store)...")
        r = subprocess.run(
            ['certutil', '-user', '-addstore', 'Root', crt_path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(r.stdout); print(r.stderr, file=sys.stderr)
            print("WARNING: certutil failed. Install manually via MMC or accept the warning in-browser.")
        else:
            print("Cert installed. Restart your browser so it picks up the new trust anchor.")
    finally:
        try: os.unlink(crt_path)
        except OSError: pass


def main():
    ap = argparse.ArgumentParser(description='Generate a valid HTTPS cert for EverNothing.')
    ap.add_argument('--days',  type=int, default=825, help='Validity in days (default 825 — Chrome max).')
    ap.add_argument('--force', action='store_true', help='Overwrite existing cert/key.')
    ap.add_argument('--trust', action='store_true', help='Install to Windows trust store (CurrentUser\\Root).')
    ap.add_argument('--host',  action='append', default=[], help='Extra hostname for SAN (repeatable).')
    args = ap.parse_args()

    key, cert, dns_names, ip_addresses = generate(args.days, args.host)
    write_files(key, cert, force=args.force)

    fp = cert.fingerprint(hashes.SHA256()).hex(':').upper()
    print()
    print(f"Cert written: {CERT_PATH}")
    print(f"Key written:  {KEY_PATH}")
    print(f"Valid until:  {cert.not_valid_after.isoformat()}Z")
    print(f"SHA-256:      {fp}")
    print()
    print("SAN entries:")
    for d in sorted(dns_names):       print(f"  DNS: {d}")
    for ip in sorted(ip_addresses, key=str):
        print(f"  IP:  {ip}")

    if args.trust:
        if sys.platform != 'win32':
            print("\n--trust is only implemented for Windows.")
        else:
            install_trust_windows(cert)
    else:
        print()
        print("To have the browser accept the cert without warnings, re-run with --trust.")
        print("Otherwise accept the self-signed warning once per browser profile.")

    print()
    print("Next step: restart the server with   Startup\\test_and_restart.bat")


if __name__ == '__main__':
    main()
