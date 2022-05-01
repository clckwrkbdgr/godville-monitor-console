import setuptools
import re, subprocess
version = '.'.join(sorted([
		m.group(1).split('.')
		for m in
		(re.match(r'^.*(\d+[.]\d+[.]\d+)$', line) for line in subprocess.check_output(['git', 'tag']).decode().splitlines())
		if m
		])[-1])
setuptools.setup(
		name='godvill-monitor-console',
		version=version,
		packages=[ # TODO package data: auth.cfg, pygod.ini, translations to share/, example rules.py
			'pygod',
			'pygod.engine',
			'pygod.core',
			'pygod.status_processing',
			'pygod.windows',
			],
		entry_points={
			"console_scripts" : [
				'pygod = pygod.pygod:main',
				]
			},
		)

