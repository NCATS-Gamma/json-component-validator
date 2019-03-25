# json-component-validator

## Docker

```
docker run
    --publish <PORT>:7071
    covar/json-component-validator
    <URL>
```

## Installation

It is recommended that you use a virtual environment. For example, using _conda_:

1. `conda create --name json_validator`
2. `source activate json_validator`
3. `pip install -r requirements.txt`

## Usage

`python server.py --port <PORT> <LOCAL FILE PATH>`

OR

`python server.py --port <PORT> <URL>`