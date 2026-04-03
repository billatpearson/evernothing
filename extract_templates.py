content = open('evernothing.py', encoding='utf-8').read()
start = content.find('STYLE = ')
end   = content.find('# --- JSON API')
block = content[start:end].rstrip()

out = '"""evernothing_templates.py — User Experience\nSTYLE constant and all T_* HTML template strings.\n"""\n' + block + '\n'
open('evernothing_templates.py', 'w', encoding='utf-8').write(out)
print('Written', len(out), 'chars')
