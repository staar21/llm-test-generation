![Docker Supported](https://img.shields.io/badge/Docker-supported-green?style=square&logo=docker)
![Ubuntu Supported](https://img.shields.io/badge/Ubuntu-supported-green?style=square&logo=ubuntu)
![Windows via Docker](https://img.shields.io/badge/Windows-via%20Docker-yellow?style=square&logo=window)
![Python](https://img.shields.io/badge/python-≥_3.9-blue)

# LLM-based Test Generation

This project aims to generate test case using LLM without human's manual efforts. It provides source code and automatically generated prompts, then return two type of test cases: (1) negative test code with type errors, (2) positive test code without any error.

It consists of 2 modules. (1) Potential type error identifier, (2) Test generator.


## Local Installation

```sh
git clone https://github.com/Khamax4mr/llm-test-generation.git
cd llm-test-generation
pip install -r requirements.txt
```

## Docker Installation (Window supported)

```sh
git clone https://github.com/Khamax4mr/llm-test-generation.git
cd llm-test-generation
docker build -t llm-test-generation .
docker run -it --env OPENAI_API_KEY=[your open api key] llm-test-generation
```

## Run (Overall)

```sh
python3 run.py -s [path, path, ..] ..
```

#### Required
* **-s [path1, path2, ..]** - source code path list. **First path** is the target to generate test case. Other paths are used as references for test generation.
* **-c [path]** - config path for model, framework, and their configs

#### Optional
* **-r [res1, res2, ..]** - user defined additional data `<title>:<data>`.
* **-f [fct1, fct2, ..]** - function or class method name list. Target functions to generate test case. If there are no input, it returns all test case.
* **-n [number]** - number of Negative test cases.
* **-p [number]** - number of Positive test cases.
* **-i [number]** - number of rewrite during the test generation.
* **-m [name]** - name of LLM model. ('response')
* **-fw [name]** - name of test framework. ('pytest')
* **-ec [path]** - potential error line identifier config path.
* **-nc [path]** - negative test generator config path.
* **-pc [path]** - positive test generator config path.
* **-fc [path]** - test framework config path.
* **-o [경로]** - output path.

## Run (potential type error identifier)

```sh
python3 -m tools.error_line_identifier.run -s [path] ..
```

#### Required
* **-s [path]** - source code path.

#### Optional
* **-f [fct1, fct2, ..]** - function or class method name list. Target functions to identify type error. If there are no input, it returns all identified lines.
* **-i [number]** - number of re-identifying.
* **-m [name]** - name of LLM model. ('response')
* **-c [path]** - potential error line identifier config path.
* **-o [경로]** - output path.


## Run (test generator)

```sh
python3 -m tools.test_generator.run -s [path1, path2, ..] ..
```

#### Required
* **-s [path1, path2, ..]** - source code path list. **First path** is the target to generate test case. Other paths are used as references for test generation.
* **-e [path]** - identified potential type error line path.

#### Optional
* **-r [res1, res2, ..]** - user defined additional data `<title>:<data>`.
* **-i [number]** - number of rewrite during the test generation.
* **-g [number]** - number of genrated test per request.
* **-n [number]** - number of Negative test cases.
* **-p [number]** - number of Positive test cases.
* **-m [name]** - name of LLM model. ('response')
* **-fw [name]** - name of test framework. ('pytest')
* **-ec [path]** - potential error line identifier config path.
* **-nc [path]** - negative test generator config path.
* **-pc [path]** - positive test generator config path.
* **-fc [path]** - test framework config path.
* **-o [경로]** - output path.