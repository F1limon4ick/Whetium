from pathlib import Path

path = Path('main.py')
text = path.read_text(encoding='utf-8')
replacement_char = chr(0xfffd)
text = text.replace(replacement_char, '📝', 1)
text = text.replace(replacement_char + '💰', '💰', 1)
path.write_text(text, encoding='utf-8')
print('updated')
