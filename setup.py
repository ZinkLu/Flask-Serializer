# -*- coding: utf-8 -*-


from setuptools import setup

setup(
    name='flask_serializer',  # How you named your package folder (MyLib)
    packages=["flask_serializer", "flask_serializer.utils", "flask_serializer.mixins", "flask_serializer.func_field",
              "flask_serializer.cache_object"],
    version='0.0.5.1',  # Start with a small number and increase it with every change you make
    license='MIT',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description="A Flask serializer built with marshmallow and flask-sqlalchemy",
    long_description_content_type='text/markdown',
    # Give a short description about your library
    author='ZinkLu',  # Type in your name
    author_email='zinkworld@live.cn',  # Type in your E-Mail
    url='https://github.com/ZinkLu',  # Provide either the link to your github or to your website
    download_url='https://github.com/ZinkLu/Flask-Serializer/archive/v0.0.5.tar.gz',  # I explain this later on
    keywords=['Flask', 'extension', 'serializer', "marshmallow", "flask-sqlalchemy"],
    # Keywords that define your package best
    install_requires=[  # I get to this in a second
        "sqlalchemy",
        "marshmallow",
        "Flask",
        "Flask-sqlalchemy",
        "six",
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],

)
