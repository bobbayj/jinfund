from setuptools import setup, find_packages

setup(
    name='jinfund',
    version='0.1',
    packages=find_packages(),

    # Dependencies
    install_requires=['yfinance>=0.1.50'],

    # Metadata for PyPI
    author='Bob Jin',
    author_email='automaticjinandtonic@gmail.com',
    description='Track your ETF exposures',
    keywords='finance tax fintech etf portfolio management',
    url='https://github.com/bobbayj/jinfund',
    license='GNU GENERAL PUBLIC LICENSE V3.0',
    long_description=open('README.md').read(),
)