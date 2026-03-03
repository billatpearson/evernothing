import sqlite3, base64, html
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

with open('secret.key','rb') as f:
    KEY = f.read()
aes = AESGCM(KEY)

c = sqlite3.connect('evernothing.db')
cur = c.cursor()

cur.execute('SELECT id,note_key FROM notes WHERE id=34')
r = cur.fetchone()
enc_key = html.unescape(r[1])
data = base64.b64decode(enc_key)
dec_key = aes.decrypt(data[:12], data[12:], None).decode('utf-8')

cur.execute('UPDATE notes SET note_key=? WHERE id=34', (dec_key,))
cur.execute('UPDATE note_history SET note_key=? WHERE note_id=34', (dec_key,))

c.commit()
print(f'Decrypted note 34 key to: {dec_key}')
c.close()
