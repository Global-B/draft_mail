from setuptools import setup, find_packages

setup(
    name='draft-mail',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    description='A Django package that provides a graph api to send draft emails',
    long_description=open('README.md').read(),
    author='Felix Guzman',
    author_email='felixg@clickping.do',
    url='https://github.com/Global-B/draft_mail',
    install_requires=[
        'azure-identity>=1.17.1',
        'msgraph-sdk>=1.5.4',
        'typing-extensions>4.12.0',
        'httpx>=0.27.0',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
