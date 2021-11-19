#!/bin/sh

profile=${PROFILE:=ir1101@home}
exec_time=${EXEC_TIME}

app_base_dir="./app"

# XXX too bad way....
app_list_storage=".app_list"

Usage()
{
    echo "Usage: test-cpu-units.sh (start|getlog|clean) unit ..."
    echo "    e.g."
    echo "    test-cpu-units.sh start 256 256"
    echo "    test-cpu-units.sh getlog"
    echo "    test-cpu-units.sh clean"
    echo "    EXEC_TIME=134000 test-cpu-units.sh start 16 32"
    echo "    PROFILE=ir1101 test-cpu-units.sh start 16 32"
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
        PROFILE=${profile} APP_NAME=${app_name} CPU_UNITS=${unit} \
            EXEC_TIME=${exec_time} LOG_FILE=${app_name}.log \
            APP_BASE_DIR=${app_base_dir} \
            ./mkpkg.sh
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
        rm -rf ${app_dir}/${app_name}
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

