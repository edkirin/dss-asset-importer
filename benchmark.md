# CSV Loader benchmark

## Data set

- header
- 100.000 rows
- 25 fields
  - int x 6
  - float x 5
  - str x 9
  - bool x 5
- all valid fields, no errors
- file size: 26M

## Benchmark results

| env | run 1 | run 2 | run 3 | run 4 | run 5 | average |
| -- | -- | -- | -- | -- | -- | -- |
| Python 3.7.16 + Pydantic 1.8.2 | 5.027 | 5.072 | 5.015 | 4.992 | 5.032 | 5.028 |
| Python 3.7.16 + Pydantic 1.10.4 | 5.042 | 5.117 | 5.174 | 5.107 | 5.131 | 5.114 |
| Python 3.10.9 + Pydantic 1.10.4 | 4.504 | 4.501 | 4.481 | 4.435 | 4.520 | 4.489 |
| Python 3.11.1 + Pydantic 1.10.4 | 6.264 | 6.334 | 6.279 | 6.228 | 6.345 | 6.290 |
