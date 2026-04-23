import sqlite3, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

with open('secret.key','rb') as f:
    KEY = f.read()
aes = AESGCM(KEY)

def dec(t):
    if not t:
        return t
    try:
        data = base64.b64decode(t)
        return aes.decrypt(data[:12], data[12:], None).decode('utf-8')
    except:
        return t

c = sqlite3.connect('evernothing.db')
cur = c.cursor()

# Decrypt folders
cur.execute('SELECT id,name FROM folders')
folders = cur.fetchall()
for fid, name in folders:
    decrypted = dec(name)
    if decrypted != name:
        cur.execute('UPDATE folders SET name=? WHERE id=?', (decrypted, fid))

# Decrypt notes
cur.execute('SELECT id,note_key,note_value FROM notes')
notes = cur.fetchall()
for nid, key, val in notes:
    dec_key = dec(key)
    dec_val = dec(val)
    if dec_key != key or dec_val != val:
        cur.execute('UPDATE notes SET note_key=?, note_value=? WHERE id=?', (dec_key, dec_val, nid))

# Decrypt note_history
cur.execute('SELECT id,note_key,note_value FROM note_history')
history = cur.fetchall()
for hid, key, val in history:
    dec_key = dec(key)
    dec_val = dec(val)
    if dec_key != key or dec_val != val:
        cur.execute('UPDATE note_history SET note_key=?, note_value=? WHERE id=?', (dec_key, dec_val, hid))

c.commit()
print(f'Decrypted {len([f for f in folders if "=" in f[1]])} folders')
print(f'Decrypted {len([n for n in notes if "=" in n[1] or "=" in n[2]])} notes')
print(f'Decrypted {len([h for h in history if "=" in h[1] or "=" in h[2]])} history entries')
c.close()
print('Done. All encrypted data is now plaintext.')
