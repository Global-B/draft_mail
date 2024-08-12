from setuptools import setup, find_packages

setup(
    name='django-insurance-draft-mail',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    description='A Django package that provides a graph api to send draft emails',
    long_description=open('README.md').read(),
    author='Felix Guzman',
    author_email='felixg@clickping.do',
    url='https://github.com/Global-B/django_insurance_draft_mail',
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
