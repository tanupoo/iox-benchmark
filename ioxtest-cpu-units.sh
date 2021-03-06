#!/bin/sh

docker_image=${DOCKER_IMAGE:=ir1101-benchmark}
profile=${PROFILE:=ir1101@tlab}
exec_time=${EXEC_TIME}
nb_tests=${NB_TESTS:=20}
nb_threads=${NB_THREADS:=1}
target=${TARGET:=sysbench}
memory_size=${MEMORY_SIZE:=64}

app_base_dir="./app"

# XXX too bad way....
app_list_storage=".app_list"

Usage()
{
    echo "Usage: ioxtest-cpu-units.sh (start|getlog|clean) unit ..."
    echo "    e.g."
    echo "    ioxtest-cpu-units.sh start 256 256"
    echo "    ioxtest-cpu-units.sh getlog"
    echo "    ioxtest-cpu-units.sh clean"
    echo "    EXEC_TIME=134000 ioxtest-cpu-units.sh start 16 32"
    echo "    PROFILE=ir1101 ioxtest-cpu-units.sh start 16 32"
    exit 0
}

get_app_list()
{
    echo "##"
    echo "## app list"
    ioxclient --profile ${profile} app li
}

start()
{
    app_list=""

    echo "=== packaging ==="
    num=0
    for unit in $*
    do
        num=$((num+1))
        app_name=$(date +app%Y%m%dT%H%M%Sx${num})
        app_list="${app_list}${app_name} "
        echo "##"
        echo "## packaging $app_name"
        DOCKER_IMAGE=${docker_image} PROFILE=${profile} APP_NAME=${app_name} \
            CPU_UNITS=${unit} MEMORY_SIZE=${memory_size} \
            TARGET=${target} NB_TESTS=${nb_tests} NB_THREADS=${nb_threads} \
            EXEC_TIME=${exec_time} LOG_FILE=${app_name}.log \
            APP_BASE_DIR=${app_base_dir} \
            ./ioxmkpkg.sh
    done

    echo "=== start test ==="
    for app_name in ${app_list}
    do
        echo "##"
        echo "## start ${app_name}"
        ioxclient --profile ${profile} app sta ${app_name}
    done

    echo "##"
    echo "## NOTE: ${app_list_storage} is created and app_names are stored in it."
    echo ${app_list} > ${app_list_storage}

    get_app_list
    date
    echo "EXEC_TIME: ${exec_time}"
}

getlog()
{
    for app_name in $(cat ${app_list_storage})
    do
        echo "##"
        echo "## gettig log ${app_name}"
        ioxclient --profile ${profile} app logs download \
            ${app_name} ${app_name}.log
    done
}

clean()
{
    for app_name in $(cat ${app_list_storage})
    do
        echo "##"
        echo "## cleanup ${app_name}"
        ioxclient --profile ${profile} app stop ${app_name}
        ioxclient --profile ${profile} app deact ${app_name}
        ioxclient --profile ${profile} app unin ${app_name}
        rm -rf ${app_base_dir}/${app_name}
    done

    get_app_list
}

#
# main
#
mode=$1
case "$mode" in
    start)
        shift
        units="$*"
        if [ -z "$units" ] ; then
            Usage
        fi
        start $(./expand_units.py $units)
        ;;
    clean) clean ;;
    getlog) getlog ;;
    *) Usage ;;
esac

