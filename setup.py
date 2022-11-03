from setuptools import find_packages, setup


setup(
    name="fancyping",
    version="0.1.0",
    description="Colorful ICMP pings for your terminal",
    author="Torsten Rehn",
    author_email="torsten@rehn.email",
    url="https://github.com/trehn/fancyping",
    license="GPLv3",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            "fancyping=fancyping.cmdline:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console :: Curses",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: System :: Systems Administration",
    ],
    install_requires=[
        "icmplib",
    ],
)
