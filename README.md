# troi-recommendation-playground

A recommendation engine playground that should hopefully make playing with music recommendations easy.

## installation


**Linux and Mac**
```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -r requirements.txt
```

If you plan to do local development or run tests, you'll need to:

```
pip3 install -e .
```

**Windows**

```
virtualenv -p python3 .ve
.ve\Scripts\activate.bat
pip3 install -r requirements.txt
```

**Docker**

On non Linux operating systems installing python modules can be a bit of a pain. For that a thin-shell docker
container can be created. Note that docker is not required, but helpful if you're not on Linux.

To use this container, you first need to build the container and start it:

```
./run-docker.sh build
./run-docker.sh up
```

Now you can run any of the scripts via run-docker.sh:

```
./run-docker.sh recommend_recordings.py rob similar
```

When you are done with the container, take it down with:

```
./run-docker.sh up
```

To run tests:

```
./run-docker.sh test
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

**Docker**

If you installed the system via docker, you can run scripts via:

```
./run-docker.sh recommend_recordings.py rob similar
open OpenPost.html
```
