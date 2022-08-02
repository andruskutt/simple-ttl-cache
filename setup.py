"""Setup script."""

import os

from setuptools import setup


with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name='simple_ttl_cache',
    version='0.0.1',
    description='TTL cache',
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='caching',
    author='Andrus Kütt',
    author_email='andrus.kuett@gmail.com',
    url='https://github.com/andruskutt/simple-ttl-cache',
    license='MIT',
    py_modules=['simple_ttl_cache'],
    python_requires='>=3.7',
)
