
from setuptools import setup, find_packages

with open("requirements.txt", "r") as fh:
    requirements = fh.read()

setup(
    name='gridworld',
    version='0.1',
    description='',
    long_description='',
    long_description_content_type="text/markdown",
    url='https://github.com/artemZholus/gridworld',
    author='Artem Zholus',
    author_email='artem.zholus@gmail.com',
    include_package_data=True,
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=requirements,
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)