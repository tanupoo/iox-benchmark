#!/bin/sh

profile=${PROFILE:=ir1101@home}
time_exec=${TIME_EXEC}

Usage()
{
    echo "Usage: test-cpu-units.sh (start|getlog|clean) unit ..."
    echo "    e.g."
    echo "    test-cpu-units.sh start 256 256"
    echo "    test-cpu-units.sh getlog 256 256"
    echo "    test-cpu-units.sh clean 256 256"
    echo "    TIME_EXEC=134000 test-cpu-units.sh start 16 32"
    echo "    PROFILE=ir1101 test-cpu-units.sh start 16 32"
    exit 0
}

start()
{
    app_list=""

    echo "=== packaging ==="
    num=0
    for unit in $units
    do
        num=$((num+1))
        app_name=$(date +app%Y%m%dT%H%M%Sx${num})
        app_list="${app_list}${app_name} "
        echo "## packaging $app_name"
        PROFILE=${profile} APP_NAME=${app_name} CPU_UNITS=${unit} TIME_EXEC=${time_exec} ./mkpkg.sh
    done

    echo "=== start test ==="
    for app_name in ${app_list}
    do
        echo "## start ${app_name}"
        ioxclient --profile ${profile} app sta ${app_name}
    done

    date
}

getlog()
{
    for unit in $units
    do
        app_name="app${unit}"
        ioxclient --profile ${profile} app logs download \
            ${app_name} ${app_name}.log
    done
}

clean()
{
    for unit in $units
    do
        app_name="app${unit}"
        echo "## cleanup ${app_name}"
        ioxclient --profile ${profile} app deact ${app_name}
        ioxclient --profile ${profile} app unin ${app_name}
        rm -rf ${app_name}
    done
}

#
# main
#
mode=$1
shift
units="$*"
if [ -z "$units" ] ; then
    Usage
fi
case "$mode" in
    start) start $units ;;
    clean) clean $units ;;
    getlog) getlog $units ;;
    *) Usage ;;
esac

