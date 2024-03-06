python3.11 -m venv kpenv
source kpenv/bin/activate
pip install -r requirements.txt --find-links https://download.pytorch.org/whl/nightly/cpu/torch_nightly.html
python setup.py install
