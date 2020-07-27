# -*- coding: utf-8 -*-


from distutils.core import setup

setup(
    name='Flask-Serializer',  # How you named your package folder (MyLib)
    version='0.0.1',  # Start with a small number and increase it with every change you make
    license='MIT',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description="A Flask serializer built with marshmallow and flask-sqlalchemy",
    # Give a short description about your library
    author='ZinkLu',  # Type in your name
    author_email='zinkworld@live.cn',  # Type in your E-Mail
    url='https://github.com/ZinkLu',  # Provide either the link to your github or to your website
    download_url='https://github.com/ZinkLu/Flask-Schema/archive/0.0.1.tar.gz',  # I explain this later on
    keywords=['Flask', 'extension', 'serializer', "marshmallow", "flask-sqlalchemy"],
    # Keywords that define your package best
    install_requires=[  # I get to this in a second
        "sqlalchemy",
        "marshmallow",
        "Flask",
        "Flask-sqlalchemy",
        "six",
    ],
)
