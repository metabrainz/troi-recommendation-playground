# troi-recommendation-playground

A recommendation engine playground that should hopefully make playing with music recommendations easy.

## installation


**Linux and Mac**
```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -r requirements.txt
```

**Windows**
```
virtualenv -p python3 .ve
.ve\Scripts\activate.bat
pip3 install -r requirements.txt
```

## sample use

**Linux**
```
./recommended_recordings.py <user name>
open OpenPost.html
```

**Windows**
```
python recommended_recordings.py <user name>
OpenPost.html
```
