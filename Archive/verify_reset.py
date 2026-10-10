#!/usr/bin/env python
import sqlite3
from werkzeug.security import check_password_hash

con = sqlite3.connect(r'DB\evernothing.db')
r = con.cursor().execute('SELECT password FROM users WHERE username="bspeiser"').fetchone()
print('Verify:', check_password_hash(r[0], 'Password123!'))
