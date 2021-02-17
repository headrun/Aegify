#!/bin/sh

. $(dirname "$0")/base.sh

clean_release_dirs(){
    release_path=$1
    days=$2
    remove_type=$3
    if [ -z $release_path ]
    then
        echo "Invalid directory $release_path"
        exit 1
    fi

    if [ -z $days ]
    then
        days=60 #default days to remove the files/dirs
    fi

    if [ -z $remove_type ]
    then
        find $release_path -type f -mtime +$days -exec rm -rf {} \;
    else
        # type for deleting specific format dirs/files. ex rm -rf *.log
        find $release_path -name "*.$remove_type" -type f -mtime +$days -exec rm -rf {} \;
    fi
}

main() {
    release_tgz=$1
    base_validate

    if [ -z $release_tgz ] & [ $1 = "clean_dirs" ]
    then
        clean_release_dirs $2 $3 $4
        exit 1
    fi

    if [ -z $release_tgz ] || [ ! -f $release_tgz ]
    then
        echo "Invalid file $release_tgz"
        exit 1
    fi
    tar -xzf $release_tgz
    tgz=${release_tgz##*\/}
    release_dir=${tgz%.*}

    sh $release_dir/deploy/upgrade.sh
}

main $1 $2 $3 $4
