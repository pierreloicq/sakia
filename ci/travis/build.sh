#!/usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

cd $HOME/build/duniter/sakia

pyenv shell $PYENV_PYTHON_VERSION
pyenv activate sakia-env
pip install coveralls
pip install pyinstaller
pip install -r requirements.txt
if [ $TRAVIS_OS_NAME == "linux" ]
then
    pip install -U git+https://github.com/posborne/dbus-python.git
    pip install notify2

    export PATH=/tmp/qt/5.5/5.5/gcc_64/bin:$PATH
fi

python gen_resources.py
python gen_translations.py --lrelease

if [ $TRAVIS_OS_NAME == "osx" ]
then
    pyinstaller sakia.spec
    cp -rv dist/sakia/* dist/sakia.app/Contents/MacOS
    rm -rfv dist/sakia
elif [ $TRAVIS_OS_NAME == "linux" ]
then
    pyinstaller sakia.spec
fi

