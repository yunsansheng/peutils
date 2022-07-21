# peutils
pe utils


## jenkins
```
sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
apk add python3
apk add zip
apk add vim 
# 安装pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py



#apk add python3-dev
#apk add libffi-dev
# python3 -m pip install twine -i https://pypi.douban.com/simple
# vi .pypirc
########
#[distutils]
#index-servers = pypi
#
#[pypi]
#username:__token__
#password:pypi-xxx
######
###############pypi##############
#python --version
#echo $(pwd)

python3 setup.py sdist
python3 -m twine upload dist/*

```

