from setuptools import setup
import os
import sys

v = sys.version_info
if v[0] == 2 and v[1] == 7:
    scripts = []
    data_files = []
    files = {}
    for d in ['lib', 'tests']:
      for root, dirs, filenames in os.walk(d):
        for dir in dirs:
          if os.path.join(root, dir) not in files:
            files[os.path.join(root, dir)] = []
        for f in filenames:
          fullpath = os.path.join(root, f)
          dirname = os.path.dirname(fullpath)
          if dirname not in files:
            files[dirname] = []
          files[dirname].append(fullpath)
    for directory in sorted(files.keys()):
      data_files.append((directory, files[directory]))
    for root, dirs, filenames in os.walk("bin"):
      for filename in filenames:
        scripts.append(os.path.join("bin", filename))
    setup(name='nuoca',
          version='1.0.0',
          description='NuoDB Collection Agent',
          url='http://TBD',
          author='The Product Experience Team',
          author_email='prex-support@nuodb.com',
          data_files=data_files,
          install_requires=["argparse",
                            "click",
                            "elasticsearch>=5.0.0,<6.0.0",
                            "pyyaml"
                            ],
          dependency_links=[],
          license='TBD',
          packages=['nuoca'],
          scripts=scripts,
          zip_safe=False,
          entry_points={
              'console_scripts': [
                  'nuoca = nuoca.main'
              ]
          },
          )
else:
    print "ERROR: You must be running python 2.7"
    sys.exit(2)
