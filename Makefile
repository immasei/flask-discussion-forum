.PHONY: build
.PHONY: clean
.PHONY: init
.PHONY: install
.PHONY: venv

build: 
	python3 app.py

clean:
	rm -rf database
	rm -rf __pycache__

venv:
	rm -rf venv


	
	

