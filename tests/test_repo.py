import os
import re
import subprocess
import unittest

ROOT = os.path.join(os.path.dirname(__file__), '..')
SKILLS = os.path.join(ROOT, 'skills')


def tracked_files():
    out = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [os.path.join(ROOT, f) for f in out.split()]


def frontmatter(path):
    text = open(path).read()
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    return dict(line.split(': ', 1) for line in m.group(1).splitlines()) if m else {}


class RepoTest(unittest.TestCase):
    def test_no_dollar_figures(self):
        for f in tracked_files():
            if f.endswith(('.md', '.json', '.py', '.sh', 'LICENSE')):
                for n, line in enumerate(open(f, errors='ignore'), 1):
                    self.assertIsNone(re.search(r'\$\s?\d', line), f'{f}:{n} has a dollar figure: {line.strip()}')

    def test_skill_frontmatter(self):
        names = sorted(os.listdir(SKILLS))
        self.assertEqual(len(names), 7)
        for name in names:
            fm = frontmatter(os.path.join(SKILLS, name, 'SKILL.md'))
            self.assertEqual(fm.get('name'), name)
            self.assertTrue(fm.get('description', '').startswith('Use when'), name)
            self.assertLess(len(fm['description']), 300, name)

    def test_skill_length(self):
        for name in os.listdir(SKILLS):
            words = len(open(os.path.join(SKILLS, name, 'SKILL.md')).read().split())
            self.assertLess(words, 500, f'{name} has {words} words')

    def test_readme_installs_and_lists_every_skill(self):
        readme = open(os.path.join(ROOT, 'README.md')).read()
        self.assertIn('/plugin install agent-team-skills --marketplace coracle-us/agent-team-skills', readme)
        for name in os.listdir(SKILLS):
            self.assertIn(f'`{name}`', readme)


if __name__ == '__main__':
    unittest.main()
