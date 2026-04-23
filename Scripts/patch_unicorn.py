# Unicorn SVG (twemoji-style, public domain)
UNICORN = '<img class="unicorn-img" src="https://twemoji.maxcdn.com/v/latest/svg/1f984.svg" alt="🦄">'
SPARKLE = '<img class="sparkle-img" src="https://twemoji.maxcdn.com/v/latest/svg/2728.svg" alt="✨">'
PAGE_UNICORN = '<img class="page-unicorn" src="https://twemoji.maxcdn.com/v/latest/svg/1f984.svg" alt="🦄">'

content = open('evernothing.py', encoding='utf-8').read()

# Nav brand spans
content = content.replace(
    '<span class="nav-brand">&#9670; EverNothing</span>',
    f'<span class="nav-brand">{UNICORN} EverNothing {SPARKLE}</span>'
)
content = content.replace(
    '<span class="nav-brand">&#9670; Admin</span>',
    f'<span class="nav-brand">{UNICORN} Admin {SPARKLE}</span>'
)

# Centered card headings (login/register/forgot/reset pages)
content = content.replace(
    '<h2 style="text-align:center;margin-block-end:4px">&#9670; EverNothing</h2>',
    f'<h2 style="text-align:center;margin-block-end:4px">{PAGE_UNICORN}EverNothing</h2>'
)
content = content.replace(
    '<h2 style="text-align:center;margin-block-end:4px">&#9670; Admin</h2>',
    f'<h2 style="text-align:center;margin-block-end:4px">{PAGE_UNICORN}Admin</h2>'
)
content = content.replace(
    '<h2 style="text-align:center;margin-block-end:20px">&#9670; Reset Password</h2>',
    f'<h2 style="text-align:center;margin-block-end:20px">{PAGE_UNICORN}Reset Password</h2>'
)

open('evernothing.py', 'w', encoding='utf-8').write(content)

# Count replacements
print('unicorn-img:', content.count('unicorn-img'))
print('sparkle-img:', content.count('sparkle-img'))
print('page-unicorn:', content.count('page-unicorn'))
