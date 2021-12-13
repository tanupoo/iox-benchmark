Cisco IOx: test tools
=====================

## テスト用IOxアプリのビルド

```
docker build -t ir1101-benchmark docker/
```

## ioxtest-cpu-units.sh

テストスクリプト。

```
Usage: ioxtest-cpu-units.sh (start|getlog|clean) unit ...
```

unit に CPUユニット値を指定する。
コンテナを複数動かす場合は列挙する。
同じ値の場合は `x` が使える。例えば、256を4つ動かす場合は、`256x4`

その他のパラメータは環境変数で渡す。

環境変数は以下の通り。カッコ内はデフォルト値。

DOCKER_IMAGE: テストのためのDockerイメージを指定する。(ir1101-benchmark)
PROFILE: ioxclientで使うプロファイル名。(ir1101@tlab)
EXEC_TIME: テストの起動時間。指定しなければ即時実行する。
NB_TESTS: テスト回数。(20)
NB_THREADS: スレッド数。(1)
TARGET: テスト名 (sysbench)
MEMORY_SIZE: IOxアプリに割り当てるメモリサイズ。(64)

TARGETは下記のいずれか。

- sysbench:
- linpack:
- openssl:
- sleep: sleepするだけ。コンテナのデバッグに使う。

## IR1101 の場合

CPUユニット値1024のコンテナを4つで、sysbenchを動かす。
sysbenchを9時40分に起動させる。
テスト回数は1000回。

```
EXEC_TIME=094000 NB_TESTS=1000 ./ioxtest-cpu-units.sh start 1024x4
```

CPUユニット値128,256,512、メモリ512MBのコンテナを3つで、opensslを動かす。
テスト回数は20回。
スレッドは2つ。

```
TARGET=openssl \
MEMORY_SIZE=512 \
NB_THREADS=2 \
NB_TESTS=20 \
./ioxtest-cpu-units.sh start 512
```

## RPi1/RPi3/RPi4 の場合

benchmark.sh を使う。

```
TARGET=sysbench \
NB_TESTS=20 \
NB_THREADS=1 \
MEMORY_SIZE=64 \
LOG_PATH=. \
LOG_FILE=rpi1-sysbench.log \
./benchmark.sh
```

## mac の場合

benchmark.sh を使う。

gnu-dateが必要なので、coreutilsをインストールして、
DATE_CMDを gdateにする。

```
brew install coreutils
```

```
TARGET=sysbench \
NB_TESTS=20 \
NB_THREADS=1 \
MEMORY_SIZE=64 \
LOG_PATH=. \
LOG_FILE=rpi1-sysbench.log \
./benchmark.sh
```

## Qiitaのグラフデータ

```
./parselog.py log/64/ap* -v | ./tab2gm.py
./parselog.py log/1155x20/ap* -v | ./tab2gm.py
./parselog.py log/1155x20/ap* -v --show-statts
./parselog.py log/N100-*x4/ap* --graph hist-tt --save-data fig3.json
./parselog.py log/N100-*x8/ap* --graph hist-tt --save-data fig4.json
```

## dev

linpackやopensslのビルド用

```
cd docker
docker build -t ir1101-benchmark-dev -f Dockerfile.dev .
docker run -it --name ir1101-benchmark-dev ir1101-benchmark-dev
    :
docker build -t ir1101-benchmark-opt -f Dockerfile.opt .
```

