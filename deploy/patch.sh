#!/bin/bash

remove_tag(){
    tag_version=$1
    remove_type=$2

    if [ -z $tag_version ]
    then
        echo "Unable to remove the tag, please provide the valid tag_version"
        exit 1
    fi

    # remove the local-tag
    git tag -d $tag_version

    # remove the remote tag
    if [ -z $remove_type ]
    then
        exit 1
    else
        git push origin :refs/tags/$tag_version
    fi

}

create_and_push_branch_from_tag() {
    tag_version=$1
    branch_name=$2
    if [ -z $tag_version ] || [ -z $branch_name ]
    then
        echo "Invalid args are passed"
        exit 1
    fi
    # fetching the branch_name
    current_branch=`git branch -v | grep '^*' | cut -f2 -d' '`
    if [ $current_branch != "master" ]
    then
        git checkout origin master
    fi

    git fetch origin
    git checkout -b $branch_name $tag_version
    echo "patch branch is created, $branch_name"
    git push origin $branch_name

}

main(){
    setup_type=$1
    if [ -z $setup_type ]
    then
        echo "Invalid args are passed"
        exit 1
    fi

    if [ $setup_type = "create_branch" ]
    then
        echo $setup_type
        create_and_push_branch_from_tag $2 $3

    elif [ $setup_type = "remove_tag" ]
    then
        remove_tag $2 $3
    fi

}

main $1 $2 $3
