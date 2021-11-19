#!/bin/sh

# Usage: mkpkg.sh
#        PROFILLE=ir809 mkpkg.sh
#        PROFILLE=cat9135 EXEC_TIME=133000 mkpkg.sh
# PROFILE     ir1101@home
# APP_NAME    app${CPU_UNITS}
# CPU_UNITS   32
# NB_TESTS    20
# NB_THREADS  1
# MEMORY_SIZE 64
# TARGET      sysbench
# EXEC_TIME   None, HHMMSS
# LOG_FILE    ${APP_NAME}.log

image_name=ir1101-sysbench-cpu
profile=${PROFILE:=ir1101@home}
app_name=${APP_NAME:=app${cpu_units}}
cpu_units=${CPU_UNITS:=32}
nb_tests=${NB_TESTS:=20}
nb_threads=${NB_THREADS:=1}
memory_size=${MEMORY_SIZE:=64}
target=${TARGET:=sysbench}
exec_time=${EXEC_TIME}
log_file=${LOG_FILE:=${app_name}.log}
app_base_dir=${APP_BASE_DIR:=app}

runtime_options="-e PROFILE=${profile} -e APP_NAME=${app_name} \
    -e CPU_UNITS=${cpu_units} -e NB_TESTS=${nb_tests} \
    -e NB_THREADS=${nb_threads} -e MEMORY_SIZE=${memory_size} \
    -e TARGET=${target} -e EXEC_TIME=${exec_time} -e LOG_FILE=${log_file}"

if [ ! -d "${app_base_dir}" ] ; then
    mkdir ${app_base_dir}
fi

if [ -z "$app_name" -o -z "$cpu_units" ] ; then
    echo Must specify app_name and cup_units
    exit 128
fi

app_dir="${app_base_dir}/${app_name}"
if [ -d ${app_dir} ] ; then
    echo "Must delete the directory, ${app_dir}"
    exit 128
fi
mkdir ${app_dir}

cat <<EOD > ${app_dir}/package.yaml
descriptor-schema-version: "2.12"
info:
  name: ir1101-sysbench-cpu
  description: buildkit.dockerfile.v0
  version: latest
app:
  cpuarch: aarch64
  env:
    PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  resources:
    cpu: ${cpu_units}
    memory: ${memory_size}
    disk: 2
    network:
    - interface-name: eth0
      ports: {}
    profile: custom
  startup:
    rootfs: rootfs.tar
    target:
    - /bin/sh
    - -c
    - /bin/test.sh
    runtime_options: "${runtime_options}"
  type: docker
EOD

# Packaging
ioxclient --profile ${profile} docker pkg ${image_name} ${app_dir}/

# Install
ioxclient --profile ${profile} app in ${app_name} ${app_dir}/package.tar

# Activate
ioxclient --profile ${profile} app act ${app_name} \
    --payload activate.json \
    --docker-opts "${runtime_options}"
