# usage
run the following code.
```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mkdir work
cd work
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix/binding/python

sudo apt-get update && sudo apt-get install python3-dev python3-pillow -y
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)

cd ../../../../
sudo python main.py
```