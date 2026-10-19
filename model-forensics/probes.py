"""Deterministic public probe panel. No model-written questions or benchmark inputs."""
import random


def build(seed=4101):
    rng = random.Random(seed)
    rows = []

    def add(family, split, kind, text, **extra):
        rows.append(dict(id=f"{family}-{sum(p['family'] == family for p in rows):02}",
                         family=family, split=split, kind=kind, prompt=text, **extra))

    choices = [
        ('number', 'explore', 'Choose one number', ['17', '23', '41', '68']),
        ('letter', 'holdout', 'Choose one letter', ['A', 'K', 'M', 'Z']),
        ('color', 'explore', 'Choose one color', ['red', 'blue', 'green', 'yellow']),
        ('shape', 'holdout', 'Choose one shape', ['circle', 'square', 'triangle', 'oval']),
        ('portuguese', 'explore', 'Escolha uma palavra', ['rio', 'mar', 'sol', 'lua']),
        ('spanish', 'holdout', 'Elige una palabra', ['nube', 'lago', 'flor', 'hoja']),
    ]
    for family, split, instruction, options in choices:
        for _ in range(3):
            order = rng.sample(options, len(options))
            add(family, split, 'choice', f"{instruction}: {', '.join(order)}. "
                'Return exactly one listed item, with no punctuation.', options=options)

    for i in range(6):
        a, b, c = rng.randint(11, 39), rng.randint(3, 9), rng.randint(2, 8)
        add('arithmetic', 'explore', 'exact',
            f'Return only the integer: ({a} * {b} + {c}) modulo 13.', expected=str((a*b+c) % 13))
        word = ''.join(rng.choice('aabccdde') for _ in range(19))
        add('character-count', 'holdout', 'exact',
            f'Count lowercase c characters in this string. Return only the integer: {word}', expected=str(word.count('c')))
        nums = rng.sample(range(10, 100), 6)
        add('list-index', 'explore', 'exact',
            f'Use zero-based indexing. Return only element 3 of {nums}.', expected=str(nums[3]))
        bits = ''.join(rng.choice('01') for _ in range(9))
        add('binary', 'holdout', 'exact',
            f'Convert binary {bits} to decimal. Return only the integer.', expected=str(int(bits, 2)))

    for family, split, strings in [
        ('unicode-copy', 'explore', ['é e\u0301', 'ＡAΑА', '👩\u200d💻🧑\u200d🔬', '零〇0O']),
        ('syntax-copy', 'holdout', ['a\\b\\n', '[]{}()<>', 'foo::bar->baz', '00_01__10']),
    ]:
        for s in strings:
            add(family, split, 'exact', f'Copy the text between START and END exactly. '
                f'Do not include the delimiters. START{s}END', expected=s)

    # Each family has a base and doubled string. Differences remove a constant template offset.
    for family, split, s in [
        ('tokens-ascii', 'explore', 'antidisestablishmentarianism 0123456789 '),
        ('tokens-cjk', 'holdout', '漢字かなカナ 中文测试 '),
        ('tokens-code', 'explore', 'fn main(){let x=0xdead_beef;}\n'),
        ('tokens-arabic', 'holdout', 'مرحبا بالعالم '),
        ('tokens-spaces', 'explore', ' a  b\t c\n'),
        ('tokens-emoji', 'holdout', '👩\u200d💻 🏳️\u200d🌈 👍🏽 '),
    ]:
        for multiplier in (1, 2):
            add(family, split, 'tokens', s * multiplier, multiplier=multiplier)
    return rows
