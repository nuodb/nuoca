import os
import re

from setuptools import setup, find_packages

readme = os.path.join(os.path.dirname(__file__), 'README.rst')

setup(
    name="pynuoca", # Replace with your own username
    version="20.0.3",
    author="NuoDB",
    author_email="support@nuodb.com",
    description="NuoDB Collection Agent (NuoCA)",
    long_description=open(readme).read(),
    url="https://github.com/nuodb/nuoca",
    license='MIT',
    keywords='nuodb scalable cloud database',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "tests/*"]),
    include_package_data=True,
    install_requires=[
        'aenum>=2.0.8',
        'click>=6.7',
        'elasticsearch>=5.0.0,<6.0.0',
        'python-dateutil>=2.6.1',
        'PyPubSub>=3.3.0',
        'PyYaml>=3.12',
        'requests>=2.21.0',
        'wrapt>=1.10.11',
        'Yapsy>=1.11.223',
        'kafka-python>=1.4.1',
        'pynuoadmin>=1.0.0',
        'pynuodb>=2.3.2',
    ],
    scripts=['bin/nuoca',
    ],
    data_files=[
        ('etc', ['etc/nuoca_setup.sh', 'etc/nuoca_export.sh', 'etc/nuoca_env.sh',
                 'etc/nuoca_settings.yml', 'etc/nuoca.yml']),
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        'Topic :: Database :: Front-Ends',
    ],
)
